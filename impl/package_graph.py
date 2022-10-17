
import os
import hashlib
import json
import importlib.util

import package_utils
import package_config
import package_constructor

def _load_module(abs_path_to_pyfile, load_location):
	ll = "modpak.sha." + load_location
	spec = importlib.util.spec_from_file_location(ll, abs_path_to_pyfile)
	module_context = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module_context)

	#source hash	
	sh = hashlib.sha256(spec.loader.get_data(abs_path_to_pyfile)).hexdigest()

	return (module_context, sh)

#--------------------------------------------------------------------------------------------------------------------------------

class ModuleLocator():
	def __init__(self):
		pass

	def resolve_path(self, current_module, path, tags):
		if tags != None and "abspath" in tags:
			return path

		return os.path.abspath(os.path.join(current_module._abs_pipeline_dir, path))

	def try_resolve_path(self, current_module, path, tags):
		if tags != None and "abspath" in tags:
			if os.path.exists(path):
				return path

		path = os.path.abspath(os.path.join(current_module._abs_pipeline_dir, path))
		if os.path.exists(path):
			return path

		return None

	def resolve_abspath_or_die(self, current_module, path, tags):
		p = self.resolve_path(current_module, path, tags)
		if p == None or os.path.exists(p) == False:
			modpath = current_module._abs_pipeline_path
			raise Exception(f"Could not find path {path} in module {modpath}")

		return p

#--------------------------------------------------------------------------------------------------------------------------------

class Module(package_utils.PackageEntry):
	def __init__(self, modkey, abs_pipeline_path, graph):
		package_utils.PackageEntry.__init__(self)

		p,s = _load_module(abs_pipeline_path, modkey)

		self.graph = graph
		self.pipeline = p

		self.sha = s #content sha
		self.key = modkey #search key

		self._abs_pipeline_path = abs_pipeline_path
		self._abs_pipeline_dir, self._pipeline_filename = os.path.split(abs_pipeline_path)

		self._name = self._pipeline_filename.replace(".pak.py","")

		self.links = {} #key==modkey, value==ModuleLink
		#^ children

		self.enabled = True
		self.configured = False

	def _create_child_link(self, modkey, tags, abs_dep_path):
		if modkey in self.links:
			raise Exception(f"Dependency to {abs_dep_path} already exists.")

		dep = package_utils.ModuleLink(abs_dep_path, tags)
		self.links[modkey] = dep
		
		return dep

	#def _module_enabled(self, modkey):
	#	cm = self.graph.modules.get(modkey, None)
	#	if cm == None:
	#		return False
    #
	#	if cm.enabled == False:
	#		return False
    #
	#	return True
    #
	#def _module_tags(self, modkey):
	#	cm = self.graph.modules.get(modkey, None)
	#	if cm == None:
	#		return set()
    #
	#	return cm.tags

	def serialize(self, out):
		out["name"] = self.get_name()

		out["enabled"] = self.enabled
		out["configured"] = self.configured
		out["key"] = self.key
		out["sha"] = self.sha

		links = {}
		for lk,ld in self.links.items():
			links[lk] = {
				"path" : ld.path,
				"tags" : list(ld.tags),
			}
		out["links"] = links



	def get_name(self):
		return self._name

	def get_proc(self, procname):
		try:
			return getattr(self.pipeline, procname)
		except AttributeError:
			return None
		except:
			raise

	def get_package_dir(self):
		return self._abs_pipeline_dir

	def print_info(self, print_key, print_sha, print_path, print_links):
		m = "- "
		m = m + str(self._name).ljust(16)
		if print_key == True:
			m = m + " key:" + self.key
		if print_sha == True:
			m = m + " sha:" + self.sha
		if print_path == True:
			m = m + " path:" + self._abs_pipeline_path

		if print_links == True:
			m = m + " links:\n"
			for l,lm in self.links.items():
				mod = self.graph.modules.get(l, None)
				if mod == None:
					m = m + "\t" + l + lm.get_tags_str(" ") +  "\n"
				else:
					m = m + "\t" + mod.get_name() + lm.get_tags_str(" ") + "\n"

		print(m)

#--------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------

