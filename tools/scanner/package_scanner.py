
import os
import sys
import json
import srcbuild_default_paths

def _ignore_filename(filename):
	if filename.startswith("."):
		return True

	return False

def _is_module(filename):
	if filename.endswith('.pak.py'):
		return True

	return False

def _scan_folder_structure(root_path):
	packages = {}

	index = 0
	# Walk through the directory and its subdirectories
	for root, dirs, files in os.walk(root_path):
		for file in files:
			if _ignore_filename(file):
				continue
			
			if _is_module(file):
				full_path = os.path.join(root, file)
				full_path = os.path.relpath(full_path, root_path)

				pfile = packages.get(file, None)
				if pfile != None:
					raise Exception(f"Duplicate package `{file}` found at\n 1:{pfile}\n 2:{full_path}")

				packages[file] = full_path

				print(str(index).rjust(4) + f" | {full_path}")
				index += 1
			
	return packages

	
def discover_local_packages(scan_location, destination_folder):
	packs = _scan_folder_structure(scan_location)

	final_modules_folder = os.path.join(destination_folder, srcbuild_default_paths.default_modules_folder )

	if not os.path.exists(final_modules_folder):
		os.makedirs(final_modules_folder)

	local_modules_file = os.path.join(final_modules_folder, srcbuild_default_paths.default_index_filename)

	content = {
		"workspace" : scan_location,
		"modules" : packs,
	}

	f = open(local_modules_file, "w")
	f.write(json.dumps(content,indent=2))
	f.close()

	print(f"\nGenerated -> {local_modules_file}\n")

def scan(scan_location, destination_folder):
	discover_local_packages(scan_location, destination_folder);