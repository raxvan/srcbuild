
import os

#workspace:
default_workspace = "/wspace/workspace"
default_modules_folder = ".modules"
default_index_filename = "index.local.json"


#build:
def get_build_invremental_data(build_dir):
	return os.path.join(build_dir, ".incremental")

def get_build_tools_dir(build_dir):
	return os.path.join(build_dir, ".srcbuild")

def get_build_modules_data(build_dir):
	return os.path.join(build_dir, ".srcbuild", "modules")


#individual files:
def get_build_config_init(build_dir):
	return os.path.join(build_dir, ".srcbuild", "config.ini")

def get_build_stamps_file(build_dir):
	return os.path.join(build_dir, ".srcbuild", "stamps.txt")

