
import os
import sys
import shutil
import shell_utils
import generator_query

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

	if item.content.get_property_or_die("type").value == "exe":
		fixed_name = "_" + fixed_name

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

class CmakeContext():
	def __init__(self, template_folder, solution, config):

		self.cmake_workspace = shell_utils.read_text_file(os.path.join(template_folder,"cmake_workspace_template.txt"))
		self.cmake_project_template = shell_utils.read_text_file(os.path.join(template_folder,"cmake_project_template.txt"))
		fc = [
			"cmake_build_with_config.sh",
			"cmake_generate_make.sh",
			"cmake_generate_vs2022.bat",
		]
		self.files_to_copy = { x : os.path.join(template_folder, x) for x in fc }


		self.solution = solution
		self.config = config

	def generate_header(self, solution_name):
		sname = "_" + solution_name.replace("-","_")
		return self.cmake_workspace.replace("__SOLUTION_NAME__",sname) + "\n"

	def generate_project_str(self, replmap):
		proj_data = self.cmake_project_template
		for word, value in replmap.items():
			proj_data = proj_data.replace(word, value)
		return proj_data + "\n"

	def generate_project_file(self, target_build_folder, item):

		all_includes = generator_query.query_include_paths(self.solution, item)
		all_sources = generator_query.query_sources(self.solution, item)
		all_defines = generator_query.query_defines(self.solution, item)
		all_links = generator_query.query_libs(self.solution, item)
		extra_links = generator_query.query_extra_libs(self.solution, item) #TODO

		mrp = generator_query.make_relative_path

		itype = item.content.get_property_or_die("type").value
		name =  _get_project_name(item)
		replacemap = {
			"__NAME__" : name,
			"__INCL__" : "\n\t".join(["${CMAKE_CURRENT_SOURCE_DIR}/../../" + mrp(d, target_build_folder) for d in all_includes]),
			"__SRC__" : "\n\t".join(["${CMAKE_CURRENT_SOURCE_DIR}/../../" + mrp(d, target_build_folder) for d in all_sources]),
			"__DEF__" : "\n\t".join(all_defines),
			"__LINKS__" : "\n\t".join([d.get_name() for d in all_links]),
			"__ADD_TYPE__" : cmake_add_type[itype],
			"__ADD_TYPE_DATA__" : cmake_add_type_data[itype],
			"__STANDARD__" : _get_cpp_standard(item),
			"__THREADS__" : "YES"
		}

		_update_warnings(replacemap, item);

		cmakelists_dir = os.path.join(target_build_folder,"projects", name)
		if not os.path.exists(cmakelists_dir):
			os.makedirs(cmakelists_dir)

		cmakelists_file = os.path.join(cmakelists_dir, "CMakeLists.txt")
		print(cmakelists_file)
		f = open(cmakelists_file,"w")
		f.write(self.generate_project_str(replacemap))
		f.close();

	def run(self, solution_name, output_dir):

		cmakelists_path = os.path.join(output_dir,"CMakeLists.txt")
		tout = open(cmakelists_path,"w")

		#solution entry
		header = self.generate_header(solution_name)
		tout.write(header)

		#projects:
		for m in self.solution.get_modules():
			self.generate_project_file(output_dir, m)
			tout.write("add_subdirectory(projects/" + _get_project_name(m) + ")\n")

		tout.close()

		for k,v in self.files_to_copy.items():
			output_path = os.path.join(output_dir, k)
			shutil.copyfile(v,output_path)

		print(f"Generated solution: {cmakelists_path}")
