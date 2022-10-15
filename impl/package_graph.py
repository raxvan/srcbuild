
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
		if "abspath" in tags:
			return path

		return os.path.abspath(os.path.join(current_module._abs_pipeline_dir, path))

	def try_resolve_path(self, current_module, path, tags):
		if "abspath" in tags:
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

class Module():
	def __init__(self, modkey, abs_pipeline_path, parent_graph):

		p,s = _load_module(abs_pipeline_path, modkey)
		
		self.graph = parent_graph
		self.pipeline = p

		self.sha = s #content sha
		self.key = modkey #search key

		self._abs_pipeline_path = abs_pipeline_path
		self._abs_pipeline_dir, self._pipeline_filename = os.path.split(abs_pipeline_path)

		self._name = self._pipeline_filename.replace(".pak.py","")

		self.links = {} #key==modkey, value==ModuleLink
		#^ children

		self.configured = False


		self._config_priority = 0
		if hasattr(self.pipeline, 'priority'):
			self._config_priority = self.pipeline.priority()

	def _link_child_module(self, modkey, tags, abs_dep_path):
		dep = self.links.get(modkey,None)

		if dep == None:
			dep = package_utils.ModuleLink(abs_dep_path, tags)
			self.links[modkey] = dep
			self.graph._link_modules(self.key, modkey)
		elif tags != None:
			dep.tag(tags)

		return dep

	def get_name(self):
		return self._name

	def run_proc(self, procname, *args):
		p = getattr(self.pipeline, procname)
		return p(*args)

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

		self.forward_links = {} #modkey:parent -> modkey:children
		self.backward_links = {} #modkey:child -> modkey:parents

		self.roots = None #modkey, modules with 0 parents
		self.leafs = None #modkey, modules with 0 children

		self.configurator = None
		self.locator = None

	def _link_modules(self, parent, child):
		self.forward_links.setdefault(parent,[]).append(child)
		self.backward_links.setdefault(child,[]).append(parent)

	def get_module_with_path(self, p):
		p = os.path.abspath(p)

		mk = self.path_map.get(p,None)
		if mk == None:
			raise Exception(f"No module with path: {p}")

		return self.modules[mk]

	def get_modules(self):
		return [v for _,v in self.modules.items()]

	#################################################################################################
	#overloadable

	def create_module(self, modkey, modpath):
		return Module(modkey, modpath, self)

	def create_locator(self):
		return ModuleLocator()

	def create_configurator(self):
		return package_config.Configurator(self.locator)

	def create_constructor(self, target_module, config):
		return package_constructor.PackageConstructor(self.locator, target_module, config)


	def create_and_validate_module(self, modkey, modpath):
		if not os.path.exists(modpath):
			raise Exception(f"Module `{modpath}` not found!")

		m = self.create_module(modkey, modpath)

		#if not hasattr(m.pipeline, 'configure'):
		#	raise Exception(f"Module `{modpath}` is missing configure function!")

		self.modules[modkey] = m
		self.path_map[modpath] = modkey

		return m


	#################################################################################################
	#utils:

	def print_info(self, print_key, print_sha, print_path, print_links):

		for _,m in self.modules.items():
			m.print_info(print_key, print_sha, print_path, print_links)

		print("roots: " + str(self.roots))
		print("leafs: " + str(self.leafs))

	def _load_single_module(self, name):
		modpath = os.path.abspath(name)
		modkey = package_utils._path_to_modkey(modpath)
		if modkey in self.modules:
			return None

		return self.create_and_validate_module(modkey, modpath)

	def load_shallow(self, entrypoint_paths):
		#returns modules list
		confgure_queue = []
		for e in entrypoint_paths:
			m = self._load_single_module(e);
			if m != None:
				confgure_queue.append(m)

		return confgure_queue

	def configure(self, confgure_queue = None):
		
		if confgure_queue == None:
			unconfigured_modules = [m for _,m in self.modules.items() if m.configured == False]
			return self.configure(unconfigured_modules)

		#load_queue is returned by load_shallow
		if len(confgure_queue) == 0:
			print("NOTHING TO LOAD...")
			return

		if self.locator == None:
			self.locator = self.create_locator()

		if self.configurator == None:
			self.configurator = self.create_configurator()

		print("CONFIGURING...")

		index = 0
		while len(confgure_queue) > 0:

			confgure_queue.sort(key=lambda m: m._config_priority)

			print("\t" + str(index) + ":" + ",".join([m.get_name() for m in confgure_queue]))
			index = index + 1

			########################################################################################
			#run module configuration
			self.configurator._group_begin()

			for m in confgure_queue:
				if m.configured == False:
					self.configurator._configure_module(m)

			next_items = self.configurator._group_end()

			########################################################################################
			#load the actual module and queue for scanning
			confgure_queue = []
			for srcmod, modkey, modpath in next_items:
				if modkey in self.modules:
					continue
				nextmod = self.create_and_validate_module(modkey, modpath)

				confgure_queue.append(nextmod)

		self.link_graph()

		return self.configurator

	def link_graph(self):

		self.roots = []
		self.leafs = []
		for k, m in self.modules.items():
			if not k in self.backward_links:
				self.roots.append(k)

			if bool(m.links) == False:
				#no children
				self.leafs.append(k)

	

	#def construct_all(self, config):
	#	result = []
	#	for _, m in self.modules.items():
	#		m.construct(config)
	#		result.append(m)
	#	return result

