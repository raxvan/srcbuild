
import os
import subprocess
import argparse
import json

class BuildOptions():
	def __init__(self):
		self._options = {}

		self._bool_options = set()
		self._str_options = {}
		

	def create(self, k, v, possible_values):
		if not v in possible_values:
			raise Exception("Incompatible config [" + k + "] with value `" + v + "`, expecting [" + ",".join(possible_values) + "].")

		self._options[k] = v
		self._str_options[k] = self._str_options.get(k, set()).union(set(possible_values))
		

	def get_value_or_die(self, name):
		v = self._options.get(name, None)
		if v == None:
			raise Exception("Missing option `" + name + "`")

		return v

	def get(self, k, v = None):

		#TODO: improve "options" functionality
		# this is a hack

		rvalue = self._options.get(k, None)


		if v == None:
			self._bool_options.add(k)
		elif isinstance(v, list):
			if rvalue != None:
				if not rvalue in v:
					raise Exception("Incompatible value `" + rvalue + "`, expecting [" + ",".join(v) + "].")

			self._str_options[k] = self._str_options.get(k, set()).union(set(v))
		elif isinstance(v, str):
			self._str_options.setdefault(k, set()).add(v)

		if rvalue == None:
			#no assigned value, try to get a value
			possible_values = self._str_options.get(k,None)
			if possible_values != None:
				for v in possible_values:
					self._options[k] = v
					return v

			if k in self._bool_options:
				#unless somone asigns a value to this, we consider that it is a bool option
				return ""

		return rvalue

	def add_ini_config(self, abs_path_to_ini):
		import configparser
		config = configparser.ConfigParser(allow_no_value=True)
		config.optionxform=str #preserve case for keys
		
		f = open(abs_path_to_ini, "r")
		config.read_string("[void]\n" + f.read())
		f.close()
		
		result = []
		for section in config:
			section_obj = config[section]
			for key in section_obj:
				kn = str(key).strip()
				sv = str(section_obj[key]).strip()

				if sv == "":
					self._bool_options.add(kn)
				else:
					self._options[kn] = sv

	def save_ini_config(self, abs_path_to_ini):
		fout = ""

		all_options = sorted(set(
			[k for k,v in self._options.items()] + 
			[k for k,v in self._str_options.items()] +
			list(self._bool_options)
		))

		for o in all_options:
			v = self._options.get(o,None)

			if v == None and o in self._bool_options:
				fout = fout + "#" + o + "=\n"
				fout = fout + "\t#BOOL\n"
			elif v != None:
				possible_values = self._str_options.get(o,None)
				fout = fout + "" + o + "=" + str(v) + "\n"

				if possible_values != None:
					possible_values = sorted(possible_values)
					fout = fout + "\t#options:" + ",".join(possible_values) + "\n"
			else:
				raise Exception("Internal error")

		f = open(abs_path_to_ini, "w")
		f.write(fout)
		f.close()


	def collect(self, out):
		all_options = sorted(set(
			[k for k,v in self._options.items()] + 
			[k for k,v in self._str_options.items()] +
			list(self._bool_options)
		))

		for o in all_options:
			v = self._options.get(o,None)
			if v == None and o in self._bool_options:
				out[o] = "" #no value
			elif v != None:
				out[o] = v