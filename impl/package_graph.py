
import os
import hashlib
import json
import importlib.util

import package_utils
import package_config
import package_constructor
import package_locator

def _load_module(abs_path_to_pyfile, load_location):
	ll = "modpak.sha." + load_location
	spec = importlib.util.spec_from_file_location(ll, abs_path_to_pyfile)
	module_context = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module_context)

	#source hash
	sh = hashlib.sha256(spec.loader.get_data(abs_path_to_pyfile)).hexdigest()

	return (module_context, sh)

#--------------------------------------------------------------------------------------------------------------------------------

class Module(package_utils.PackageEntry):
	def __init__(self, modkey, abs_pipeline_path, graph):
		package_utils.PackageEntry.__init__(self)

		p,s = _load_module(abs_pipeline_path, modkey)

		self.graph = graph
		self.pipeline = p

		self.key = modkey #search key
		self.sha = s #content sha

		self.rawtype = None

		self._abs_pipeline_path = abs_pipeline_path
		self._abs_pipeline_dir, self._pipeline_filename = os.path.split(abs_pipeline_path)

		self._name = self._pipeline_filename.replace(".pak.py","")
		self._simplified_name = self._name #self._name.replace(".","_").replace("-","_").lower()

		self.links = {} #key==modkey, value==ModuleLink
		#^ children

		self.enabled = True
		self.configured = False #set to true when package is configured

	def _create_child_link(self, modkey, tags, abs_dep_path):
		if modkey in self.links:
			raise Exception(f"Dependency to {abs_dep_path} already exists.")

		dep = package_utils.ModuleLink(abs_dep_path, tags)
		self.links[modkey] = dep
		
		return dep

	def serialize(self):
		modinfo = {}
		modinfo["name"] = self.get_name()

		modinfo["enabled"] = self.enabled
		modinfo["configured"] = self.configured
		modinfo["key"] = self.key
		modinfo["module-sha"] = self.sha
		modinfo["tags"] = list(self.tags)

		links = {}
		for lk,ld in self.links.items():
			links[lk] = {
				"path" : ld.path,
				"tags" : list(ld.tags),
			}
		modinfo["links"] = links

		return modinfo

	def get_name(self):
		return self._name
		
	def get_simplified_name(self):
		return self._simplified_name

	def get_package_relative_path(self, rpath):
		return os.path.relpath(self._abs_pipeline_path, rpath)

	def get_package_absolute_path(self):
		return self._abs_pipeline_path

	def get_package_filename(self):
		return self._pipeline_filename

	def get_package_dir(self):
		return self._abs_pipeline_dir

	def get_proc(self, procname):
		try:
			return getattr(self.pipeline, procname)
		except AttributeError:
			return None
		except:
			raise

	def get_type(self):
		return self.rawtype

	def set_type(self, type_value):
		self.rawtype = type_value

	def set_tags(self, tags):
		self.join_tags(tags)

	def print_info(self, print_key, print_sha, print_path):
		m = "- "
		m = m + str(self._name).ljust(16)
		if print_key == True:
			m = m + " key:" + self.key
		if print_sha == True:
			m = m + " sha:" + self.sha
		if print_path == True:
			m = m + " path:" + self._abs_pipeline_path

		print(m)


	def print_links_recursive(self, pidx, depth):
		h = None
		if pidx != None:
			h = str(pidx) + ":"
		else:
			h = ">"

		m = "\t" * depth + h + str(self._name)

		if self.links:
			m = m + " [" + str(len(self.links.items())) + "] ->\n"
			index = 0
			for l,lm in self.links.items():
				mod = self.graph.modules.get(l, None)
				if mod == None:
					m = m + "\t" * depth + str(index) + ":" + l + lm.get_tags_str(" ") +  "\n"
				else:
					m = m + mod.print_links_recursive(index, depth + 1)
				index = index + 1
		else:
			m = m + " [0]\n"

		return m

	def print_links(self):
		m = self.print_links_recursive(None, 0)
		print(m)

	def print_links_shallow(self):
		m = str(self._name)
		if self.links:
			m = m + " [" + str(len(self.links.items())) + "] ->\n"
			index = 0
			for l,lm in self.links.items():
				mod = self.graph.modules.get(l, None)
				if mod == None:
					m = m + "\t" + str(index) + ":" + l + lm.get_tags_str(" ") +  "\n"
				else:
					m = m + "\t" + str(index) + ":" + mod.get_name() + lm.get_tags_str(" ") + "\n"
				index = index + 1
		else:
			m = m + " [0] *"

		print (m)

	def dump_dependency_tree(self, out):
		this_links = {}
		if self.links:
			for l,lm in self.links.items():
				mod = self.graph.modules.get(l, None)
				mod.dump_dependency_tree(this_links)

		out[self.key] = this_links

#--------------------------------------------------------------------------------------------------------------------------------

class GraphIterator():
	def __init__(self, counters, links, stack):
		self.stack = stack
		self.counters = counters
		self.links = links

	def begin(self):

		if self.stack:
			r = self.stack.pop()
			return r
		return None

	def end(self, r):
		parent_lins = self.links.get(r, None)
		if  parent_lins == None:
			return

		for link in parent_lins:
			c = self.counters[link]
			c -= 1
			if c == 0:
				self.stack.append(link)
			else:
				self.counters[link] = c


#--------------------------------------------------------------------------------------------------------------------------------

