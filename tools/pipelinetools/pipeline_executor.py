
import os
import sys
import hashlib

import package_graph
import package_config
import package_constructor
import package_utils

import pipeline_utils

import hashlib


_citalic = package_utils.Colors.ITALIC
_cbold = package_utils.Colors.BOLD
_cend = package_utils.Colors.END
_cwhite = package_utils.Colors.LIGHT_WHITE
_cred = package_utils.Colors.RED
_clightblue = package_utils.Colors.LIGHT_BLUE
_cbrown = package_utils.Colors.BROWN
_cyellow = package_utils.Colors.YELLOW
_cgreen = package_utils.Colors.GREEN

#--------------------------------------------------------------------------------------------------------------------------------

class PipelineModule(package_graph.Module):
	def __init__(self, modkey, modpath, graph):
		package_graph.Module.__init__(self, modkey, modpath, graph)

		self.exec_count = 0

		self.content = None

#--------------------------------------------------------------------------------------------------------------------------------

class PipelineConstructor(package_constructor.PackageConstructor):
	def __init__(self, graph, target_module):
		package_constructor.PackageConstructor.__init__(self, graph, target_module)
		self.builder_names = []

	def builder(self, name, func):
		self._graph.add_builder(self._module, name, func)

		self.builder_names.append(name)

	def run(self, build_name, **kwargs):
		return self._graph.run_builder(build_name)

	def serialize(self, data):
		package_constructor.PackageConstructor.serialize(self,data)
		data['builders'] = sorted(self.builder_names)

	def _get_exec_file(self, path_to_file):
		script = None

		if isinstance(path_to_file, str):
			script = self.file(path_to_file)
		elif isinstance(path_to_file, package_utils.FileEntry):
			script = path_to_file
			self._paths[path_to_file.path] = path_to_file
			self._files.append(path_to_file.path)
		else:
			raise Exception("Invalid script...")

		return script

	def _run_command_sync(self, cmd):
		joined_cmd = " ".join(cmd)
		hcmd = hashlib.sha256(joined_cmd.encode("utf-8") ).hexdigest()
		self.assign(hcmd, cmd)

		import subprocess
		result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		self.assign(hcmd + "-returncode", result.returncode)
		
		log = f"CMD:\n{joined_cmd}"
		log = log + "\nSTDOUT:\n" + result.stdout.decode("utf-8")
		log = log + "\nSTDERR:\n" + result.stderr.decode("utf-8")
		logloc = self._graph.push_log_file(hcmd, log)
		if(result.returncode != 0):
			raise Exception("exec_shell_sync failed, check " + logloc)

	def exec_shell_sync(self, script_info, args = []):
		script = self._get_exec_file(script_info)
		cmd = ["/bin/bash", script.path] + args
		self._run_command_sync(cmd)

	def exec_binary_sync(self, executable_info, args = []):
		exe = self._get_exec_file(executable_info)
		cmd = [exe.path] + args
		self._run_command_sync(cmd)


#--------------------------------------------------------------------------------------------------------------------------------

class PipelineBuilder():
	def __init__(self, name, module, func):
		self.name = name
		self.module = module
		self.func = func

	def get_full_name(self):
		return self.module.get_name() + "." + self.name

#--------------------------------------------------------------------------------------------------------------------------------

