
import os
import sys
import hashlib

import package_graph
import package_config
import package_constructor
import package_utils

import pipeline_utils
import pipeline_constructor


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

class PipelineBuilder():
	def __init__(self, name, module, func):
		self.name = name
		self.module = module
		self.func = func

	def get_full_name(self):
		return self.module.get_name() + "." + self.name

class BuilderInstance():
	def __init__(self):
		self.builder_name = None
		self.instance_name = None
		self.data = None
		self.content = None
		self.future = None

	def get_content():
		return self.content

	def get_result(self):
		return self.future

#--------------------------------------------------------------------------------------------------------------------------------

class Solution(package_graph.ModuleGraph):
	def __init__(self, reconfigure):
		package_graph.ModuleGraph.__init__(self)

		self.builders = {}
		self.hashes = None
		self.hashcache = {}

		self.reconfigure = reconfigure

		self.internal_folder = None
		self.pipeline_dirname = None #short name for pipeline output
		self.output = None #output dir
		self.logsdir = None #log output dir
		self.modulesdir = None
		self.submodulesdir = None
		self.version = 0

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
		return pipeline_constructor.Pipeline(self, target_module)

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

	def set_dirty(self, absfile):
		self.hashcache[absfile] = "dirty"

	def get_file_hash(self, absfile):

		h = self.hashcache.get(absfile, None)
		if h != None:
			return h

		hc = pipeline_utils.sha256sum(absfile)
		self.hashcache[absfile] = hc
		return hc


	def check_for_changes_in_database(self, module, data):

		modinfo = data.get('module', None)

		if (modinfo == None):
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

	def check_changes_with_file(self, base_module, display_name, desc_path):

		display_name = f"{_clightblue}[{_cyellow}" + display_name + f"{_clightblue}]{_cend}"

		if (not os.path.exists(desc_path)):
			return None, display_name + f"{_cbrown} + {desc_path} does not exist.{_cend}"
		
		data = pipeline_utils.read_json(desc_path)
		if (data == None):
			return None, display_name + f"{_cbrown} + {desc_path} could not be opened.{_cend}"

		bver = data.get('version', None)
		if bver != self.version:
			bver = str(bver)
			return None, display_name + f"{_cyellow} + {desc_path} was built with an older version {bver}.{_cend}"

		changes = self.check_for_changes_in_database(base_module, data)
		if isinstance(changes, str):
			return None, display_name + changes
		elif isinstance(changes, list) and changes:
			reason = display_name + f"{_cbrown} * detected changes:{_cend}"
			for c in changes:
				reason = reason + "\n\t" + c
			return None, reason

		builders = data.get("builders", None)
		if builders != None:
			reason = None
			for b in builders:
				func = base_module.get_proc(b)
				if func == None:
					reason = f"{_cred} ! Builder {b} could not be found...{_cend}"
					break;
			if reason != None:
				return None, display_name + reason
			for b in builders:
				self.add_builder(base_module, b, base_module.get_proc(b))

		return data, display_name + f"{_cgreen} Nothing to do.{_cend}"

	def save_json(self, result, module, content, desc_path):
		j = {
			"version" : self.version,
			"result" : result,
		}
		module.serialize(j)
		content.serialize(j)
		package_utils.save_json(j, desc_path)

		files = j['content']['files']
		for k, v in files.items():
			self.get_file_hash(k)

	def execute_module_constructor(self, mk, m):
		desc_path = os.path.join(self.modulesdir, m.get_name() + ".json")

		content, message = self.check_changes_with_file(m, m.get_name(), desc_path)

		if content != None:
			print(message)

			m.content = self.create_constructor(m)
			m.content.deserialize(content)

		elif message != None:
			print(message)

			m.content = self.create_constructor(m)
			m.content.config("nocache")
			construct_proc = m.get_proc("construct")
			if construct_proc == None:
				raise Exception(f"Could not find 'construct' function in {m.get_name()}")
			result = construct_proc(m.content)

			#save json
			self.save_json(result, m, m.content, desc_path)

	def spawn_builder(self, basemodule, builder_name, data):
		
		builder = self.builders.get(builder_name, None)
		if (builder == None):
			raise Exception(f"Could not find builder '{builder_name}'")

		instance_name = f"{basemodule.get_simplified_name()}.{builder_name}.{pipeline_utils.kwargskey(data)}"
		desc_path = os.path.join(self.submodulesdir, instance_name + ".json")
		content, message = self.check_changes_with_file(builder.module, instance_name, desc_path)

		r = BuilderInstance()
		r.builder_name = builder_name;
		r.instance_name = instance_name
		r.data = data

		if content != None:
			print(message)
			r.content = self.create_constructor(builder.module)
			r.content.deserialize(content)
			r.future = content.get("result", None)

		elif message != None:
			print(message)

			r.content = self.create_constructor(basemodule)
			r.content.config("nocache")
			
			result = builder.func(r.content, **data)
			r.future = result

			self.save_json(result, builder.module, r.content, desc_path)

		return r

	def get_internal_folder(self, fpath):
		return os.path.join(self.internal_folder, fpath)

	def execute(self, path):
		cfg, root_modules = self.configure([path])

		root_module = root_modules[0]

		#self.internal_folder = "/home/wspace"
		self.internal_folder = root_module.get_package_dir()

		self.pipeline_dirname = os.path.join(".pipeline",root_module.get_simplified_name())
		self.output = os.path.join(self.internal_folder, self.pipeline_dirname)
		self.output = os.path.abspath(self.output)
		self.logsdir = os.path.join(self.output, "logs")

		self.modulesdir = os.path.join(self.output, "modules")
		self.submodulesdir = os.path.join(self.output, "submodules")

		if not os.path.exists(self.modulesdir):
			os.makedirs(self.modulesdir)
		if not os.path.exists(self.submodulesdir):
			os.makedirs(self.submodulesdir)
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

			self.execute_module_constructor(mk, m)

			modstack.extend(self.get_next_modules(mk, m))

		self.hashes.update(self.hashcache)
		for k,v in self.hashcache.items():
			if v == "dirty":
				self.hashes[k] = pipeline_utils.sha256sum(k)

		package_utils.save_json(self.hashes, hashes_file)

		#check if all modules are built
		error = []
		for k,v in self.modules.items():
			if m.enabled and m.exec_count != len(m.links):
				error.append(v.get_name())

		if error:
			msg = _cred + "ERROR: Detected modules that are not constructed:" + _cend
			for e in error:
				msg = msg + "\n\t" + _cbold + e + _cend
			msg = msg + _cred + "\n(´。＿。｀)" + _cend + "\n"
			print(msg)
		else:
			print(_cgreen + "\nDONE!" + _cwhite + " ☜(ﾟヮﾟ☜)\n" + _cend)


def run_pipeline(path, reconfigure):
	path = os.path.abspath(path)

	mg = Solution(reconfigure)
	mg.execute(path)

