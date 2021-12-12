
import os
import sys

import shutil
import shell_utils
import generator_query

_this_dir = os.path.dirname(os.path.abspath(__file__))

cmake_workspace = shell_utils.read_text_file(os.path.join(_this_dir,"..","templates","cmake_workspace_template.txt"))
cmake_project = shell_utils.read_text_file(os.path.join(_this_dir,"..","templates","cmake_project_template.txt"))

files_to_copy = {
	"_generate_vs.bat" : os.path.join(_this_dir,"..","templates","cmake_generate_vs.bat"),
	"build.sh" : os.path.join(_this_dir,"..","templates","cmake_build.sh"),
	"clean.sh" : os.path.join(_this_dir,"..","templates","cmake_clean.sh"),
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

def _get_project_name(item):
	fixed_name = item.get_name()

	if item.content.get_property_or_die("type") == "exe":
		fixed_name = "_" + fixed_name

	return fixed_name

def _update_warnings(replacemap,item):
	warnings_map = {
		"off" : "NO",
		"default" : "YES",
		"full" : "YES",
	}
	w = item.content.get_property_or_die("warnings")
	if w == "off":
		replacemap["__FULL_WARNINGS__"] = "NO"
		replacemap["__DISABLE_WARNINGS__"] = "YES"
	elif w == "default":
		replacemap["__FULL_WARNINGS__"] = "NO"
		replacemap["__DISABLE_WARNINGS__"] = "NO"
	elif w == "full":
		replacemap["__FULL_WARNINGS__"] = "YES"
		replacemap["__DISABLE_WARNINGS__"] = "NO"
	

def _get_cpp_standard(item):
	return item.options.get_value_or_die("cppstd")

##################################################################################################################################

def generate_cmakelists(project_stack, target_build_folder, item):
	all_includes = generator_query.query_include_paths(project_stack, item)
	all_sources = generator_query.query_sources(project_stack, item)
	all_defines = generator_query.query_defines(project_stack, item)
	all_links = generator_query.query_libs(project_stack, item)

	mrp = generator_query.make_relative_path

	itype = item.content.get_property_or_die("type")
	name = _get_project_name(item)

	replacemap = {
		"__NAME__" : name,
		"__INCL__" : "\n\t".join(["${CMAKE_CURRENT_SOURCE_DIR}/../../" + mrp(d, target_build_folder) for d in all_includes]),
		"__SRC__" : "\n\t".join(["${CMAKE_CURRENT_SOURCE_DIR}/../../" + mrp(d, target_build_folder) for d in all_sources]),
		"__DEF__" : "\n\t".join(all_defines),
		"__LINKS__" : "\n\t".join(all_links),
		"__ADD_TYPE__" : cmake_add_type[itype],
		"__ADD_TYPE_DATA__" : cmake_add_type_data[itype],
		"__STANDARD__" : _get_cpp_standard(item),
		"__THREADS__" : "YES"
	}
	_update_warnings(replacemap,item)

	cmakelists_dir = os.path.join(target_build_folder,"projects",name)
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

def append_project_to_file(solution_file, project_stack, target_build_folder, item):
	generate_cmakelists(project_stack, target_build_folder, item);
	solution_file.write("add_subdirectory(projects/" + _get_project_name(item) + ")\n")

def generate_header(root_project):
	sname = "_" + root_project.get_name().replace("-","_")
	return cmake_workspace.replace("__SOLUTION_NAME__",sname)

def run(project_stack, root_project, options, output_dir):

	cmake_path = os.path.join(output_dir,"CMakeLists.txt")
	f = open(cmake_path,"w")

	header = generate_header(root_project)
	f.write(header)

	#for k,v in project_stack.items():
	#	append_project_to_file(f, context, target_build_folder, project_stack, v)
	for k,v in project_stack.items():
		append_project_to_file(f, project_stack, output_dir, v)

	f.close()

	#generate other files
	for k,v in files_to_copy.items():
		output_path = os.path.join(output_dir,k)
		shutil.copyfile(v,output_path)
