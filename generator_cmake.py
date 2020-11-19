
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

cmake_workspace = ciutil.read_text_file(os.path.join(_this_dir,"templates","cmake_workspace_template.txt")) 
cmake_project = ciutil.read_text_file(os.path.join(_this_dir,"templates","cmake_project_template.txt")) 
files_to_copy = {
	"_cmake_generate_solution.bat" : os.path.join(_this_dir,"templates","cmake_generate_solution.bat")
}


cmake_add_type = {
	"exe" : "add_executable",
	"lib" : "add_library",
	
	"dll" : "add_library",
	"view" : "add_library",
}
cmake_add_type_data = {
	"exe" : "",
	"lib" : "STATIC",
	
	"dll" : "SHARED",
	"view" : "STATIC",
}

def generate_cmakelists(ctx,target_build_folder, project_name, project_stack, item):
	all_includes = ctx.collapse_includes( project_stack, item)
	all_sources = ctx.collapse_sources( project_stack, item)
	all_defines = ctx.collapse_defines( project_stack, item)
	(all_local_libs,all_external_libs) = ctx.collapse_libs( project_stack, item)
    
	all_libs = list(set(all_local_libs + all_external_libs))
	all_libs.sort()

	_warnings = "NO"
	if item['options']['warnings'] == True:
		_warnings = "YES"

	replacemap = {
		"__NAME__" : project_name,
		"__INCL__" : "\n\t".join(["${CMAKE_SOURCE_DIR}/" + ctx.final_path(target_build_folder,d) for d in all_includes]),
		"__SRC__" : "\n\t".join(["${CMAKE_SOURCE_DIR}/" + ctx.final_path(target_build_folder,d) for d in all_sources]),
		"__DEF__" : "\n\t".join([d for d in all_defines]),
		"__LINKS__" : "\n\t".join([d for d in all_libs]),
		"__ADD_TYPE__" : cmake_add_type[item["kind"]],
		"__ADD_TYPE_DATA__" : cmake_add_type_data[item["kind"]],
		"__PLATFORM__" : item["platform"],
		"__BUILDER__" : item["builder"],
		"__STANDARD__" : item["cpp-standard"],
		"__WARNINGS__" : _warnings,
		"__KIND__" : item['kind']
	}
	cmakelists_dir = os.path.join(target_build_folder,"projects",project_name)
	if not os.path.exists(cmakelists_dir):
		os.makedirs(cmakelists_dir)
	cmakelists_file = os.path.join(cmakelists_dir,"CMakeLists.txt")
	f = open(cmakelists_file,"w")

	proj_data = cmake_project
	for word, value in replacemap.items():
		proj_data = proj_data.replace(word, value)
	proj_data = "\n" + proj_data + "\n"
	f.write(proj_data)

	f.close();

def append_project_to_file(file_handle, ctx, target_build_folder, project_stack, item):
    
	project_name = item['name']
	if item['kind'] == "exe":
		project_name = "_" + project_name

	generate_cmakelists(ctx, target_build_folder, project_name, project_stack, item);
    
	#add add_subdirectory()
	file_handle.write("add_subdirectory(projects/" + project_name + ")\n")

def generate_header(context):
	sname = "_" + context.name.replace("-","_")
	return cmake_workspace.replace("__SOLUTION_NAME__",sname)

def run(context, target_build_folder, project_stack):

	cmake_path = os.path.join(target_build_folder,"CMakeLists.txt")
	f = open(cmake_path,"w")

	header = generate_header(context)
	f.write(header)

	for k,v in project_stack.items():
		append_project_to_file(f, context, target_build_folder, project_stack, v)

	f.close()

	#generate other files
	for k,v in files_to_copy.items():
		output_path = os.path.join(target_build_folder,k)
		shutil.copyfile(v,output_path)

