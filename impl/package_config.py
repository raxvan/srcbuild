
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

	def accepts(self, value):
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


class UserComponent(package_utils.PackageEntry):
	def __init__(self, tags):
		package_utils.PackageEntry.__init__(self, tags)
		self.enabled = None

	def update(self, value):
		if value != None and self.enabled == None:
			self.enabled = value

#--------------------------------------------------------------------------------------------------------------------------------

class Configurator():
	def __init__(self, solver):

		self.current_module = None
		self.current_dependency = None

		self.solver = solver

		self._components = {}
		self._options = {}

	def _group_begin(self):
		self.current_dependency = []
		pass

	def _group_end(self):
		return self.current_dependency

	def _configure_module(self, module):
		self.current_module = module

		try:
			module.run_proc("configure",self)
		except:
			#AttributeError, in case it does not have configure confution, we carry on
			pass
		
		module.configured = True
		self.current_module = None
		
	def _link_path(self, abs_dep_path, tags):
		modkey = package_utils._path_to_modkey(abs_dep_path)

		if (modkey == self.current_module.key):
			#depends on itself ?
			return

		self.current_dependency.append((self.current_module, modkey, abs_dep_path))
		return self.current_module._link_child_module(modkey, tags, abs_dep_path);

	#api
	def enable(self):
		self.current_module.enabled = True

	def disable(self):
		self.current_module.enabled = False

	def link(self, child_info):
		# links child to current module (parent)
		tags, value = package_utils._parse_key(child_info)

		abs_dep_path = self.solver.resolve_abspath_or_die(self.current_module, value, tags)
		return self._link_path(abs_dep_path, tags)
		
	def optional_link(self, child_info):
		# links child to current module (parent) if module exists
		tags, value = package_utils._parse_key(child_info)

		abs_dep_path = self.solver.try_resolve_path(self.current_module, value, tags)
		if abs_dep_path != None:
			return self._link_path(abs_dep_path, tags)
			
		return None

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
