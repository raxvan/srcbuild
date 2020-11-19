
import os
import shutil
import fnmatch
import filecmp
import sys
import glob
import re
import subprocess
import json
import ciutil

_this_dir = os.path.dirname(os.path.abspath(__file__))

premake_workspace = ciutil.read_text_file(os.path.join(_this_dir,"templates","premake_workspace_template.txt")) 

premake_platform_map_arg = {
	"win32" : "windows",
	"linux" : "linux",
}
premake_builder_map_arg = {
	"msvc" : "vs2019", #latest
	"vs2019" : "vs2019",
	"vs2017" : "vs2017",
	"vs2015" : "vs2015",
	"make" : "gmake",
}

premake_project_kind = {
	"exe" : "ConsoleApp",
	"lib" : "StaticLib",
	#"pure-dll" : "SharedLib",
	"dll" : "SharedLib",
	"view" : "StaticLib",
}

cpp_standards_map = {
	"11" : "C++11",
	"14" : "C++14",
	"17" : "C++17"
}

premake_project_template = ciutil.read_text_file(os.path.join(_this_dir,"templates","premake_project_template.txt")) 


def get_custom_build_flags(item):
	opts = []
	if item["platform"] == "linux" and item["builder"] == "make":
		opts.append("-lrt") #no idea for what
		opts.append("-pthread") #for threading
	elif item["platform"] == "win32" and item["builder"] in ["msvc","vs2019","vs2017","vs2015"]:
		opts.append("/MP") #enable multiprocessos compilation

	return ",".join(['"' + o + '"' for o in opts])

def get_custom_link_flags(item):
	opts = []
	if item["platform"] == "linux" and item["builder"] == "make":
		opts.append("-lpthread") #for threading


	return ",".join(['"' + o + '"' for o in opts])

def append_project_to_file(file_handle, ctx, target_build_folder, project_stack, item):

	all_includes = ctx.collapse_includes( project_stack, item)
	all_sources = ctx.collapse_sources( project_stack, item)
	all_defines = ctx.collapse_defines( project_stack, item)
	(all_local_libs,all_external_libs) = ctx.collapse_libs( project_stack, item)

	all_libs = list(set(all_local_libs + all_external_libs))
	all_libs.sort()

	fixed_name = item['name']
	if item['kind'] == "exe":
		fixed_name = "_" + fixed_name

	warnings_flag = "Off"
	if item['options']['warnings'] == True:
		warnings_flag = "Extra"

	replacemap = {
		"__NAME__" : fixed_name,
		"__INCL__" : ",".join(['"' + ctx.final_path(target_build_folder,d) + '"' for d in all_includes]),
		"__SRC__" : ",".join(['"' + ctx.final_path(target_build_folder,d) + '"' for d in all_sources]),
		"__DEF__" : ",".join(['"' + d + '"' for d in all_defines]),
		"__LINKS__" : ",".join(['"' + d + '"' for d in all_libs]),
		"__KIND__" : premake_project_kind[item["kind"]],
		"__PLATFORM__" : item["platform"],
		"__BUILDER__" : item["builder"],
		"__STANDARD__" : cpp_standards_map[item["cpp-standard"]],
		"__CUSTOM_BUILD_FLAGS__" : get_custom_build_flags(item),
		"__CUSTOM_LINK_FLAGS__" : get_custom_link_flags(item),
		"__WARNINGS__": '"' + warnings_flag + '"',
	}

	#generator.premake.lua
	file_handle.write(generate_project_str(replacemap))

def generate_project_str(replmap):
	proj_data = premake_project_template
	for word, value in replmap.items():
		proj_data = proj_data.replace(word, value)
	return "\n" + proj_data + "\n"

def generate_header(context):
	sname = "_" + context.name.replace("-","_")
	return premake_workspace.replace("__SOLUTION_NAME__",sname)

def run(context, target_build_folder, project_stack):

	premake_path = os.path.join(target_build_folder,"generator.premake.lua")
	f = open(premake_path,"w")

	header = generate_header(context)
	f.write(header)

	for k,v in project_stack.items():
		append_project_to_file(f, context, target_build_folder, project_stack, v)

	f.close()

	premake_os = premake_platform_map_arg[context.platform]
	premake_builder = premake_builder_map_arg[context.builder]

	output = subprocess.run([context.envget("premake5"),"--verbose","--os=" + premake_os,"--file=" + premake_path,premake_builder])
	return output
