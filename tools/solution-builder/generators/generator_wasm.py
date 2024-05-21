
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

class WasmContext(generator_utils.GeneratorInterface):
	def __init__(self, workspace):
		self.template_folder = os.path.join(_this_dir, "templates", "wasm")

		self.workspace = workspace
		self.wasm_workspace = generator_utils.read_text_file(os.path.join(self.template_folder,"wasm_workspace_template.txt"))
		self.wasm_project_template = generator_utils.read_text_file(os.path.join(self.template_folder,"wasm_project_template.txt"))

		self.files_to_copy = []

		self._add_template("wasm-emscripten.dockerfile", ".", "emscripten", False)
		self._add_template("wasm-emscripten-build.sh", ".", "emscripten", True)
		
		
		self._add_template("wasm-webserver.dockerfile", ".", "webhost", False)
		self._add_template("requirements.txt", ".", "webhost", False)
		self._add_template("wasm-webhost.py", ".", "webhost", False)
		self._add_template("wasm-index.html", ".", "webhost", True)

		
		self._add_template("wasm-host-config.bat", ".", ".", True)
		self._add_template("wasm-build-with-config.bat", ".", ".", True)

	def __str__(self):
		return "cmake"

	def _add_template(self, filename, input_folder, target_folder, preprocess):
		self.files_to_copy.append((filename, input_folder, target_folder, preprocess))

	def _preprocessFile(self, solution, input_file, output_file):
		f = open(input_file,"r")
		content = f.read()
		f.close()
		replmap = {
			"__WORKSPACE_RELPATH__" : os.path.join(os.path.relpath(self.workspace, solution.output)),
			"__WORKSPACE_PATH__" : os.path.relpath(solution.output, self.workspace),
		}
		for word, value in replmap.items():
			content = content.replace(word, value)
		f = open(output_file,"w")
		f.write(content)
		f.close()

	def _generate_header(self, solution_name):
		sname = "_" + solution_name.replace("-","_")
		return self.wasm_workspace.replace("__SOLUTION_NAME__",sname) + "\n"

	def _generate_project_str(self, replmap):
		proj_data = self.wasm_project_template
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
			"__PROJECT_TYPE__" : itype,
			"__ISEXECUTABLE__" : "YES" if itype == "exe" else "NO",
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

		for i in self.files_to_copy:
			(filename, input_folder, target_folder, preprocess) = i
			input_file = os.path.join(self.template_folder, input_folder, filename)
			target_folder = os.path.join(solution.output, target_folder)
			if not os.path.exists(target_folder):
				os.makedirs(target_folder)

			target_file = os.path.join(target_folder, filename)
			if preprocess == False:
				shutil.copyfile(input_file, target_file)
			else:
				self._preprocessFile(solution, input_file, target_file)



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
	return WasmContext(workspace)



