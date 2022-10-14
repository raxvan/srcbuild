
import os
import sys
import subprocess

import shell_utils
import generator_query

_this_dir = os.path.dirname(os.path.abspath(__file__))

premake_workspace = shell_utils.read_text_file(os.path.join(_this_dir,"..","templates","premake_workspace_template.txt")) 
premake_project_template = shell_utils.read_text_file(os.path.join(_this_dir,"..","templates","premake_project_template.txt")) 

##################################################################################################################################

def _get_custom_build_flags(item):
	opts = []
	_platform = item.options.get_value_or_die("platform")
	_builder = item.options.get_value_or_die("builder")
	if _platform == "linux" and _builder == "make":
		opts.append("-lrt") #no idea for what
		opts.append("-pthread") #for threading
	elif _platform == "win32" and _builder in ["vs","vs2019", "vs2017","vs2015"]:
		opts.append("/MP") #enable multiprocessos compilation

	return ",".join(['"' + o + '"' for o in opts])

def _get_custom_link_flags(item):
	opts = []
	_platform = item.options.get_value_or_die("platform")
	_builder = item.options.get_value_or_die("builder")
	if _platform == "linux" and _builder == "make":
		opts.append("-lpthread") #for threading

	return ",".join(['"' + o + '"' for o in opts])

def _get_cpp_standard(item):
	cpp_standards_map = {
		"11" : "C++11",
		"14" : "C++14",
		"17" : "C++17",
		"20" : "C++20",
	}
	return cpp_standards_map[item.options.get_value_or_die("cppstd")]

def _get_project_kind(item):
	premake_project_kind = {
		"exe" : "ConsoleApp",
		"lib" : "StaticLib",
		"dll" : "SharedLib",
		"view" : "NONE",
	}
	return premake_project_kind[item.content.get_property_or_die("type")]

def _get_warnings(item):
	warnings_map = {
		"off" : "Off",
		"default" : "On",
		"full" : "Extra",
	}
	return warnings_map[item.content.get_property_or_die("warnings")]

def _get_project_name(item):
	fixed_name = item.get_name()

	if item.content.get_property_or_die("type") == "exe":
		fixed_name = "_" + fixed_name

	return fixed_name

def _get_premake_os_arg(options):
	#platform
	premake_platform_map_arg = {
		"win32" : "windows",
		"linux" : "linux",
	}
	return premake_platform_map_arg[options.get("platform")]

def _get_premake_builder_arg(options):
	premake_builder_map_arg = {
		"vs" : "vs2019", #latest
		"vs2019" : "vs2019",
		"vs2017" : "vs2017",
		"vs2015" : "vs2015",
		#"make" : "gmake",
	}
	return premake_builder_map_arg[options.get("builder")]



##################################################################################################################################

def append_project_to_file(projects_graph, target_build_folder, item):

	all_includes = generator_query.query_include_paths(projects_graph, item)
	all_sources = generator_query.query_sources(projects_graph, item)
	all_defines = generator_query.query_defines(projects_graph, item)
	all_links = generator_query.query_libs(projects_graph, item)
	extra_links = generator_query.query_extra_libs(projects_graph, item)

	mrp = generator_query.make_relative_path

	replacemap = {
		"__NAME__" : _get_project_name(item),
		"__INCL__" : ",".join(['"' + mrp(d, target_build_folder) + '"' for d in all_includes]),
		"__SRC__" : ",".join(['"' + mrp(d, target_build_folder) + '"' for d in all_sources]),
		"__DEF__" : ",".join(['"' + d + '"' for d,_ in all_defines.items()]),
		"__LINKS__" : ",".join(
			['"' + d + '"' for d in all_links] + 
			['"' + mrp(d, target_build_folder) + '"' for d in extra_links]
		),
		"__KIND__" : _get_project_kind(item),
		"__STANDARD__" : _get_cpp_standard(item),
		"__CUSTOM_BUILD_FLAGS__" : _get_custom_build_flags(item),
		"__CUSTOM_LINK_FLAGS__" : _get_custom_link_flags(item),
		"__WARNINGS__": _get_warnings(item),
	}

	#generator.premake.lua
	return generate_project_str(replacemap)

def generate_project_str(replmap):
	proj_data = premake_project_template
	for word, value in replmap.items():
		proj_data = proj_data.replace(word, value)
	return proj_data + "\n"

def generate_header(solution_name):
	sname = "_" + solution_name.replace("-","_")
	return premake_workspace.replace("__SOLUTION_NAME__",sname) + "\n"

def run(projects_graph, solution_name, options, output_dir):

	premake_path = os.path.join(output_dir,"generator.premake.lua")
	tout = open(premake_path,"w")

	#solution entry
	header = generate_header(solution_name)
	tout.write(header)

	#projects:
	for _,v in projects_graph.items():
		content = append_project_to_file(projects_graph, output_dir, v)
		tout.write(content)

	tout.close()

	#actually generate the solution
	premake_os = _get_premake_os_arg(options)
	premake_builder = _get_premake_builder_arg(options)

	#output = subprocess.run([os.getenv("PREMAKE5_EXE",None),"--verbose","--os=" + premake_os,"--file=" + premake_path, premake_builder])
	#return output
