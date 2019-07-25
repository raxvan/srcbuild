
import os
import shutil
import fnmatch
import filecmp
import sys
import glob
import re
import subprocess
import json

premake_workspace = """

---------------------------------------------------------------------------------------------
local _global_optimize_flags = "Speed"
---------------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------------

workspace "_this_"
	location(".")
	configurations { "Debug", "Release" }
	platforms { "x32", "x64", "ARM" }
	filter "platforms:x32"
		kind "StaticLib"
		architecture "x32"

	filter "platforms:x64"
		kind "StaticLib"
		architecture "x64"
	filter "platforms:ARM"
		kind "StaticLib"
		architecture "ARM"
"""

premake_project_kind = {
	"exe" : "ConsoleApp",
	"lib" : "StaticLib",
	"view" : "StaticLib",
}
premake_platform_map = {
	"win32" : "windows",
	"linux" : "linux",
}
premake_builder_map = {
	"vs2019" : "vs2019",
	"vs2017" : "vs2017",
	"vs2015" : "vs2015",
	"make" : "gmake",
}

premake_project_template = """
project "__NAME__"
	kind("__KIND__")
	language("C++")
	location(".")
	characterset("MBCS")
	warnings("Extra")

	includedirs { __INCL__ }

	files { __SRC__ }

	defines { __DEF__ }

	links { __LINKS__ }

	flags {
		cppdialect "C++14"
	}

	configuration "Debug"
		defines { "DEBUG" }
		symbols "On"

	configuration "Release"
		optimize (_global_optimize_flags)

	configmap {
		["Debug"] = "Debug",
		["Release"] = "Release",
	}
"""

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

	replacemap = {
		"__NAME__" : fixed_name,
		"__INCL__" : ",".join(['"' + ctx.final_path(target_build_folder,d) + '"' for d in all_includes]),
		"__SRC__" : ",".join(['"' + ctx.final_path(target_build_folder,d) + '"' for d in all_sources]),
		"__DEF__" : ",".join(['"' + d + '"' for d in all_defines]),
		"__LINKS__" : ",".join(['"' + d + '"' for d in all_libs]),
		"__KIND__" : premake_project_kind[item["kind"]],
		"__PLATFORM__" : item["platform"],
		"__BUILDER__" : item["builder"],
	}

	#generator.premake.lua
	file_handle.write(generate_project_str(replacemap))

def generate_project_str(replmap):
	proj_data = premake_project_template
	for word, value in replmap.items():
		proj_data = proj_data.replace(word, value)
	return "\n" + proj_data + "\n"

def run(context, target_build_folder, project_stack):

	premake_path = os.path.join(target_build_folder,"generator.premake.lua")
	f = open(premake_path,"w")
	f.write(premake_workspace)

	for k,v in project_stack.items():
		append_project_to_file(f, context, target_build_folder, project_stack, v)

	f.close()

	premake_os = premake_platform_map[context.platform]
	premake_builder = premake_builder_map[context.builder]

	output = subprocess.run([context.envget("premake5"),"--verbose","--os=" + premake_os,"--file=" + premake_path,premake_builder])
	return output