#--------------------------------------------------------------------------------------------------------------------------------

#def _parse_bool_value(sv):
#	if sv in ["true", "on", "yes", "1"]:
#		return True
#	if sv in ["false", "off", "no", "0"]:
#		return False
#
#	raise Exception("Invalid bool `" + str(sv) "`")
#	
#
#def _load_ini_map(abs_path_to_ini):
#	if not os.path.exists(abs_path_to_ini):
#		return {}, {}
#
#	import configparser
#	config = configparser.ConfigParser(allow_no_value=True)
#	config.optionxform=str #preserve case for keys
#	
#	f = open(abs_path_to_ini, "r")
#
#	config.read_string(f.read())
#	f.close()
#	
#	options = {}
#	components = {}
#	for section in config:
#		
#		section_obj = config[section]
#		for key in section_obj:
#			kn = str(key).strip()
#			sv = str(section_obj[key]).strip()
#			if section == "OPTIONS":
#				options[kn] = sv
#			elif section == "COMPONENTS":
#				components[kn] = _parse_bool_value(sv.lower())
#
#	return options, components
#
#
#class OptionsBuilder():
#	def __init__(self):
#		#selected
#		
#
#	def dirty(self):
#		return self._dirty
#
#
#
#	def build(self, ini_config_path):
#
#		options, components = _load_ini_map(ini_config_path)
#
#		f = open(ini_config_path, "w")
#		if f == None:
#			raise Exception("Failed to create config at `" + str(ini_config_path) "`.")
#
#		f.write("[COMPONENTS]\n")
#		components = self._process_components(f, components)
#		f.write("[OPTIONS]\n")
#		options = self._process_options(f, options)
#
#		f.close()
#
#
#	def _process_components(self, fout, user_config_components):
#
#		all_components = self._all_components
#
#		result = {}
#
#		for o in all_components:
#			ucv = user_config_components.get(o,None)
#
#			is_enabled = False
#			if ucv != None:
#				is_enabled = ucv
#			elif o in self._enabled_components:
#				is_enabled = True
#
#			result[o] = is_enabled
#
#			#write to config
#			if is_enabled == True:
#				fout.write(str(o) + " = 1\n")
#			else:
#				fout.write(str(o) + " = 0\n")
#
#		return result
#
#	def _process_options(self, fout, user_config_options):
#		
#		result = {}
#		for o in self._str_keys:
#			v = user_config_components.get(o,None)
#
#			restrictions = self._str_values.get(o, None)
#			defaults = self._str_defaults.get(o, None)
#
#			outv = None
#			if v != None:
#				#defined by user:
#				if restrictions != None:
#					if not v in restrictions:
#						raise Exception("Invalid option [" + k + "] with value `" + v + "`, expecting [" + ",".join(restrictions) + "].")
#				
#				outv = v
#
#		return result
#
#
#
#class ParsedOptions():
#	def __init__(self):
#		pass
#
#
		#kv = self._options.get(k, None)
		#if kv == None:
		#	raise Exception("Missing option value [" + k + "] with value `" + v + "`, expecting [" + ",".join(possible_values) + "].")
	    #
        #
		#return self._options[k]
		

	#def get_value_or_die(self, name):
	#	v = self._options.get(name, None)
	#	if v == None:
	#		raise Exception("Missing option `" + name + "`")
    #
	#	return v


	#def get(self, k, v = None):
    #
	#	#TODO: improve "options" functionality
	#	# this is a hack
    #
	#	rvalue = self._options.get(k, None)
    #
    #
	#	if v == None:
	#		self._bool_options.add(k)
	#	elif isinstance(v, list):
	#		if rvalue != None:
	#			if not rvalue in v:
	#				raise Exception("Incompatible value `" + rvalue + "`, expecting [" + ",".join(v) + "].")
    #
	#		self._str_values[k] = self._str_values.get(k, set()).union(set(v))
	#	elif isinstance(v, str):
	#		self._str_values.setdefault(k, set()).add(v)
    #
	#	if rvalue == None:
	#		#no assigned value, try to get a value
	#		possible_values = self._str_values.get(k,None)
	#		if possible_values != None:
	#			for v in possible_values:
	#				self._options[k] = v
	#				return v
    #
	#		if k in self._bool_options:
	#			#unless somone asigns a value to this, we consider that it is a bool option
	#			return ""
    #
	#	return rvalue

