
import os
import hashlib

import package_utils

def _parse_bool_value(sv):
	if sv in ["true", "on", "yes", "1"]:
		return True
	if sv in ["false", "off", "no", "0"]:
		return False

	raise Exception("Invalid bool `" + str(sv) + "`")
	
def _load_ini_map(abs_path_to_ini, components, options):
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
			if section == "OPTIONS":
				options[kn] = sv
			elif section == "COMPONENTS":
				components[kn] = _parse_bool_value(sv.lower())

	return True

def _save_init_map(abs_path_to_ini, options, components, all_options, all_components):
	f = open(abs_path_to_ini, "w")
	if f == None:
		raise Exception(f"Failed create file {abs_path_to_ini}")

	f.write("[COMPONENTS]\n")
	for cname, _ in all_components:
		if cname in components:
			f.write(f"{cname} = 1\n")
		else:
			f.write(f"{cname} = 0\n")
	
	f.write("[OPTIONS]\n")
	for oname, ovalue in all_options.items():
		c = options[oname]
		f.write(f"{oname} = {c}\n")

		if ovalue.accepts != None:
			index = 0
			for acc in ovalue.accepts:
				f.write(f"\t#{index}:{acc}\n")
				index = index + 1

	f.close()

#--------------------------------------------------------------------------------------------------------------------------------

class UserOption():
	def __init__(self):
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
			return self.accepts[0]
		return self.defaults[0]

class UserComponent():
	def __init__(self):
		self.enabled = None

	def update(self, value):
		if value != None and self.enabled == None:
			self.enabled = value

#--------------------------------------------------------------------------------------------------------------------------------

class Configurator():
	def __init__(self, solver):

		self.current_module = None
		self.current_dependency = None

		self.path_solver = solver

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
		
	#api
	def link(self, child_info):
		# links child to current module (parent)
		tags, value = package_utils._parse_key(child_info)

		abs_dep_path = self.path_solver.resolve_abspath(self.current_module, value, tags)
		modkey = package_utils._path_to_modkey(abs_dep_path)

		if (modkey == self.current_module.key):
			#depends on itself ?
			return

		self.current_dependency.append((self.current_module, modkey, abs_dep_path))
		return self.current_module._link_child_module(modkey, tags, abs_dep_path);
		

	def option(self, k, default_value, possible_values = None):
		o = self._options.get(k,None)
    
		if o == None:
			o = UserOption()
			self._options[k] = o
    
		if possible_values != None:
			o.add_accepted_values(possible_values)
		
		if default_value != None:
			o.add_default_value(default_value)

		return o
    
	def component(self, name, default_bool_value = None):
		
		c = self._components.get(name,None)
    
		if c == None:
			c = UserComponent()
			self._components[name] = c
    
		if not (default_bool_value == None or default_bool_value == False or default_bool_value == True):
			raise Exception("Expeting bool or None, got " + str(name) + ".")

		c.update(default_bool_value)

		return c

def get_config_ini(cfg):
	r = ""

	r = r + "[COMPONENTS]\n"
	for cname, cvalue in cfg._components.items():
		if cvalue.enabled == None:
			r = r + f"#{cname} = *\n"
		elif cvalue.enabled == True:
			r = r + f"{cname} = 1\n"
		else:
			r = r + f"{cname} = 0\n"
	
	r = r + "[OPTIONS]\n"
	for oname, ovalue in cfg._options.items():
		c = ovalue.get_value()
		r = r + f"{oname} = {c}\n"

		if ovalue.accepts != None:
			index = 0
			for acc in ovalue.accepts:
				r = r + f"\t#{index}:{acc}\n"
				index = index + 1

	r = r + "#end.\n"

	return r







	#internal
"""
	def _load_ini_configs(self):
		user_options = {}
		user_components = {}
		for c in self.config_list:
			_load_ini_map(c, user_components, user_options)

		return user_components, user_options

	def sync(self, solution_config, abs_path_to_ini_config):
		user_components, user_options = self._load_ini_configs()
		
		#components:
		for cname, cv in self._components.items():

			if cname in user_components:
				if user_components[cname] == True:
					solution_config.components.add(cname)
				continue

			#if one module enagled this, it's enabled for all modules
			if cv.enabled:
				solution_config.components.add(cname)

		#options:
		for optname, opt in self._options.items():
			optvalue = None

			if optname in user_options:
				v = user_options[optname]
				if opt.accepts != None:
					if not v in opt.accepts:
						raise Exception(
							f"Option {optname} value {v} is not accepted:" +
							",".format(opt.accepts)
						)
				optvalue = v
			elif opt.defaults != None:
				for v in opt.defaults:
					if opt.accepts != None:
						if v in opt.accepts:
							optvalue = v
							break
					else:
						optvalue = v
						break
			elif opt.accepts != None:
				optvalue = opt.accepts[0]

			if optvalue == None:
				em = [f"Could not resolve option {optname};"]
				if opt.defaults != None:
					em.append("Defaults: " + ",".format(opt.defaults) + ";")
				if opt.accepts != None:
					em.append("Accepts: " + ",".format(opt.accepts) + ";")
				raise Exception("\n".format(em))

			solution_config.options[optname] = str(optvalue)

		_save_init_map(
			abs_path_to_ini_config,
			solution_config.options,
			solution_config.components,
			self._options,
			self._components
		)
		
"""