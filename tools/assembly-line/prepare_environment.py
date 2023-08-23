
import os
import sys

project_type = sys.argv[1]

abs_path_to_project = None

if project_type == "win-exe" or project_type == "win-lib":
	abs_path_to_project = os.path.join(os.environ['THIS_WORKSPACE'], os.environ['TARGET_PROJECT_IN_WORKSPACE'])
elif project_type == "wspace-exe":
	abs_path_to_project = os.path.join("/wspace/workspace",os.environ['TARGET_PROJECT_IN_WORKSPACE'])


basedir, basename = os.path.split(abs_path_to_project)
raw_name = basename.replace(".pak.py","")

def decl_win_var(key, value):
	print("set " + key + "=" + value)

def decl_wspace_var(key, value):
	print("export " + key + "=" + value)


if project_type == "win-exe":
	decl_win_var("ABS_SOLUTION_DIR", os.path.join(basedir, "build", "msvc-" + raw_name))
	decl_win_var("SOLUTION_NAME", "_" + raw_name + ".sln")
	decl_win_var("EXECUTABLE_NAME", "_" + raw_name + ".exe")
elif project_type == "win-lib":
	decl_win_var("ABS_SOLUTION_DIR", + os.path.join(basedir, "build", "msvc-" + raw_name))
	decl_win_var("SOLUTION_NAME", + "_" + raw_name + ".sln")
elif project_type == "wspace-exe":
	decl_wspace_var("ABS_SOLUTION_DIR", os.path.join(basedir, "build", "cmake-" + raw_name))
	decl_wspace_var("EXECUTABLE_NAME", "_" + raw_name)

