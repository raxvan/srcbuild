
import os
import shutil
import fnmatch
import filecmp
import sys
import glob
import re
import json
import sys
import inspect
import subprocess
import argparse

#################################################################################################

env_paths = {
	"premake5" : os.getenv("PREMAKE5_EXE","/build/premake5/bin/release/premake5"),
}

#################################################################################################
#################################################################################################

def get_builders_list():
	return [
		"vs2019",
		"vs2017",
		"vs2015",
		"make"
	]

def get_platform_map():
	return {
		"win32" : "BUILD_PLATFORM_WIN32",
		"linux" : "BUILD_PLATFORM_LINUX",
		"android" : "BUILD_PLATFORM_ANDROID",
		"ios" : "BUILD_PLATFORM_IOS",
		"osx" : "BUILD_PLATFORM_OSX",
	}

def _decode_project_name(abs_file_path):
	_, filename = os.path.split(abs_file_path)

	return filename.replace(".py","").replace("prj.","")

class Generator():
	def __init__(self, default_extensions = None):
		parser = argparse.ArgumentParser()
		parser.add_argument('builder', choices=get_builders_list(), help='tool used to build stuff, like your ide')
		parser.add_argument('platform', choices=get_platform_map().keys(), help='target platform')
		parser.add_argument('-o', '--out', dest="out", help='output folder path', nargs=1)
		parser.add_argument('-e', '--env_paths', action="store_true", help='prints out known paths')

		args = parser.parse_args()

		if args.env_paths == True:
			print(json.dumps(env_paths, indent=4, sort_keys=True))
			exit()


		#p#rint(args)

		top_calling_script = os.path.abspath((inspect.stack()[1])[1])
		self.abs_project_path, _ = os.path.split(top_calling_script)

		self.default_ext = default_extensions

		self.builder = args.builder
		self.platform = args.platform
		self.output = None
		if args.out != None:
			self.output = args.out[0]

		#self.global_defines = args.define

		self.name = _decode_project_name(sys.argv[0])

		print("\n--------------------------------------------:: " + self.name + " >>>")	
		#print("	>defines:" + str(self.global_defines))
		if self.output != None:
			print("	>output:" + self.output)

	def _validate_platfroms(self,platform_list):
		known_list = get_platform_map()

		for p in platform_list:
			if not p in known_list:
				raise Exception("Unknown platform filter `" + p + "` accepted platforms:\n" + "\n".join(known_list.keys()))

	def envget(self,*args):
		itr = env_paths
		for a in args:
			itr = itr.get(a,None)
			if itr == None:
				raise Exception("No path available at: [" + ",".join(args) + "]")

		return itr

	def env(self,*args):
		itr = env_paths
		for a in args:
			itr = itr.get(a,None)
			if itr == None:
				raise Exception("No path available at: [" + ",".join(args) + "]")

		return "env>" + itr

	def filter(self, all_sources, target_platforms, sources_to_filter):
		platform_files_set = set(sources_to_filter)

		if type(target_platforms) is list:
			self._validate_platfroms(target_platforms)
			if self.platform in target_platforms:
				return list(set(all_sources + sources_to_filter))
			else:
				return [s for s in all_sources if not s in sources_to_filter]

		elif target_platforms in ["+","*"]:
			return list(set(all_sources + sources_to_filter))

		elif target_platforms == "-" or target_platforms == None:
			return [s for s in all_sources if not s in sources_to_filter]

		elif target_platforms != "*":
			self._validate_platfroms([target_platforms])
			if target_platforms == self.platform:
				return list(set(all_sources + sources_to_filter))
			else:
				return [s for s in all_sources if not s in sources_to_filter]

		raise Exception("Unknown filter:" + target_platforms)
	

	#if platform does notmatch then we remove those files from all sources
	def globfilter(self, all_sources, target_platforms, rel_dir_path, extensions = None):
		platform_files = self.glob(rel_dir_path, extensions)
		return self.filter(all_sources,target_platforms,platform_files)

	def glob(self, rel_dir_path, extensions = None):
		_ext = self.default_ext
		if extensions != None:
			_ext = extensions
		search_folder = os.path.abspath(os.path.join(self.abs_project_path,rel_dir_path))
		matches = []
		print("Searching: " + search_folder + " for: " + ", ".join(_ext))

		#walk tree structure
		for root, dirnames, filenames in os.walk(search_folder):
			for f in filenames:
				if _ext != None:
					filename, file_extension = os.path.splitext(f)
					if(file_extension in _ext):
						matches.append(os.path.join(root, f))
				else:
					matches.append(os.path.join(root, f))


		print("    :" + str(len(matches)) + " - files found");
		return matches


	def find(self, rel_dir_path, pattern):
		regex = fnmatch.translate(pattern)
		reobj = re.compile(regex)

		search_folder = os.path.abspath(os.path.join(self.abs_project_path,rel_dir_path))
		matches = []
		print("Matching: " + pattern)

		#walk tree structure
		for root, dirnames, filenames in os.walk(search_folder):
			for f in filenames:
				if not reobj.match(f):
					continue
				matches.append(os.path.join(root, f))
		print("    :" + str(len(matches)) + " - files found");
		return matches

	def run(self,kind, **kwargs):

		includes = kwargs.get("incl",[])
		src = kwargs.get("src",[])
		defines = kwargs.get("defines",[])
		depends = kwargs.get("depends",[])
		extra_libs = kwargs.get("libs",[])

		if not type(includes) is list:
			includes = [includes]
		if not type(src) is list:
			src = [src]

		#add builtin defines
		defines.append(get_platform_map()[self.platform])
		

		#calculate build output
		builder_solution_folder = os.path.join(self.abs_project_path,"build",self.name + "_" + self.platform + "_" + self.builder )
		alaternative_target = self.output
		if alaternative_target != None:
			builder_solution_folder = alaternative_target
		if not os.path.exists(builder_solution_folder):
			os.makedirs(builder_solution_folder)

		project_metadata = {}

		project_metadata["name"] = self.name
		project_metadata["generator-dir"] = self.abs_project_path

		project_metadata["args"] = sys.argv
		project_metadata["builder"] = self.builder
		project_metadata["platform"] = self.platform
		project_metadata["kind"] = kind
		project_metadata["build"] = builder_solution_folder

		#defines
		(_public_defines,_private_defines,_global_defines) = self._evaluate_defines(defines)

		project_metadata["public-defines"] = list(set(_public_defines))
		project_metadata["private-defines"] = list(set(_private_defines))
		project_metadata["global-defines"] = list(set(_global_defines))

		#src
		project_metadata["sources"] = list(set([str(self._solve_path(p)) for p in src]))

		#incl
		(_public_includes,_private_includes) = self._evaluate_includes(includes)

		project_metadata["public-includes"] = _public_includes #[str(self._solve_path(p)) for p in public_includes]
		project_metadata["private-includes"] = _private_includes #[str(self._solve_path(p)) for p in private_includes]

		#chain
		(_public_dependency,_private_dependency) = self._evaluate_dependency_list(depends,builder_solution_folder)

		project_metadata["public-dependency"] = _public_dependency #list(set(self._evaluate_dependency_list(depends,builder_solution_folder)))
		project_metadata["private-dependency"] = _private_dependency #list(set(self._evaluate_dependency_list(depends,builder_solution_folder)))

		#extra links
		project_metadata["links"] = list(set(extra_libs))

		#sort lists
		project_metadata["sources"].sort()
		project_metadata["public-defines"].sort()
		project_metadata["private-defines"].sort()
		project_metadata["global-defines"].sort()
		project_metadata["links"].sort()

		#dump json for reasoning
		about_file = os.path.join(builder_solution_folder,self.name + ".prj.json")
		self._write_final_project(about_file, project_metadata)

		if(alaternative_target == None):
			#load all projects
			project_stack = {
				self.name : project_metadata
			}
			self._load_projects_recursive(builder_solution_folder, project_metadata['public-dependency'], project_stack)
			self._load_projects_recursive(builder_solution_folder, project_metadata['private-dependency'], project_stack)
			#run generator
			self._run_generator(builder_solution_folder, project_stack)

		return project_metadata

	def _evaluate_defines(self, defines):
		public_includes = []
		private_includes = []
		global_defines = []

		for p in defines:
			path = p
			target = public_includes
			if p.count("private>") > 0:
				path = path.replace("private>","")
				target = private_includes
			if p.count("public>") > 0:
				path = path.replace("public>","")
				target = public_includes
			if p.count("global>") > 0:
				path = path.replace("global>","")
				target = global_defines
			target.append(path)

		return (public_includes,private_includes,global_defines);

	def _evaluate_includes(self,include_list):
		public_includes = []
		private_includes = []

		for p in include_list:
			path = p
			target = public_includes
			if p.count("private>") > 0:
				path = path.replace("private>","")
				target = private_includes
			if p.count("public>") > 0:
				path = path.replace("public>","")
				target = public_includes
			target.append(self._solve_path(path))

		return (public_includes,private_includes)

	def _evaluate_dependency_list(self,dependency_list,builder_solution_folder):

		public_dependency = []
		private_dependency = []

		result = []
		for d in dependency_list:
			path = d
			target = public_dependency
			if path.count("private>") > 0:
				path = path.replace("private>","")
				target = private_dependency
			if path.count("public>") > 0:
				path = path.replace("public>","")
				target = public_dependency

			target.append(_decode_project_name(path))

			dependency_file_path = self._find_project_path(path)
			if dependency_file_path.endswith(".py"):
				#esult.append(_decode_project_name(dependency_file_path))

				arguments = ["python3",dependency_file_path]
				arguments = arguments + ["--out",builder_solution_folder]
				arguments = arguments + [self.builder,self.platform]

				output = subprocess.run(arguments)
				print(output)
			else:
				raise Exception("Unknown dependency:" + path)

		return (public_dependency,private_dependency)

	def _find_project_path(self,path):
		p = os.path.join(self.abs_project_path,path)
		if os.path.exists(p):
			return os.path.abspath(p)

		raise Exception("Failed to locate path: `" + path + "` in:\n	" +
			self.abs_project_path
		)

	def _solve_path(self,path):
		if path.count("env>") > 0:
			return path

		p = self._find_project_path(path)
		return os.path.relpath(p,self.abs_project_path)

	def _run_generator(self, target_build_folder, project_stack):

		#propagate global properties
		global_defines = []
		for k,v in project_stack.items():
			global_defines.extend(v['global-defines'])

		for k,v in project_stack.items():
			v['global-defines'] = global_defines

		import generator_premake
		generator_premake.run(self, target_build_folder, project_stack)


	def _write_final_project(self,  target_json_abs_path, result_json):
		with open(target_json_abs_path, 'w') as fp:
			fp.write(json.dumps(result_json, indent=4, sort_keys=True))

	def _load_projects_recursive(self, build_directory, dependency_list, project_stack):
		for dep in dependency_list:
			json_metadata = project_stack.get(dep,None)
			if json_metadata == None:
				name = dep + ".prj.json"
				with open(os.path.join(build_directory,name), 'r') as f:
					json_metadata = json.load(f)
				project_stack[dep] = json_metadata
				self._load_projects_recursive(build_directory, json_metadata['public-dependency'], project_stack)
				self._load_projects_recursive(build_directory, json_metadata['private-dependency'], project_stack)


	def final_path(self, target_build_folder, itm):
		if itm.count("env>") > 0:
			return itm.replace("env>","")
		else:
			return os.path.relpath(itm,target_build_folder)

	def collapse_includes(self, project_stack, item, with_private = True):
		generator_path = item['generator-dir']
		includes = []
		includes = includes + [os.path.join(generator_path,d) for d in item['public-includes']]

		if with_private == True:
			includes = includes + [os.path.join(generator_path,d) for d in item['private-includes']]

		for d in item['public-dependency']:
			includes = includes + self.collapse_includes( project_stack, project_stack[d], False)

		if with_private == True:
			for d in item['private-dependency']:
				includes = includes + self.collapse_includes( project_stack, project_stack[d], False)

		return includes

	def collapse_sources(self, project_stack, item):
		generator_path = item['generator-dir']
		src = list(set([os.path.join(generator_path,d) for d in item['sources']]))
		src.sort();
		return src

	def collapse_defines(self, project_stack, item, with_private = True):
		defines = []
		defines = defines + item['public-defines']

		if with_private == True:
			defines = defines + item['private-defines']

		for d in item['public-dependency']:
			defines = defines + self.collapse_defines( project_stack, project_stack[d], False)

		if with_private == True:
			for d in item['private-dependency']:
				defines = defines + self.collapse_defines( project_stack, project_stack[d], False)

		defines = list(set(defines + item['global-defines']))
		defines.sort()
		return defines

	def collapse_libs(self, project_stack, item):
		local_links = []
		external_links = []

		external_links = external_links + item['links']

		for d in item['public-dependency']:
			proj_obj = project_stack[d]
			if not proj_obj['kind'] in ["view","exe"]:
				local_links.append(d)

			(lc,ex) = self.collapse_libs( project_stack, proj_obj)
			local_links = local_links + lc
			external_links = external_links + ex

		for d in item['private-dependency']:
			proj_obj = project_stack[d]
			if not proj_obj['kind'] in ["view","exe"]:
				local_links.append(d)

			(lc,ex) = self.collapse_libs( project_stack, proj_obj)
			local_links = local_links + lc
			external_links = external_links + ex

		return (local_links,external_links)

