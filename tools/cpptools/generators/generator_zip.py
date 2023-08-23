
import os
import generator_query
import zipfile
import datetime
import time


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
	def __init__(self, solution, config):

		self.solution = solution
		self.config = config

	def get_files_list(self, out_list, item):

		#all_includes = generator_query.query_include_paths(self.solution, item)
		all_sources = generator_query.query_sources(self.solution, item)
		#all_defines = generator_query.query_defines(self.solution, item)
		#all_links = generator_query.query_libs(self.solution, item)
		#extra_links = generator_query.query_extra_libs(self.solution, item) #TODO

		out_list.extend(all_sources)
		out_list.append(item.get_package_absolute_path())

	def run(self, solution_name, output_dir):

		workspace_root_dir = "/wspace/workspace"
		root_item = self.solution.get_module(solution_name)
		root_item_file = root_item.get_package_filename()
		root_item_dir = os.path.relpath(root_item.get_package_dir(), workspace_root_dir)
		root_item_wpath = os.path.relpath(root_item.get_package_absolute_path(), workspace_root_dir)
		
		file_list = []
		for m in self.solution.get_modules():
			self.get_files_list(file_list, m)

		#files
		target_metadata_filename = "package.metadata"
		target_ini_filename = "package.ini"
		target_zip_file = os.path.join(output_dir,"package.zip")
		target_metadata_file = os.path.join(output_dir,target_metadata_filename)
		target_ini_file = os.path.join(output_dir,target_ini_filename)


		#info
		create_time,create_time_unix = _nice_time()

		fini = open(target_ini_file, "w");
		fini.write(f"TIME={create_time}\n")
		fini.write(f"UNIX_TIMESTAMP={create_time_unix}\n")
		fini.write(f"ROOT_WPATH={root_item_wpath}\n")
		fini.write(f"ROOT_FILE={root_item_file}\n")
		fini.write(f"ROOT_DIR={root_item_dir}\n")
		fini.write(f"FILES={len(file_list)}\n")
		fini.close()

		finfo = open(target_metadata_file, "w")
		finfo.write(f"#TIME:{create_time[0]}\n")
		finfo.write(f"#UNIX-TIMESTAMP={create_time_unix}\n")
		finfo.write(f"#ROOT-WPATH:{root_item_wpath}\n")
		finfo.write(f"#ROOT-FILE:{root_item_file}\n")
		finfo.write(f"#ROOT-DIR:{root_item_dir}\n")
		finfo.write(f"#FILES:{len(file_list)}\n")
		
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

			#add entry to metadata file
			finfo.write(f"+{relative_path}\n")


		end_time,end_time_unix = _nice_time()
		finfo.write(f"#DURATION:{end_time_unix - create_time_unix}\n")
		finfo.close()

		#fzip.write(target_metadata_file, target_metadata_filename)
		fzip.write(target_ini_file, target_ini_filename)

		fzip.close()

		print("\nDone.")




