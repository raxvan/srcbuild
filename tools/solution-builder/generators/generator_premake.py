
import os
import sys
import shutil

import generator_cpp_utils
import generator_utils
import subprocess

_this_dir = os.path.dirname(os.path.abspath(__file__))

##################################################################################################################################
def _get_custom_build_flags(item):
	opts = []
	
	#_platform = item.content.get_property_or_die("platform").value
	#_platform = "win32"
	#_builder = item.content.get_property_or_die("builder").value
	#if _platform == "linux" and _builder == "make":
	#	opts.append("-lrt") #no idea for what
	#	opts.append("-pthread") #for threading
	#elif _platform == "win32":
	
	opts.append("/MP") #enable multiprocessos compilation

	return ",".join(['"' + o + '"' for o in opts])

def _get_custom_link_flags(item):
	opts = []

	#_platform = item.content.get_property_or_die("platform").value
	#_platform = "win32"
	#_builder = item.content.get_property_or_die("builder").value
	#if _platform == "linux" and _builder == "make":
	#	opts.append("-lpthread") #for threading

	return ",".join(['"' + o + '"' for o in opts])

def _get_project_kind(item):
	premake_project_kind = {
		"exe" : "ConsoleApp",
		"lib" : "StaticLib",
		"dll" : "SharedLib",
		"view" : "NONE",
	}
	return premake_project_kind[item.content.get_rawtype()]

def _get_cpp_standard(item):
	cpp_standards_map = {
		"11" : "C++11",
		"14" : "C++14",
		"17" : "C++17",
		"20" : "C++20",
	}
	return cpp_standards_map[item.content.get_property_or_die("cppstd").value]

def _get_warnings(item):
	warnings_map = {
		"off" : "Off",
		"default" : "On",
		"full" : "Extra",
	}
	return warnings_map[item.content.get_property_or_die("warnings").value]

def _get_project_name(item):
	fixed_name = item.get_name()
	n = item.content.get_property("exe-name");
	if n == None:
		return fixed_name

	return n.value

def _get_premake_os_arg():
	#platform
	#"windows"
	#"linux"
	return "windows"

def _get_premake_builder_arg(config):
	#"vs2019"
	#"vs2017"
	#"vs2015"
	return config.query_option_value("default-visual-studio")
##################################################################################################################################

class PremakeContext(generator_utils.GeneratorInterface):
	def __init__(self):
		template_folder = os.path.join(_this_dir, "templates", "premake")

		self.premake_workspace = generator_utils.read_text_file(os.path.join(template_folder,"premake_workspace_template.txt"))
		self.premake_project_template = generator_utils.read_text_file(os.path.join(template_folder,"premake_project_template.txt"))


	def __str__(self):
		return "premake"

	def _generate_header(self, solution_name):
		sname = "_" + solution_name #.replace("-","_")
		return self.premake_workspace.replace("__SOLUTION_NAME__",sname) + "\n"

	def _generate_project_str(self, replmap):
		proj_data = self.premake_project_template
		for word, value in replmap.items():
			proj_data = proj_data.replace(word, value)
		return proj_data + "\n"

	def _append_project_to_file(self, solution, target_build_folder, item):

		all_includes = generator_cpp_utils.query_include_paths(solution, item)
		all_sources = generator_cpp_utils.query_sources(solution, item)
		all_defines = generator_cpp_utils.query_defines(solution, item)
		all_links = generator_cpp_utils.query_libs(solution, item)
		extra_links = generator_cpp_utils.query_extra_libs(solution, item)

		mrp = generator_cpp_utils.make_relative_path

		replacemap = {
			"__NAME__" : _get_project_name(item),
			"__INCL__" : ",".join(sorted(['"' + mrp(d, target_build_folder) + '"' for d in all_includes])),
			"__SRC__" : ",".join(sorted(['"' + mrp(d, target_build_folder) + '"' for d in all_sources])),
			"__DEF__" : ",".join(sorted(['"' + d + '"' for d,_ in all_defines.items()])),
			"__LINKS__" : ",".join(
				sorted(
					['"' + d.get_name() + '"' for d in all_links] +
					['"' + mrp(d, target_build_folder) + '"' for d in extra_links]
				)
			),
			"__KIND__" : _get_project_kind(item),
			"__STANDARD__" : _get_cpp_standard(item),
			"__CUSTOM_BUILD_FLAGS__" : _get_custom_build_flags(item),
			"__CUSTOM_LINK_FLAGS__" : _get_custom_link_flags(item),
			"__WARNINGS__": _get_warnings(item),
		}

		#generator.premake.lua
		return self._generate_project_str(replacemap)

	def configure(self, cfg):
		cfg.option("cppstd","20",["11","14","17","20"])
		cfg.option("warnings","full",["off","default", "full"])
		cfg.option("default-visual-studio", "vs2022", [
			"vs2022",
			"vs2019",
			"vs2017",
			"vs2015"
		])


	def prebuild(self, solution):
		pass
		

	def accept(self, solution, module):
		if generator_cpp_utils.is_cpp_compilable(module):
			module.content.setoption("cppstd")
			module.content.setoption("warnings")
			return True

		return False

	def postbuild(self, solution):
		generator_file = ""

		#solution entry
		header = self._generate_header(solution.name)
		output_dir = solution.output
		generator_file = generator_file + header

		#projects:
		for m in solution.get_modules():
			if (m.enabled == False):
				continue

			if generator_cpp_utils.is_cpp_compilable(m) == False:
				continue
				
			content = self._append_project_to_file(solution, output_dir, m)
			generator_file = generator_file + content

		premake_path = os.path.join(output_dir,"generator.premake.lua")

		if(generator_utils.save_if_changed(premake_path, generator_file) == False):
			#no changes
			print("No changes...")
			return

		print(f"Running premake with: {premake_path}")

		#actually generate the solution
		premake_os = _get_premake_os_arg()
		premake_builder = _get_premake_builder_arg(solution.get_config())

		output = subprocess.run([os.getenv("PREMAKE5_EXE",None),"--verbose","--os=" + premake_os,"--file=" + premake_path, premake_builder])
		return output



def create(workspace, priority):
	return PremakeContext()



