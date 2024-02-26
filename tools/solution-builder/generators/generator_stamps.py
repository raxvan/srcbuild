
import os
import sys
import shutil

import generator_utils
import srcbuild_default_paths

_this_dir = os.path.dirname(os.path.abspath(__file__))

class StampsContext(generator_utils.GeneratorInterface):
	def __init__(self):
		template_folder = os.path.join(_this_dir, "templates", "scripts")

		fc = [
			"stamp.py",
		]
		self.files_to_copy = {x : os.path.join(template_folder, x) for x in fc }

	def __str__(self):
		return "stamps"

	def prebuild(self, solution):
		for k,v in self.files_to_copy.items():
			output_path = os.path.join(solution.output, k)
			shutil.copyfile(v,output_path)
		
	def accept(self, solution, module):
		return False

	def postbuild(self, solution):
		
		result = set()
		
		#all files
		for m in solution.get_modules():
			if (m.enabled == False):
				continue

			for f in m.content.query_all_files():
				result.add(str(os.path.relpath(f, solution.output)))

			#add module json for stamp
			modulefile = os.path.join(solution.modules_folder, m.get_name() + ".json")
			pakfile = m.get_package_absolute_path()

			result.add(str(os.path.relpath(modulefile, solution.output)))
			result.add(str(os.path.relpath(pakfile, solution.output)))

		config_file = srcbuild_default_paths.get_build_config_init(solution.output)
		result.add(str(os.path.relpath(config_file, solution.output)))

		sresult = sorted(list(result))

		outfilr = srcbuild_default_paths.get_build_stamps_file(solution.output)
		#prepare file:
		f = open(outfilr, "w")
		f.write(str(len(sresult)) + "\n")

		#write contents
		for r in sresult:
			f.write(r)
			f.write("\n")
		f.close()

		print(f"Generated file list: {outfilr}")


def create(workspace, priority):
	return StampsContext()



