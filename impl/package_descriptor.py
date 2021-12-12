
import os


class PathInfo():
	def __init__(self, ctx, rel_path):
		self.context = ctx
		self.path = rel_path


		self.filename = None
		self.cache_full_path = None
		self.cache_dir_path = None


	def get_abs_path(self):
		if self.cache_full_path == None:
			self.cache_full_path = os.path.abspath(os.path.join(self.context.get_package_dir(), self.path))
		return self.cache_full_path


	def get_context_path(self):
		return os.path.relpath(self.get_abs_path(),self.context.get_package_dir())

	def get_filename(self):
		if self.filename != None:
			return self.filename;

		self.cache_dir_path, self.filename = os.path.split(self.get_abs_path())

		return self.filename

	def get_package_name(self):
		f = self.get_filename()
		return f.replace(".pak.py","")

	def get_uuid(self):
		return self.get_abs_path()

#--------------------------------------------------------------------------------------------------------------------------------

class PackageEntry():
	def __init__(self):
		self.tags = set()

	def tag(self, utag):
		if isinstance(utag, str):
			self.tags.add(utag)
		elif isinstance(utag, list):
			self.tags = self.tags.union(set(utag))
		elif isinstance(utag, set):
			self.tags = self.tags.union(utag)
		return self

	def query_tags(self, tags_set):
		return set(tags_set).issubset(self.tags)


#--------------------------------------------------------------------------------------------------------------------------------

class PackageDependency(PackageEntry):
	def __init__(self, path):
		PackageEntry.__init__(self)
		self.path = path

	def get_name(self):
		return self.path.get_package_name()

class PackageProperty(PackageEntry):
	def __init__(self, name, value):
		PackageEntry.__init__(self)
		self.name = name
		self.value = value

class PathProperty(PackageEntry):
	def __init__(self, path):
		PackageEntry.__init__(self)
		self.path = path

class PackageScan(PackageEntry):
	def __init__(self, path):
		PackageEntry.__init__(self)
		self.path = path

#--------------------------------------------------------------------------------------------------------------------------------

class PackageData():
	def __init__(self):
		
		self.dependency = []
		self.dependency_map = {}

		self.props = {}

		self.paths = {}

		self.scans = {}

		#colections:

		self.files = {}


	def collect(self,out):
		self._collect_init()
		out['props'] = self._collect_props()
		out['paths'] = self._collect_paths()
		out['files'] = self._collect_files()
		out['depends'] = self._collect_dependency()


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

	def query_dependencies(self, taglist):
		stags = set(taglist)
		result = []
		for p in self.dependency:
			if p.query_tags(stags):
				result.append(p)
		return result

	def _add_dependency(self, path, _tags):
		pid = path.get_uuid()
		e = self.dependency_map.get(pid,None)
		if e == None:
			e = PackageDependency(path)
			self.dependency.append(e)
			self.dependency_map[pid] = e
		if _tags != None:
			e.tag(_tags)
		return e

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
		e = self.paths.get(pid,None)
		if e == None:
			e = PathProperty(path)
			self.paths[pid] = e
		if _tags != None:
			e.tag(_tags)
		return e

	def _add_file_scan(self, path, _tags):
		pid = path.get_uuid()
		e = self.scans.get(pid,None)
		if e == None:
			e = PackageScan(path)
			self.scans[pid] = e
		if _tags != None:
			e.tag(_tags)
		return e

	def _add_file(self, abs_path, _tags):
		e = self.files.get(abs_path,None)
		if e == None:
			e = PackageEntry()
			self.files[abs_path] = e
		if _tags != None:
			e.tag(_tags)
		return e

	#--------------------------------------------------------------------------------------------------------------------------------
	def _collect_init(self):
		for _,p in self.paths.items():
			abs_path = p.path.get_abs_path()
			if not os.path.exists(abs_path):
				raise Exception("Path not found: " + abs_path)
			if os.path.isfile(abs_path):
				self._add_file(abs_path, p.tags)

		for _,p in self.scans.items():
			abs_path = p.path.get_abs_path()
			if not os.path.exists(abs_path):
				raise Exception("Path not found: " + abs_path)

			for root, dirnames, filenames in os.walk(abs_path):
				for f in filenames:
					abs_item_path = os.path.join(root, f)

					#filename, file_extension = os.path.splitext(f)
					#	if(file_extension in _ext):

					self._add_file(abs_item_path, p.tags)

	def _collect_dependency(self):
		out = []

		for p in self.dependency:
			out.append([p.get_name(),list(p.tags)])

		return out

	def _collect_props(self):
		out = {}

		for _,p in self.props.items():
			out[p.name] = [p.value, list(p.tags)]

		return out

	def _collect_paths(self):
		out = {}

		for _,p in self.paths.items():
			abs_path = p.path.get_abs_path()
			
			#if path is file, then add it to entry
			if os.path.isfile(abs_path):
				f = self._add_file(abs_path, None)
				out[abs_path] = list(f.tags)
			else:
				out[abs_path] = list(p.tags)
			

		return out

	def _collect_files(self):
		out = {}

		for f,e in self.files.items():
			out[f] = list(e.tags)

		return out
		

	