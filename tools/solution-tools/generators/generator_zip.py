
import os
import generator_query
import zipfile
import datetime
import time
import json


##################################################################################################################################

def _nice_time():
	n = datetime.datetime.now()
	r = n.astimezone(datetime.timezone.utc).strftime("%Z/%z/%Y-%m-%d/%H:%M:%S")
	u = time.mktime(n.timetuple())
	return (r,u)

#def _nice_time():
#	utc_time = datetime.datetime.now(datetime.timezone.utc)
#	local_time = utc_time.astimezone()
#	return str(local_time)

class ZipContext():
	def __init__(self, solution, config, workspace):

		self.solution = solution
		self.config = config
		self.workspace_root = workspace

	def get_files_list(self, out_list, item):

		#all_includes = generator_query.query_include_paths(self.solution, item)
		all_sources = generator_query.query_sources(self.solution, item)
		#all_defines = generator_query.query_defines(self.solution, item)
		#all_links = generator_query.query_libs(self.solution, item)
		#extra_links = generator_query.query_extra_libs(self.solution, item) #TODO

		out_list.extend(all_sources)
		out_list.append(item.get_package_absolute_path())

	def run(self, solution_name, output_dir):

		workspace_root_dir = self.workspace_root
		root_item = self.solution.get_module(solution_name)
		root_item_file = root_item.get_package_filename()
		root_item_dir = os.path.relpath(root_item.get_package_dir(), workspace_root_dir)
		root_item_wpath = os.path.relpath(root_item.get_package_absolute_path(), workspace_root_dir)
		
		file_list = []
		package_list = {}
		package_dependency = {}

		root_item.dump_dependency_tree(package_dependency)
		for m in self.solution.get_modules():
			if (m.enabled == False):
				continue
			self.get_files_list(file_list, m)
			package_list[m.key] = m.get_package_relative_path(workspace_root_dir)

		#files
		metadata_filename = "package.json"
		target_zip_file = os.path.join(output_dir,"package.zip")
		target_metadata_file = os.path.join(output_dir,metadata_filename)

		#info
		info_string = f" [{len(file_list)} files -> {target_zip_file}]"
		print(info_string)
		
		#zip
		#zip_compression_method = zipfile.ZIP_LZMA
		zip_compression_method = zipfile.ZIP_DEFLATED
		fzip = zipfile.ZipFile(target_zip_file, 'w', compression=zip_compression_method)
		

		#process
		index = 0
		total_files_count = len(file_list)
		progress_bar_size = len(info_string) - 3

		relateive_file_list = []
		#loop over files
		for f in file_list:

			#progress before
			index += 1
			progress = (index / total_files_count) 
			int_progress = int(progress * progress_bar_size)
			bar = '#' * int_progress + ' ' * (progress_bar_size - int_progress)
			print(f"\r [{bar}]:[{index}/{total_files_count}] {progress * 100.0:.2f}%", end='')

			#add file to zip archive
			relative_path = os.path.relpath(f, workspace_root_dir)
			fzip.write(f, relative_path)

			#store metadata
			relateive_file_list.append(relative_path)

		create_time_str,create_time_unix = _nice_time()
		metadata = {
			"time" : create_time_str,
			"unix-timestamp" : create_time_unix,
			"package-path" : root_item_wpath,
			"package-file" : root_item_file,
			"package-dir" : root_item_dir,
			"package-key" : root_item.key,
			"file-count" : len(file_list),
			"files" : relateive_file_list,
			"packages" : package_list,
			"dependency-graph" : package_dependency,
		}
		fjson = open(target_metadata_file, "w")
		fjson.write(json.dumps(metadata, indent=2))
		fjson.close()

		fzip.write(target_metadata_file, metadata_filename)

		fzip.close()

		print("\nDone.")

		return target_zip_file



