
import os
import hashlib

import package_descriptor

import importlib.util

#--------------------------------------------------------------------------------------------------------------------------------

class PackageAggregator():
	def __init__(self, context, data, tags):
		self.context = context

		self.content = data

		self.tags = tags
		if self.tags == None:
			self.tags = []


	def _get_tags(self, base_tags):
		if base_tags == None:
			return self.tags

		return self.tags + base_tags

	def _get_path(self, rel_path):
		return package_descriptor.PathInfo(self.context, rel_path)

	def _parse_key(self, name):
		if ":" in name:
			left,right = name.split(":")

			name = right.strip()
			extra_tags = [t.strip() for t in left.replace(" ",",").split(",")]
			return (name,extra_tags)
		else:
			return (name,None)


	def dependency(self, rel_path):
		_name, _tags = self._parse_key(rel_path)
		_path = self._get_path(_name)
		return self.content._add_dependency(_path, _tags)

	def prop(self, k, v = None):
		_name, _tags = self._parse_key(k)
		return self.content._add_property(_name, v, _tags)

	def path(self, rel_path):
		_name, _tags = self._parse_key(rel_path)
		_path = self._get_path(_name)
		return self.content._add_path(_path, _tags)

	def fscan(self, rel_path):
		_name, _tags = self._parse_key(rel_path)
		_path = self._get_path(_name)
		return self.content._add_file_scan(_path, _tags)

#--------------------------------------------------------------------------------------------------------------------------------

def _load_module(abs_path_to_pyfile):
	load_location = "srcpak.sha." + hashlib.sha256(abs_path_to_pyfile.encode('utf-8')).hexdigest()

	spec = importlib.util.spec_from_file_location(load_location, abs_path_to_pyfile)
	module_context = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module_context)

	#source hash	
	sh = hashlib.sha256(spec.loader.get_data(abs_path_to_pyfile)).hexdigest()

	return (module_context,sh)


class PackageBuilder():
	def __init__(self, abs_path_to_constructor, options):

		self.pipeline, self.srchash = _load_module(abs_path_to_constructor)

		self._abs_pipeline_path = abs_path_to_constructor
		self._abs_pipeline_dir, self._pipeline_filename = os.path.split(abs_path_to_constructor)

		self._name = self._pipeline_filename.replace(".pak.py","")
		

		self.content = package_descriptor.PackageData()
		#public
		self.options = options

		self._default_aggregator = PackageAggregator(self, self.content, None)

	#--------------------------------------------------------------------------------------------------------------------------------
	#main aggregator	

	def dependency(self, rel_path):
		return self._default_aggregator.dependency(rel_path);

	def prop(self, k, v = None):
		return self._default_aggregator.prop(k, v)

	def path(self, rel_path):
		return self._default_aggregator.path(rel_path)

	def fscan(self, rel_path):
		return self._default_aggregator.fscan(rel_path)

	#--------------------------------------------------------------------------------------------------------------------------------

	def get_package_dir(self):
		return self._abs_pipeline_dir

	def get_name(self):
		return self._name

	def create_json_desc(self):
		pass

	def collect(self, out):
		options_data = {}
		self.options.collect(options_data)

		content_data = {}
		self.content.collect(content_data)

		out['name'] = self.get_name()
		out['srcpath'] = self._abs_pipeline_path
		out['srcdir'] = self._abs_pipeline_dir

		out['options'] = options_data
		out['content'] = content_data



def construct_package(package):
	package.pipeline.construct(package)

def get_package_output(package, builder, platform):
	pak_dirname = builder + "-" + platform + "-" + package.get_name()
	if hasattr(package.pipeline, 'output'):
		return os.path.abspath(os.path.join(package.pipeline.output(package),pak_dirname))
	else:
		return os.path.abspath(os.path.join(package._abs_pipeline_dir,"build",pak_dirname))

def get_package_priority(package):
	if hasattr(package.pipeline, 'priority'):
		return package.pipeline.priority(package)
	else:
		return 0


