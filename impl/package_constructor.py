
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

	def newfolder(self, fpath):
		apath, entry = self._add_new_folder(fpath)
		if not os.path.exists(apath):
			os.makedirs(apath)
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

		r = []

		for root, dirnames, filenames in os.walk(apath):
			for f in filenames:
				if file_filter != None:
					if not fnmatch.fnmatch(f, file_filter):
						continue;
				abs_item_path = os.path.join(root, f)
				path_entry = package_utils.FileEntry(abs_item_path, tags)
				self._paths[abs_item_path] = path_entry
				self._files.append(abs_item_path)
				r.append(path_entry)

		return r

	def module_enabled(self, modname):
		return self._graph.module_enabled(modname)

	def component_enabled(self, component_name):
		c = self._config._components.get(component_name, None)
		if c == None:
			raise Exception(f"Component {component_name} was not found!")
		return c.enabled


	def module(self, modname):
		return self._graph.get_module(modname)

	def get_child(self, modname):
		module = self._graph.names.get(modname,None)
		if module == None:
			return None
		if module.key in self._module.links:
			return module
		return None

	###############################################################################
	# property setters
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

	def setoption(self, pkey, pvalue = None):
		tags, key = package_utils._parse_key(pkey)

		opt = self._config._options.get(key, None)
		if opt == None:
			raise Exception(f"No configuratin found with name {key}")

		if pvalue == None:
			prop = self.set(pkey, opt.get_value())
			prop.join_tags(opt.tags)
			return prop
		elif opt.allow_value(pvalue) == True:
			prop = self.set(pkey, pvalue)
			prop.join_tags(opt.tags)
			return prop
		else:
			raise Exception(f"Failed to create property {pkey}")

	def get_option(self, pkey):
		c = self._config._options.get(pkey, None)
		if c == None:
			raise Exception(f"No configuratin found with name {pkey}")
		return c.get_value()

	###############################################################################
	#internal
	def _add_path_internal(self, apath, constructor, tags):
		path_entry = self._paths.get(apath, None)
		if path_entry == None:
			path_entry = constructor(apath, tags)
			self._paths[apath] = path_entry
		elif tags != None:
			path_entry.join_tags(tags)

		return apath, path_entry

	def _add_loaded_path(self, abspath, constructor, tags):
		apath = self._solver.resolve_abspath_or_die(self._module, abspath, "abspath")
		return self._add_path_internal(apath, constructor, tags)
		
	def _add_path(self, pvalue, constructor):
		tags, value = package_utils._parse_key(pvalue)

		apath = self._solver.resolve_abspath_or_die(self._module, value, tags)
		return self._add_path_internal(apath, constructor, tags)

	def _add_new_folder(self, pvalue):
		tags, value = package_utils._parse_key(pvalue)
		apath = self._solver.resolve_path(self._module, value, tags)
		return self._add_path_internal(apath, package_utils.FolderEntry, tags)

	def query_paths(self, tags):
		ts = package_utils.make_tags(tags)
		result = []
		for _,pe in self._paths.items():
			if ts.issubset(pe.tags):
				result.append(pe)

		return result

	def query_files(self, tags):
		ts = package_utils.make_tags(tags)
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

	def get_property(self, pk):
		return self._props.get(pk, None)

	def query_props(self, tags):
		ts = package_utils.make_tags(tags)
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
				"tags" : sorted(list(v.tags))
			}

		for f in self._files:
			e = self._paths[f]
			files[f] = sorted(list(e.tags))

		for f in self._folders:
			e = self._paths[f]
			folders[f] = sorted(list(e.tags))

		data["content"] = {
			"files" : files,
			"folders" : folders,
			"props" : props,
		}

	def deserialize(self, data):
		content = data['content']
		props = content['props']
		files = content['files']
		folders = content['folders']

		for k, v in props.items():
			prop_entry = package_utils.PeropertyEntry(v['data'], v['tags'])
			self._props[k] = prop_entry

		for k, v in files.items():
			apath, entry = self._add_path_internal(k, package_utils.FileEntry, v)
			self._files.append(apath)

		for k, v in folders.items():
			apath, entry = self._add_path_internal(k, package_utils.FolderEntry, v)
			self._folders.append(apath)

