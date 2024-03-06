
import os

#workspace:
default_workspace = "/wspace/workspace"
default_modules_folder = ".modules"
default_index_filename = "index.local.json"

def get_pack_info(abs_path_to_pack):
	abs_pack_dir, filename = os.path.split(abs_path_to_pack)
	pack_name = filename.replace(".pak.py","")
	simplified_name = pack_name #_name.replace(".","_").replace("-","_").lower()
	return (
		abs_pack_dir,
		filename,
		pack_name,
		simplified_name
	)

#build:
def get_build_folder(abs_path_to_pack):
	abs_pack_dir, filename = os.path.split(abs_path_to_pack)
	return os.path.join(abs_pack_dir, "build", filename.replace(".pak.py",""))
	

def get_build_invremental_data(build_dir):
	return os.path.join(build_dir, ".incremental")

def get_build_tools_dir(build_dir):
	return os.path.join(build_dir, ".srcbuild")

def get_build_modules_data(build_dir):
	return os.path.join(build_dir, ".srcbuild", "modules")


#individual files:
def get_build_config_init(build_dir):
	return os.path.join(build_dir, ".srcbuild", "config.ini")

def get_build_solution_files(build_dir):
	return os.path.join(build_dir, ".srcbuild", "solution-files.txt")

