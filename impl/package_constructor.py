
import os
import hashlib
import os, fnmatch

import package_utils

class PackageConstructor():
	def __init__(self, graph, module):
		self._graph = graph
		self._module = module
		self._solver = graph.locator
		self._config = graph.configurator

		self._props = {}
		self._paths = {}

		self._files = []
		self._folders = []

	###############################################################################
	# file scanning:

	def folder(self, fpath):
		apath, entry = self._add_path(fpath, package_utils.FolderEntry)

		if os.path.isdir(apath) == False:
			raise Exception(f"Expected directory at {apath}")

		self._folders.append(apath)

		return entry

	def file(self, fpath):
		apath, entry = self._add_path(fpath, package_utils.FileEntry)

		if os.path.isfile(apath) == False:
			raise Exception(f"Expected file at {apath}")

		self._files.append(apath)

		return entry

	def fscan(self, fpath, file_filter = None):
		tags, value = package_utils._parse_key(fpath)

		apath = self._solver.resolve_abspath_or_die(self._module, value, tags)

		for root, dirnames, filenames in os.walk(apath):
			for f in filenames:
				if file_filter != None:
					if fnmatch.filter(f, file_filter):
						continue;
				abs_item_path = os.path.join(root, f)
				path_entry = package_utils.FileEntry(abs_item_path, tags)
				self._paths[abs_item_path] = path_entry
				self._files.append(abs_item_path)

	def module_enabled(self, modname):
		return self._graph.module_enabled(modname)


	###############################################################################
	# property setters
	def assign(self, pkey, pvalue = None):
		tags, key = package_utils._parse_key(pkey)

		prop_entry = self._props.get(key, None)
		if prop_entry == None:
			prop_entry = package_utils.PeropertyEntry(pvalue, tags)
			self._props[key] = prop_entry
			return prop_entry
		elif tags != None:
			prop_entry.tag(tags)

		prop_entry.value = pvalue

		return prop_entry

	def config(self, pkey, pvalue = None):
		# search of pkey in config and optinos and try to set override it with pvalue
		# if pvalue is None then value is taken from config

		c = self._config._options.get(pkey, None)
		if c == None:
			raise Exception(f"No configuratin found with name {pkey}")

		if pvalue == None:
			prop = self.assign(pkey, c.get_value())
			prop.join_tags(c.tags)
			return prop
		elif c.allow_value(pvalue) == True:
			prop = self.assign(pkey, pvalue)
			prop.join_tags(c.tags)
			return prop
		else:
			raise Exception(f"Failed to create property {pkey}")



	#internal
	def _add_path(self, pvalue, constructor):
		tags, value = package_utils._parse_key(pvalue)

		apath = self._solver.resolve_abspath_or_die(self._module, value, tags)
		
		path_entry = self._paths.get(apath, None)
		if path_entry == None:
			path_entry = constructor(apath, tags)
			self._paths[apath] = path_entry
		elif tags != None:
			path_entry.tag(tags)

		return apath, path_entry

	def query_paths(self, tags):
		ts = set(tags)
		result = []
		for _,pe in self._paths.items():
			if ts.issubset(pe.tags):
				result.append(pe)

		return result

	def query_files(self, tags):
		ts = set(tags)
		result = []
		for _,pe in self._paths.items():
			if isinstance(pe, package_utils.FileEntry) and ts.issubset(pe.tags):
				result.append(pe)

		return result

	def get_property_or_die(self, pk):
		p = self._props.get(pk, None)
		if p == None:
			raise Exception(f"Could not find property {pk}")
		return p

	def query_props(self, tags):
		ts = set(tags)
		result = []
		for pk,pe in self._props.items():
			if ts.issubset(pe.tags):
				result.append((pk,pe))

		return result

	def serialize(self, data):
		props = {}
		files = {}
		folders = {}

		for p,v in self._props.items():
			props[p] = {
				"data" : v.value,
				"tags" : list(v.tags)
			}

		for f in self._files:
			e = self._paths[f]
			files[f] = list(e.tags)

		for f in self._folders:
			e = self._paths[f]
			folders[f] = list(e.tags)

		data["content"] = {
			"files" : files,
			"folders" : folders,
			"props" : props,
		}




