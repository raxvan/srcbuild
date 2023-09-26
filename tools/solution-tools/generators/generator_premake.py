
import os
import sys
import subprocess

import shell_utils
import generator_query

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

def _get_cpp_standard(item):
	cpp_standards_map = {
		"11" : "C++11",
		"14" : "C++14",
		"17" : "C++17",
		"20" : "C++20",
	}
	return cpp_standards_map[item.content.get_property_or_die("cppstd").value]

def _get_project_kind(item):
	premake_project_kind = {
		"exe" : "ConsoleApp",
		"lib" : "StaticLib",
		"dll" : "SharedLib",
		"view" : "NONE",
	}
	return premake_project_kind[item.content.get_property_or_die("type").value]

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

class PremakeContext():
	def __init__(self, template_folder, solution, config):

		self.premake_workspace = shell_utils.read_text_file(os.path.join(template_folder,"premake_workspace_template.txt"))
		self.premake_project_template = shell_utils.read_text_file(os.path.join(template_folder,"premake_project_template.txt"))

		self.solution = solution
		self.config = config

	def generate_header(self, solution_name):
		sname = "_" + solution_name #.replace("-","_")
		return self.premake_workspace.replace("__SOLUTION_NAME__",sname) + "\n"

	def generate_project_str(self, replmap):
		proj_data = self.premake_project_template
		for word, value in replmap.items():
			proj_data = proj_data.replace(word, value)
		return proj_data + "\n"

	def append_project_to_file(self, target_build_folder, item):

		all_includes = generator_query.query_include_paths(self.solution, item)
		all_sources = generator_query.query_sources(self.solution, item)
		all_defines = generator_query.query_defines(self.solution, item)
		all_links = generator_query.query_libs(self.solution, item)
		extra_links = generator_query.query_extra_libs(self.solution, item)

		mrp = generator_query.make_relative_path

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
		return self.generate_project_str(replacemap)

	def run(self, solution_name, output_dir):

		generator_file = ""

		#solution entry
		header = self.generate_header(solution_name)
		generator_file = generator_file + header

		#projects:
		for m in self.solution.get_modules():
			content = self.append_project_to_file(output_dir, m)
			generator_file = generator_file + content

		premake_path = os.path.join(output_dir,"generator.premake.lua")
		#tout = open(premake_path,"e")

		if(shell_utils.save_if_changed(premake_path, generator_file) == False):
			#no changes
			print("No changes...")
			return


		#actually generate the solution
		premake_os = _get_premake_os_arg()
		premake_builder = _get_premake_builder_arg(self.config)

		output = subprocess.run([os.getenv("PREMAKE5_EXE",None),"--verbose","--os=" + premake_os,"--file=" + premake_path, premake_builder])
		return output