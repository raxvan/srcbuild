
import os
import hashlib

import package_utils

class PackageConstructor():
	def __init__(self, solver):
		
		self.current_module = None
		self.path_solver = solver
		self.props = {}
		self.paths = {}

	def folder(self, fpath):
		apath, entry = self._add_path(fpath, package_utils.FolderEntry)

		if os.path.isdir(apath) == False:
			raise Exception(f"Expected directory at {apath}")

		return entry

	def file(self, fpath):
		apath, entry = self._add_path(fpath, package_utils.FileEntry)

		if os.path.isdir(apath) == False:
			raise Exception(f"Expected file at {apath}")

		return entry

	def fscan(self, fpath):
		tags, value = package_descriptor._parse_key(fpath)

		apath = self.path_solver.resolve_abspath_or_die(self.current_module, value, tags)

		for root, dirnames, filenames in os.walk(apath):
			for f in filenames:
				abs_item_path = os.path.join(root, f)
				path_entry = package_utils.FileEntry(abs_item_path, tags)
				self.paths[apath] = path_entry


	def prop(self, pkey, pvalue):
		tags, key = package_descriptor._parse_key(pkey)

		prop_entry = self.props.get(key, None)
		if prop_entry == None:
			prop_entry = PeropertyEntry(pvalue, tags)
			self.props[key] = prop_entry
		else:
			prop_entry.tag(tags)
			prop_entry.value = pvalue


	#internal
	def _add_path(self, pvalue, constructor):
		tags, value = package_descriptor._parse_key(pvalue)

		apath = self.path_solver.resolve_abspath_or_die(self.current_module, value, tags)
		
		path_entry = self.paths.get(apath, None)
		if path_entry == None:
			path_entry = constructor(apath, tags)
			self.paths[apath] = path_entry
		else:
			path_entry.tag(tags)

		return apath, path_entry

	
"""
	def collect(self,out):
		
		out['props'] = self._collect_props()
		out['paths'] = self._collect_paths()
		out['files'] = self._collect_files()


	def get_property_or_die(self,propname):
		pv = self.props.get(propname,None)
		if pv == None:
			raise Exception("Missing property `" + propname + "`")
			
		return pv.value

	def query_props(self, taglist):
		stags = set(taglist)
		result = []
		for n,p in self.props.items():
			if p.query_tags(stags):
				result.append((n,p))
		return result

	def query_paths(self, taglist):
		stags = set(taglist)
		result = []
		for _,p in self.paths.items():
			if p.query_tags(stags):
				result.append(p)
		return result

	def query_files(self, taglist):
		stags = set(taglist)
		result = []
		for n,p in self.files.items():
			if p.query_tags(stags):
				result.append(n)
		return result

	def _add_property(self, k, v, _tags):
		e = self.props.get(k,None)
		if e != None:
			e.value = v
		else:
			e = PackageProperty(k, v)
			self.props[k] = e
		if _tags != None:
			e.tag(_tags)
		return e

	def _add_path(self, path, _tags):
		pid = path.get_uuid()
		if pid in self.paths:
			raise Exception("Multiple definitions of path " + pid)

		ppath = PackagePath(path)
		self.paths[pid] = ppath

		abs_path = ppath.get_abs_path()
		if os.path.exists(abs_path):

			if os.path.isfile(abs_path):
				ppath.isfile = True
				self._add_file(abs_path, p.tags)

		elif not "optional" in p.tags:
			raise Exception("Path not found: " + abs_path)


		return ppath

	def _scan_path(self, path, _tags):
		abs_path = path.get_abs_path()
		
		if os.path.exists(abs_path):
			for root, dirnames, filenames in os.walk(abs_path):
				for f in filenames:
					abs_item_path = os.path.join(root, f)
					self._add_file(abs_item_path, _tags)

		elif not "optional" in _tags:
			raise Exception("Path not found: " + abs_path)

	def _add_file(self, abs_path, _tags):
		e = self.files.get(abs_path,None)
		if e == None:
			e = PackageEntry()
			self.files[abs_path] = e
		if _tags != None:
			e.tag(_tags)
		return e

			

	def _collect_props(self):
		out = {}
	
		for _,p in self.props.items():
			out[p.name] = [p.value, list(p.tags)]
	
		return out
	
	def _collect_paths(self):
		out = {}
	
		for _,p in self.paths.items():
			abs_path = p.path.get_abs_path()
			out[abs_path] = list(p.tags)
			
		return out
	
	def _collect_files(self):
		out = {}
	
		for f,e in self.files.items():
			out[f] = list(e.tags)
	
		return out
		
"""
	