
import os
import hashlib


def _parse_key_value(left, right):
		name = right.strip()
		tags = [t.strip() for t in left.replace(" ",",").split(",")]
		return (tags, name)

def _parse_key(name):
	if "|" in name:
		left, right = name.split("|")
		return _parse_key_value(left,right)
	elif ":" in name:
		left, right = name.split(":")
		return _parse_key_value(left,right)
	else:
		return (None,name)

def _path_to_modkey(abs_path_to_module):
	return hashlib.sha256(abs_path_to_module.lower().encode('utf-8')).hexdigest()

def save_json(j, abs_output_file):
	import json
	with open(abs_output_file, "w") as outfile:
		outfile.write(json.dumps(j, indent=4, sort_keys=True))

#--------------------------------------------------------------------------------------------------------------------------------	

class PackageEntry():
	def __init__(self, utag = None):
		if utag == None:
			self.tags = set()
		elif isinstance(utag, str):
			self.tags = set([utag])
		elif isinstance(utag, list):
			self.tags = set(utag)
		elif isinstance(utag, set):
			self.tags = utag

	def join_tags(self, utag):
		if utag != None:
			if isinstance(utag, str):
				self.tags.add(utag)
			elif isinstance(utag, list):
				self.tags = self.tags.union(set(utag))
			elif isinstance(utag, set):
				self.tags = self.tags.union(utag)
		return self

	#def query_tags(self, tags_set):
	#	return set(tags_set).issubset(self.tags)
    #
	#def check_subtags_set(self, tags_set):
	#	return tags_set.issubset(self.tags)
    #

	def get_tags_str(self, suffix):
		if self.tags:
			return suffix + "[" + ",".join(list(self.tags)) + "]"
		return ""

#--------------------------------------------------------------------------------------------------------------------------------

class PathEntry(PackageEntry):
	def __init__(self, path, tags):
		PackageEntry.__init__(self, tags)
		self.path = path


	def get_path_relative_to(self, p):
		return os.path.relpath(self.get_abs_path(),p)

#--------------------------------------------------------------------------------------------------------------------------------

class ModuleLink(PathEntry):
	def __init__(self, abspath, tags):
		PathEntry.__init__(self, abspath, tags)

#--------------------------------------------------------------------------------------------------------------------------------

class PeropertyEntry(PackageEntry):
	def __init__(self, value, tags):
		PackageEntry.__init__(self, tags)

		self.value = value

#--------------------------------------------------------------------------------------------------------------------------------

class FileEntry(PathEntry):
	def __init__(self, path, tags):
		PathEntry.__init__(self, path, tags)
		

class FolderEntry(PathEntry):
	def __init__(self, path, tags):
		PathEntry.__init__(self, path, tags)

#--------------------------------------------------------------------------------------------------------------------------------

#class PathEntry(PackageEntry):
#	def __init__(self, ctx, rel_path, tags):
#		PackageEntry.__init__(self, tags)
#
#		#self.context = ctx
#		self.path = rel_path
#
#		self.filename = None
#		self.cached_abs_path = None
#		self.cache_dir_path = None
#
#def get_abs_path(self):
#	if self.cached_abs_path == None:
#		self.cached_abs_path = self.context.resolve_abspath(self.path, self.tags)
#	return self.cached_abs_path

#def get_context_path(self):
#	#returns path relative to current context
#	return os.path.relpath(self.get_abs_path(),self.context.get_package_dir())

#def get_filename(self):
#	if self.filename != None:
#		return self.filename;
#
#	self.cache_dir_path, self.filename = os.path.split(self.get_abs_path())
#
#	return self.filename
#
#def get_package_name(self):
#	f = self.get_filename()
#	return f.replace(".pak.py","")
#
#def get_uuid(self):
#	return self.get_abs_path()

#--------------------------------------------------------------------------------------------------------------------------------