class Solution(package_graph.ModuleGraph):
	def __init__(self, reconfigure):
		package_graph.ModuleGraph.__init__(self)

		self.builders = {}
		self.hashes = None
		self.hachcache = {}

		self.reconfigure = reconfigure

		self.pipeline_dirname = None
		self.output = None
		self.logsdir = None

	def add_builder(self, module, name, func):
		check = self.builders.get(name, None)
		if check != None:
			raise Exception(f"Builder {name} already exists:" + check.get_full_name())

		self.builders[name] = PipelineBuilder(name, module, func)

	def run_builder(self, builder):
		builder = self.builders.get(build_name, None)
		if builder == None:
			raise Exception(f"No builder found with name {builder_name}")

		return builder.name();

	def create_configurator(self):
		cfg = package_graph.ModuleGraph.create_configurator(self)

		#cfg.option("platform",self.platform,["win32"])
		cfg.option("nocache",False,[True, False])

		return cfg

	def create_module(self, modkey, modpath):
		return PipelineModule(modkey, modpath, self)

	def create_constructor(self, target_module):
		return PipelineConstructor(self, target_module)

	def get_next_modules(self, modkey, module):
		parents = self.backward_links.get(modkey, None)
		if parents == None:
			return []

		result = []
		for p in parents:
			m = self.modules[p]
			m.exec_count = m.exec_count + 1
			if m.exec_count == len(m.links):
				result.append(p)

		return result

	def push_log_file(self, filename, content):
		f = open(os.path.join(self.logsdir, filename), "w")
		f.write(content)
		f.close()

		return os.path.join(self.pipeline_dirname, filename)

	def get_file_hash(self, absfile):
		h = self.hachcache.get(absfile, None)
		if h != None:
			return h

		hc = pipeline_utils.sha256sum(absfile)
		self.hachcache[absfile] = hc
		return hc


	def check_for_changes(self, module, data):

		modinfo = data.get('module', None)			

		if (module == None):
			return [f"{_cred}'module' seems to be missing ...{_cend}"]

		if module.sha != modinfo.get('sha',None):
			return f" {_cwhite}Pipeline changed ...{_cend}"

		content = data.get('content',None)
		if (content == None):
			return [f"{_cred}'content' seems to be missing ...{_cend}"]

		props = content.get('props',None)
		if props != None:
			ncp = props.get('nocache',None)
			if ncp != None:
				if ncp['data'] == True:
					return f"{_cwhite} Always builds ...{_cend}"

		files = content.get('files',None)
		folders = content.get('folders',None)

		if files == None:
			return [f"{_cred}'files' are be missing ...{_cend}"]
		if folders == None:
			return [f"{_cred}'folders' are be missing ...{_cend}"]

		r = []

		for k, _ in files.items():
			if(not os.path.exists(k)):
				r.append(f"{_citalic}File {k} no longer exists.{_cend}")
				continue
			hc = self.get_file_hash(k)
			if hc != self.hashes.get(k,None):
				r.append(f"{_citalic}File {k} has changed.{_cend}")

		for k, _ in folders.items():
			if(not os.path.exists(k)):
				r.append(f"{_citalic}Folder {k} no longer exists.{_cend}")
				continue

		return r		

	def execute_module_constructor(self,metaout, mk, m):
		desc_path = os.path.join(metaout,m.get_name() + ".json")

		reason = None

		display_name = f"{_clightblue}[{_cyellow}" + m.get_name() + f"{_clightblue}]{_cend}"

		while True:
			if (not os.path.exists(desc_path)):
				reason = f"{_cbrown} + {desc_path} does not exist.{_cend}"
				break;
			
			data = pipeline_utils.read_json(desc_path)
			if (data == None):
				reason = f"{_cbrown} + {desc_path} could not be opened.{_cend}"
				break

			changes = self.check_for_changes(m, data)
			if isinstance(changes, str):
				reason = changes
				break
			elif isinstance(changes, list) and changes:
				reason = f"{_cbrown} * detected changes:{_cend}"
				for c in changes:
					reason = reason + "\n\t" + c
				break

			print(display_name + f"{_cgreen} Nothing to do.{_cend}")

			m.content = self.create_constructor(m)
			m.content.deserialize(data)

			break

		if(reason != None):
			print(display_name + reason)

			m.content = self.create_constructor(m)
			m.content.config("nocache")
			construct_proc = m.get_proc("construct")
			if construct_proc == None:
				raise Exception(f"Could not find 'construct' function in {m.get_name()}")
			construct_proc(m.content)

			#save json
			j = {}
			m.serialize(j)
			m.content.serialize(j)
			package_utils.save_json(j, desc_path)

			files = j['content']['files']
			for k, v in files.items():
				self.get_file_hash(k)

	def execute(self, path):
		cfg, root_modules = self.configure([path])

		root_module = root_modules[0]

		self.pipeline_dirname = os.path.join("pipeline",root_module.get_name().replace(".","_").replace("-","_").lower())
		self.output = os.path.join(root_module.get_package_dir(), self.pipeline_dirname)
		self.output = os.path.abspath(self.output)
		self.logsdir = os.path.join(self.output, "logs")

		metaout = os.path.join(self.output, "modules")
		if not os.path.exists(metaout):
			os.makedirs(metaout)
		if not os.path.exists(self.logsdir):
			os.makedirs(self.logsdir)

		hashes_file = os.path.join(self.output, "hashes.json")
		self.hashes = pipeline_utils.read_json(hashes_file)
		if self.hashes == None:
			self.hashes = {}

		self.sync_config(os.path.join(self.output, "config.ini"), self.reconfigure)

		self.forward_disable(root_modules)

		modstack = self.leafs.copy()

		package_utils.display_status("RUNNING PIPELINES...")

		while len(modstack) != 0:
			mk = modstack.pop()
			m = self.modules[mk]

			self.execute_module_constructor(metaout, mk, m)

			modstack.extend(self.get_next_modules(mk, m))

		self.hashes.update(self.hachcache)
		package_utils.save_json(self.hashes, hashes_file)
		


def run_pipeline(path, reconfigure):
	path = os.path.abspath(path)

	mg = Solution(reconfigure)
	mg.execute(path)