class ModuleGraph():
	def __init__(self):
		self.modules = {} #modkey/Module
		self.path_map = {} #abs_path/modkey

		self.age = 0

		self.forward_links = {} #modkey:parent -> modkey:children []
		self.backward_links = {} #modkey:child -> modkey:parents []

		self.roots = None #modkey, modules with 0 parents
		self.leafs = None #modkey, modules with 0 children

		self.configurator = None
		self.locator = None

	def _create_link(self, parent_module, modkey, abs_module_path, tags):
		link = parent_module._create_child_link(modkey, tags, abs_module_path)

		chmod = self.modules.get(modkey, None)

		if chmod == None:
			chmod = self.create_and_validate_module(modkey, abs_module_path)
			self.modules[modkey] = chmod
			self.path_map[abs_module_path] = modkey

		self.forward_links.setdefault(parent_module.key,[]).append(chmod.key)
		self.backward_links.setdefault(chmod.key,[]).append(parent_module.key)

		link.module = chmod

		return link		

	def get_module_with_path(self, p):
		p = os.path.abspath(p)

		mk = self.path_map.get(p,None)
		if mk == None:
			raise Exception(f"No module with path: {p}")

		return self.modules[mk]

	def get_module_with_key(self, k):
		return self.modules.get(k,None)

	def get_modules(self):
		return [v for _,v in self.modules.items()]

	#################################################################################################
	#overloadable

	def create_module(self, modkey, modpath):
		return Module(modkey, modpath, self)

	def create_locator(self):
		return ModuleLocator()

	def create_configurator(self):
		return package_config.Configurator(self.locator, self)

	def create_constructor(self, target_module, config):
		return package_constructor.PackageConstructor(self.locator, target_module, config)


	def create_and_validate_module(self, modkey, modpath):
		if not os.path.exists(modpath):
			raise Exception(f"Module `{modpath}` not found!")

		m = self.create_module(modkey, modpath)

		#if not hasattr(m.pipeline, 'configure'):
		#	raise Exception(f"Module `{modpath}` is missing configure function!")

		return m


	#################################################################################################
	#utils:

	def forward_disable(self, modules_list):
		
		print("FORWARD DISABLE:")

		while modules_list:

			next_modules_list = []
			for current_module in modules_list:
				children_list = self.forward_links.get(current_module.key,None)
				if children_list == None:
					continue

				for child in children_list:
					child_module = self.modules[child]
					next_modules_list.append(child_module)

					if(child_module.enabled == True):
						all_parents = self.backward_links[child]
						disable = True
						for parent in all_parents:
							parent_module = self.modules[parent]
							if parent_module.enabled:
								disable = False
								break

						if disable == True:
							child_module.enabled = False
							print("\t-" + child_module.get_name())

			modules_list = next_modules_list
						
	def sync_config(self, abs_path_to_config_ini, override):
		user_modules = self.configurator._sync_config(self, abs_path_to_config_ini, override)
		if user_modules != None:
			for _,m in self.modules.items():
				me = user_modules.get(m.get_name(), None)
				if me != None:
					m.enabled = me



	def print_info(self, print_key, print_sha, print_path, print_links):

		for _,m in self.modules.items():
			m.print_info(print_key, print_sha, print_path, print_links)

		print("roots: " + str(self.roots))
		print("leafs: " + str(self.leafs))

	def configure(self, entrypoints):
		
		if self.locator == None:
			self.locator = self.create_locator()

		if self.configurator == None:
			self.configurator = self.create_configurator()

		print("CONFIGURING...")

		result = []

		for e in entrypoints:
			modpath = os.path.abspath(e)
			modkey = package_utils._path_to_modkey(modpath)
			chmod = self.create_and_validate_module(modkey, modpath)
			self.modules[modkey] = chmod
			self.path_map[modpath] = modkey
			result.append(chmod)

		module_stack = result
		
		while len(module_stack) > 0:

			first_module = module_stack[0]
			remaning_modules = module_stack[1:]

			if first_module.configured:
				module_stack = remaning_modules
				continue

			print("\t"  + ":" + first_module.get_name())
			loaded_links = self.configurator._configure_module(first_module)
			
			module_stack = loaded_links + module_stack

		self.link_graph()

		return self.configurator, result

	def link_graph(self):

		self.roots = []
		self.leafs = []
		for k, m in self.modules.items():
			if not k in self.backward_links:
				self.roots.append(k)

			if bool(m.links) == False:
				#no children
				self.leafs.append(k)

	
