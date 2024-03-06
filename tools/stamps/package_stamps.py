
import os
import sys
import json
import srcbuild_default_paths

class StampInfo():
	def __init__(self, name, stamps_folder, stamp_file):
		self.name = name

		self.stamps_folder = None
		if os.path.exists(stamps_folder):
			self.stamps_folder = stamps_folder

		self.stamp_file = None
		if os.path.exists(stamp_file):
			self.stamp_file = stamp_file

		self.stamps = None

	def load_stamps(self):
		if self.stamps_folder == None:
			return None
		
		result = set()
		self.stamps = {}
		for f in os.listdir(self.stamps_folder):
			abs_file_path = os.path.join(self.stamps_folder, f)
			f = open(abs_file_path, "r")
			lines = f.readlines()
			f.close()
			for l in lines:
				ls = l.strip()
				result.add(ls)
				self.stamps.setdefault(ls, []).append(f)

		return result

	def has_stamp(self, s):
		if self.stamps != None:
			if s in self.stamps:
				return True
		return False


def get_stamps(index_file):
	f = open(index_file,"r")
	content = json.load(f)
	f.close()

	workspace = content['workspace']
	packages = content['modules']

	result = {}
	index = 0
	for k, v in packages.items():
		abs_pachage_path = os.path.join(workspace, v)

		build_folder = srcbuild_default_paths.get_build_folder(abs_pachage_path)
		
		stamps_folder = os.path.join(build_folder, "stamps")
		stamps_index = srcbuild_default_paths.get_build_solution_files(build_folder)
		
		result[k] = StampInfo(k, stamps_folder, stamps_index)
		
		print(str(index).rjust(4) + f" | {k}")
		index += 1

	return result

def discover_stamps(workspace_folder):
	final_modules_folder = os.path.join(workspace_folder, srcbuild_default_paths.default_modules_folder )

	if not os.path.exists(final_modules_folder):
		os.makedirs(final_modules_folder)

	#index file
	local_modules_file = os.path.join(final_modules_folder, srcbuild_default_paths.default_index_filename)
	
	if not os.path.exists(local_modules_file):
		print(f"\nNo index file found at -> {local_modules_file}\n")	

	return get_stamps(local_modules_file)


def print_header(stamps_list, modules_max, stamps_max):
	index = 0;
	print("-" * (modules_max + 2 + len(stamps_list) * 4))
	print()
	for s in stamps_list:
		print(s.rjust(modules_max) + f" | {index}")
		index += 1
	print()

def print_table(stamps, stamps_set, stamps_list, modules_max):
	print("-" * (modules_max + 2), end="")

	for index in range(len(stamps_list)):
		print(str(index).center(3,"-"), end="-")
	print()

	for k, v in stamps.items():


		print(k.rjust(modules_max), end=" |")
		for s in stamps_list:
			if v.has_stamp(s):
				print(" x ", end="|")
			else:
				print("   ", end="|")
		print("\n" + "-" * (modules_max + len(stamps_list) * 4 + 2))

def print_footer(offset, all_stamps, stamps_max):
	for i in range(stamps_max):
		print(" " * offset, end="")
		for string in all_stamps:
			if i < len(string):
				print(f" {string[i]} ", end="|")
			else:
				print("   ", end="|")
		print()

def show_all(workspace_folder):
	stamps = discover_stamps(workspace_folder)
	stamps_set = set()
	for k, v in stamps.items():
		s = v.load_stamps()
		if s != None:
			stamps_set.update(s)

	stamps_list = sorted(list(stamps_set))

	stamps_max_len = max(len(s) for s in stamps_list)
	modules_max_len = max(len(k) for k,_ in stamps.items())

	

	print_header(stamps_list, modules_max_len, stamps_max_len)
	print_table(stamps, stamps_set, stamps_list, modules_max_len)
	print_footer(modules_max_len + 2, stamps_list, stamps_max_len)