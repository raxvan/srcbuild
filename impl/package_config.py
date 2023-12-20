
import os
import hashlib

import package_utils

#--------------------------------------------------------------------------------------------------------------------------------

class UserOption(package_utils.PackageEntry):
	def __init__(self, tags):
		package_utils.PackageEntry.__init__(self, tags)
		self.accepts = None
		self.defaults = None

	def add_accepted_values(self, pv):
		if self.accepts == None:
			self.accepts = set(pv)
		else:
			self.accepts = self.accepts.intersection(set(pv))

	def add_default_value(self, dv):
		if self.defaults == None:
			self.defaults = set()

		self.defaults.add(dv)

	def get_value(self):
		if self.defaults == None:
			if self.accepts != None:
				return self.accepts[0]
			return None

		if self.accepts != None:
			for d in self.defaults:
				if d in self.accepts:
					return d

			for s in self.accepts:
				return s
		else:
			for s in self.defaults:
				return s

		return None

	def allow_value(self, value):
		if self.accepts == None:
			return True

		if value in self.accepts:
			return True

		return False

	def try_set(self, value):
		if self.accepts != None:
			if not value in self.accepts:
				return False

		self.defaults = set(value)

		return True

#--------------------------------------------------------------------------------------------------------------------------------

class UserComponent(package_utils.PackageEntry):
	def __init__(self, tags):
		package_utils.PackageEntry.__init__(self, tags)
		self.enabled = None

	def update(self, value):
		if value != None and self.enabled == None:
			self.enabled = value

#--------------------------------------------------------------------------------------------------------------------------------