class ModuleGraph():
	def __init__(self):
		self.modules = {} #modkey/Module
		self.names = {} #module.get_name()/Module

		self.forward_links = {} #modkey:parent -> modkey:children []
		self.backward_links = {} #modkey:child -> modkey:parents []

		self.roots = None #modkey, modules with 0 parents
		self.leafs = None #modkey, modules with 0 children

		self.configurator = None
		self.locator = None

		self.printer = package_utils.DefaultPackagePrinter()

	def make_log_silent(self):
		r = package_utils.EmptyPackagePrinter()
		self.printer = r
		return r

	def make_log_lazy(self, output):
		r = package_utils.LoggingPackagePrinter(output)
		self.printer = r
		return r

	def make_log_custom(self, clog):
		self.printer = clog


	def _create_new_module(self, modkey, abs_module_path):
		module = self.create_and_validate_module(modkey, abs_module_path)
		self.modules[modkey] = module
		self.names[module.get_name()] = module
		return module

	def _create_link(self, parent_module, modkey, abs_module_path, tags):
		link = parent_module._create_child_link(modkey, tags, abs_module_path)

		chmod = self.modules.get(modkey, None)

		if chmod == None:
			chmod = self._create_new_module(modkey, abs_module_path)

		self.forward_links.setdefault(parent_module.key,[]).append(chmod.key)
		self.backward_links.setdefault(chmod.key,[]).append(parent_module.key)

		link.module = chmod

		return link

	def get_module_with_key(self, k):
		return self.modules.get(k,None)

	def get_modules(self):
		return [v for _,v in self.modules.items()]

	def module_enabled(self, modname):
		module = self.names.get(modname,None)
		if module == None:
			return False
		return module.enabled

	def get_module(self, modname):
		return self.names.get(modname,None)

	#################################################################################################
	#overloadable

	def create_module(self, modkey, modpath):
		return Module(modkey, modpath, self)

	def create_locator(self, packages):
		return package_locator.ModuleLocator(packages)

	def create_configurator(self):
		return package_config.Configurator(self.locator, self)

	def create_constructor(self, target_module):
		return package_constructor.PackageConstructor(self, target_module)


	def create_and_validate_module(self, modkey, abspath):
		if not os.path.exists(abspath):
			raise Exception(f"Module `{abspath}` not found!")

		if not os.path.isfile(abspath):
			raise Exception(f"Path `{abspath}` is not a file!")

		m = self.create_module(modkey, abspath)

		#if not hasattr(m.pipeline, 'configure'):
		#	raise Exception(f"Module `{abspath}` is missing configure function!")

		return m


	#################################################################################################
	#utils:
	def build(self, root_modules_list):

		prp = self.printer

		prp.print_header("RUNNING FORWARD DISABLE...")

		while root_modules_list:

			next_root_modules_list = []
			for current_module in root_modules_list:
				children_list = self.forward_links.get(current_module.key,None)
				if children_list == None:
					continue

				for child in children_list:
					child_module = self.modules[child]
					next_root_modules_list.append(child_module)

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
							prp.print_progress("\t-" + child_module.get_name())

			root_modules_list = next_root_modules_list

		prp.print_header("GENERATING ITERATOR...")

		counters = {}
		links = {}
		stack = []

		for mk, m in self.modules.items():
			if m.enabled == False:
				prp.print_progress(f"> {m.get_name()}".ljust(32) + " -> SKIPPING: not enabled!")
				continue
			
			child_count = 0

			children_list = self.forward_links.get(mk,None)
			if children_list != None:
				for c in children_list:
					child_module = self.modules[c]
					if child_module.enabled == False:
						continue
					
					links.setdefault(c,[]).append(mk)
					child_count += 1

			if child_count == 0:
				stack.append(mk)
			else:
				counters[mk] = child_count

			prp.print_progress(f"> {m.get_name()}".ljust(32) + f" -> OK: order={child_count}")

		return GraphIterator(counters, links, stack)


	def sync_config(self, abs_path_to_config_ini, override_config):
		user_modules = self.configurator._sync_config(self, abs_path_to_config_ini, override_config)
		if user_modules != None:
			for _,m in self.modules.items():
				me = user_modules.get(m.get_name(), None)
				if me != None:
					m.enabled = me

	def print_info(self, print_key, print_sha, print_path):

		for _,m in self.modules.items():
			m.print_info(print_key, print_sha, print_path)

		#print("roots: " + str(self.roots))
		#print("leafs: " + str(self.leafs))

	def print_links_shallow(self):
		for _,m in self.modules.items():
			m.print_links_shallow()
	def print_links(self):
		for _,m in self.modules.items():
			m.print_links()


	def configure(self, entrypoints):
		packages = None

		for e in entrypoints:
			packages_path = package_locator.find_packages_json(os.path.abspath(e))
			if packages_path == None:
				continue

			self.printer.print_key_value("Config", packages_path)

			f = open(packages_path)
			packages = json.load(f)
			f.close()
			break
		
		if self.locator == None:
			self.locator = self.create_locator(packages)

		if self.configurator == None:
			self.configurator = self.create_configurator()


		self.printer.print_header("CONFIGURING...")

		result = []

		for e in entrypoints:
			modpath = os.path.abspath(e)
			modkey = package_utils._path_to_modkey(modpath)
			chmod = self._create_new_module(modkey, modpath)
			result.append(chmod)

			self.configurator._configure_module_recursive(chmod)

		self.link_graph()

		return result

	def link_graph(self):

		self.roots = []
		self.leafs = []
		for k, m in self.modules.items():
			if not k in self.backward_links:
				self.roots.append(k)

			if bool(m.links) == False:
				#no children
				self.leafs.append(k)

	
