
import os
import sys
import shutil

import generator_cpp_utils
import generator_utils

_this_dir = os.path.dirname(os.path.abspath(__file__))

##################################################################################################################################

def _get_cpp_standard(item):
	cpp_standards_map = {
		"11" : "11",
		"14" : "14",
		"17" : "17",
		"20" : "20",
	}
	return cpp_standards_map[item.content.get_property_or_die("cppstd").value]

def _get_project_name(item):
	fixed_name = item.get_name()
	n = item.content.get_rawtype()
	if n == "exe":
		return "_" + fixed_name
	return fixed_name

def _update_warnings(replacemap, item):
	warnings_map = {
		"off" : "NO",
		"default" : "YES",
		"full" : "YES",
	}
	w = item.content.get_property_or_die("warnings").value
	if w == "off":
		replacemap["__FULL_WARNINGS__"] = "NO"
		replacemap["__DISABLE_WARNINGS__"] = "YES"
	elif w == "default":
		replacemap["__FULL_WARNINGS__"] = "NO"
		replacemap["__DISABLE_WARNINGS__"] = "NO"
	elif w == "full":
		replacemap["__FULL_WARNINGS__"] = "YES"
		replacemap["__DISABLE_WARNINGS__"] = "NO"


cmake_add_type = {
	"exe" : "add_executable",
	"lib" : "add_library",

	"dll" : "add_library",
	"view" : "message",
}
cmake_add_type_data = {
	"exe" : "",
	"lib" : "STATIC",

	"dll" : "SHARED",
	"view" : "STATIC",
}

##################################################################################################################################

class CmakeContext(generator_utils.GeneratorInterface):
	def __init__(self):
		template_folder = os.path.join(_this_dir, "templates", "cmake")

		self.cmake_workspace = generator_utils.read_text_file(os.path.join(template_folder,"cmake_workspace_template.txt"))
		self.cmake_project_template = generator_utils.read_text_file(os.path.join(template_folder,"cmake_project_template.txt"))
		fc = [
			"cmake-build-with-config.sh",
			"cmake-build-with-config.bat",
			"cmake-generate-vs2022.bat",
			"cmake-generate-xcode.sh",
			"cmake-create-vscode-workspace.py",
		]
		self.files_to_copy = {x : os.path.join(template_folder, x) for x in fc }

		srcbuild_files = [
			"cmake_successfull_build.py"
		]
		self.srcbuild_files_to_copy = {x : os.path.join(template_folder, x) for x in srcbuild_files }

	def __str__(self):
		return "cmake"

	def _generate_header(self, solution_name):
		sname = "_" + solution_name.replace("-","_")
		return self.cmake_workspace.replace("__SOLUTION_NAME__",sname) + "\n"

	def _generate_project_str(self, replmap):
		proj_data = self.cmake_project_template
		for word, value in replmap.items():
			proj_data = proj_data.replace(word, value)
		return proj_data + "\n"

	def _generate_project_file(self, solution, item):

		all_includes = generator_cpp_utils.query_include_paths(solution, item)
		all_sources = generator_cpp_utils.query_sources(solution, item)
		all_defines = generator_cpp_utils.query_defines(solution, item)
		all_links = generator_cpp_utils.query_libs(solution, item)
		extra_links = generator_cpp_utils.query_extra_libs(solution, item) #TODO

		mrp = generator_cpp_utils.make_relative_path

		target_build_folder = solution.output

		itype = item.content.get_rawtype()
		name =  _get_project_name(item)
		replacemap = {
			"__NAME__" : name,
			#"__PROJECT_FILE_ABS_PATH__" : item.get_package_absolute_path(),
			"__INCL__" : "\n\t".join(["${CMAKE_CURRENT_SOURCE_DIR}/../../" + mrp(d, target_build_folder) for d in all_includes]),
			"__SRC__" : "\n\t".join(["${CMAKE_CURRENT_SOURCE_DIR}/../../" + mrp(d, target_build_folder) for d in all_sources]),
			"__DEF__" : "\n\t".join(all_defines),
			"__LINKS__" : "\n\t".join([d.get_name() for d in all_links if generator_cpp_utils.is_cpp_compilable(d)]),
			"__ADD_TYPE__" : cmake_add_type[itype],
			"__ADD_TYPE_DATA__" : cmake_add_type_data[itype],
			"__STANDARD__" : _get_cpp_standard(item),
			"__THREADS__" : "YES",
			"__PROJECT_TYPE__" : itype
		}

		_update_warnings(replacemap, item);

		cmakelists_dir = os.path.join(target_build_folder,"projects", name)
		if not os.path.exists(cmakelists_dir):
			os.makedirs(cmakelists_dir)

		cmakelists_file = os.path.join(cmakelists_dir, "CMakeLists.txt")
		print(cmakelists_file)
		f = open(cmakelists_file,"w")
		f.write(self._generate_project_str(replacemap))
		f.close()

	def configure(self, cfg):
		cfg.option("cppstd","20",["11","14","17","20"])
		cfg.option("warnings","full",["off","default", "full"])

	def prebuild(self, solution):

		for k,v in self.files_to_copy.items():
			output_path = os.path.join(solution.output, k)
			shutil.copyfile(v,output_path)

		for k,v in self.srcbuild_files_to_copy.items():
			output_path = os.path.join(solution.output, ".srcbuild", k)
			shutil.copyfile(v,output_path)

		

	def accept(self, solution, module):
		if generator_cpp_utils.is_cpp_compilable(module):
			module.content.setoption("cppstd")
			module.content.setoption("warnings")
			return True

		return False

	def postbuild(self, solution):
		
		cmakelists_path = os.path.join(solution.output,"CMakeLists.txt")
		tout = open(cmakelists_path,"w")

		#solution entry
		header = self._generate_header(solution.name)
		tout.write(header)

		#projects:
		for m in solution.get_modules():
			if (m.enabled == False):
				continue
			
			if generator_cpp_utils.is_cpp_compilable(m) == False:
				continue

			self._generate_project_file(solution, m)
			tout.write("add_subdirectory(projects/" + _get_project_name(m) + ")\n")

		tout.close()

		print(f"Generated solution: {cmakelists_path}")



def create(workspace, priority):
	return CmakeContext()