#	def add_ini_config(self, abs_path_to_ini):
#		import configparser
#		config = configparser.ConfigParser(allow_no_value=True)
#		config.optionxform=str #preserve case for keys
#		
#		f = open(abs_path_to_ini, "r")
#		config.read_string("[void]\n" + f.read())
#		f.close()
#		
#		result = []
#		for section in config:
#			section_obj = config[section]
#			for key in section_obj:
#				kn = str(key).strip()
#				sv = str(section_obj[key]).strip()
#
#				if sv == "":
#					self._bool_options.add(kn)
#				else:
#					self._options[kn] = sv
#
#	def save_ini_config(self, abs_path_to_ini):
#		fout = ""
#
#		all_options = sorted(set(
#			[k for k,v in self._options.items()] + 
#			[k for k,v in self._str_values.items()] +
#			list(self._bool_options)
#		))
#
#		for o in all_options:
#			v = self._options.get(o,None)
#
#			if v == None and o in self._bool_options:
#				fout = fout + "#" + o + "=\n"
#				fout = fout + "\t#BOOL\n"
#			elif v != None:
#				possible_values = self._str_values.get(o,None)
#				fout = fout + "" + o + "=" + str(v) + "\n"
#
#				if possible_values != None:
#					possible_values = sorted(possible_values)
#					fout = fout + "\t#options:" + ",".join(possible_values) + "\n"
#			else:
#				raise Exception("Internal error")
#
#		f = open(abs_path_to_ini, "w")
#		f.write(fout)
#		f.close()
#
#
#	def collect(self, out):
#		all_options = sorted(set(
#			[k for k,v in self._options.items()] + 
#			[k for k,v in self._str_values.items()] +
#			list(self._bool_options)
#		))
#
#		for o in all_options:
#			v = self._options.get(o,None)
#			if v == None and o in self._bool_options:
#				out[o] = "" #no value
#			elif v != None:
#				out[o] = v