class Configurator():
	def __init__(self, solver, graph):
		self.active_module = None
		self.depth = 0

		self.solver = solver
		self.graph = graph

		self._components = {}
		self._options = {}
		
	def _configure_module_recursive(self, module):
		current_link = self.active_module
		self.active_module = module
		self.depth = self.depth + 1
		
		print("-" * self.depth  + ">" + module.get_name())
		
		cfg_func = module.get_proc("configure")
		if cfg_func != None:
			cfg_func(self)

		module.configured = True
		self.active_module = current_link
		self.depth = self.depth - 1

	def _safe_modkey(self, abs_dep_path):
		modkey = package_utils._path_to_modkey(abs_dep_path)

		if (modkey == self.active_module.key):
			#depends on itself ?
			raise Exception("Recursive link.")

		return modkey

	def query_option_value(self, name):
		v = self._options.get(name)
		if v == None:
			raise Exception(f"Could not find option {name}")
		return v.get_value()

	#api
	def enable(self):
		self.active_module.enabled = True

	def disable(self):
		self.active_module.enabled = False

	def tag(self, tags):
		self.active_module.tag(tags)

	def link(self, child_info):
		# links child to current module (parent)
		tags, path = package_utils._parse_key(child_info)
		abs_module_path = self.solver.resolve_module_or_die(self.active_module, path, tags)
		modkey = self._safe_modkey(abs_module_path)

		link = self.graph._create_link(self.active_module, modkey, abs_module_path, tags)
		if link.module.configured == False:
			self._configure_module_recursive(link.module)
		return link

	def trylink(self, child_info):
		# links child to current module (parent) if:
		#	1 module exists
		#	2 module is enabled
		
		tags, path = package_utils._parse_key(child_info)
		abs_module_path = self.solver.try_resolve_module(self.active_module, path, tags)
		if abs_module_path == None:
			return None
		if not os.path.exists(abs_module_path):
			return None

		modkey = self._safe_modkey(abs_module_path)
		link = self.graph._create_link(self.active_module, modkey, abs_module_path, tags)
		if link.module.configured == False:
			self._configure_module_recursive(link.module)
		return link

	def option(self, k, default_value, possible_values = None):
		tags, kv = package_utils._parse_key(k)
		o = self._options.get(kv,None)

		if o == None:
			o = UserOption(tags)
			self._options[kv] = o
		elif tags != None:
			o.tag(tags)

		if possible_values != None:
			o.add_accepted_values(possible_values)

		if default_value != None:
			o.add_default_value(default_value)

		return o

	def component(self, name, default_bool_value = None):
		tags, value = package_utils._parse_key(name)
		c = self._components.get(value,None)

		if c == None:
			c = UserComponent(tags)
			self._components[value] = c
		elif tags != None:
			c.tag(tags)

		if not (default_bool_value == None or default_bool_value == False or default_bool_value == True):
			raise Exception("Expeting bool or None, got " + str(name) + ".")

		c.update(default_bool_value)

		return c

	def _get_config_ini(self, graph):
		r = ""

		if graph != None:
			r = r + "[MODULES]\n"
			for m in graph.get_modules():
				mname = m.get_name()
				if m.enabled == True:
					r = r + f"{mname} = 1\n"
				else:
					r = r + f"{mname} = 0\n"

		r = r + "[COMPONENTS]\n"
		for cname, cvalue in self._components.items():
			if cvalue.enabled == None:
				r = r + f"#{cname} = *\n"
			elif cvalue.enabled == True:
				r = r + f"{cname} = 1\n"
			else:
				r = r + f"{cname} = 0\n"

		r = r + "[OPTIONS]\n"
		for oname, ovalue in self._options.items():
			c = ovalue.get_value()
			r = r + f"{oname} = {c}\n"

			if ovalue.accepts != None:
				index = 0
				for acc in ovalue.accepts:
					r = r + f"\t#{index}:{acc}\n"
					index = index + 1

		r = r + "#end.\n"

		return r

	def _save_config_ini(self, graph, abs_path_to_ini, headers):

		f = open(abs_path_to_ini, "w")
		if f == None:
			raise Exception(f"Failed create file {abs_path_to_ini}")
		if headers != None:
			f.write("\n".join(["#" + h for h in headers]))
			f.write("\n")
		f.write(self._get_config_ini(graph))
		f.close()

	def _sync_config(self, graph, abs_path_to_ini_file, override):
		print("CONFIG: " + abs_path_to_ini_file)
		if override:
			self._save_config_ini(graph, abs_path_to_ini_file, ["Regenerated by user."])
			return None

		user_modules = {}
		user_components = {}
		user_options = {}
		if _load_ini_map(abs_path_to_ini_file, user_modules, user_components, user_options) == False:
			self._save_config_ini(graph, abs_path_to_ini_file, ["Regenerated because original file failed to open."])
			return None

		override_headers = []

		for c,v in self._components.items():
			uc = user_components.get(c, None)
			if uc != None:
				if uc != v.enabled:
					v.enabled = uc
			else:
				override_headers.append(f"Component {c} was not found." )

		for c,v in self._options.items():
			uc = user_options.get(c, None)
			if uc != None:
				if uc != v.get_value():
					v.try_set(uc)
			else:
				override_headers.append(f"Option {c} was not found." )

		if override_headers:
			self._save_config_ini(graph, abs_path_to_ini_file, ["Warnings:"] + override_headers )

		return user_modules

def _parse_bool_value(sv):
	if sv in ["true", "on", "yes", "1"]:
		return True
	if sv in ["false", "off", "no", "0"]:
		return False

	raise Exception("Invalid bool `" + str(sv) + "`")

def _load_ini_map(abs_path_to_ini, modules, components, options):
	if not os.path.exists(abs_path_to_ini):
		return False

	import configparser
	config = configparser.ConfigParser(allow_no_value=True)
	config.optionxform=str #preserve case for keys

	f = open(abs_path_to_ini, "r")
	if f == None:
		raise Exception(f"Failed to open file {abs_path_to_ini}")

	config.read_string(f.read())
	f.close()

	for section in config:

		section_obj = config[section]
		for key in section_obj:
			kn = str(key).strip()
			sv = str(section_obj[key]).strip()
			if section == "MODULES":
				modules[kn] = _parse_bool_value(sv.lower())
			elif section == "OPTIONS":
				options[kn] = sv
			elif section == "COMPONENTS":
				components[kn] = _parse_bool_value(sv.lower())

	return True
