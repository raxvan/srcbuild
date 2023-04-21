
import os
import sys

project_type = sys.argv[1]

abs_path_to_project = None

if project_type == "win-exe" or project_type == "win-lib":
	abs_path_to_project = os.path.join(os.environ['THIS_WORKSPACE'],os.environ['TARGET_PROJECT_IN_WORKSPACE'])
elif project_type == "wspace-exe":
	abs_path_to_project = os.path.join("/wspace/workspace",os.environ['TARGET_PROJECT_IN_WORKSPACE'])


basedir, basename = os.path.split(abs_path_to_project)
raw_name = basename.replace(".pak.py","")

if project_type == "win-exe":
	print("set ABS_SOLUTION_DIR=" + os.path.join(basedir, "build", "msvc-" + raw_name))
	print("set SOLUTION_NAME=" + "_" + raw_name + ".sln")
	print("set EXECUTABLE_NAME=" + "_" + raw_name + ".exe")
elif project_type == "win-lib":
	print("set ABS_SOLUTION_DIR=" + os.path.join(basedir, "build", "msvc-" + raw_name))
	print("set SOLUTION_NAME=" + "_" + raw_name + ".sln")
elif project_type == "wspace-exe":
	print("export ABS_SOLUTION_DIR=" + os.path.join(basedir, "build", "cmake-" + raw_name))
	print("export EXECUTABLE_NAME=" + "_" + raw_name)
	#print("set SOLUTION_NAME=" + "_" + raw_name + ".sln")
	#print("set EXECUTABLE_NAME=" + "_" + raw_name + ".exe")

