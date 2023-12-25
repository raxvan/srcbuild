
import os
import json

def find_packages_json(start_search_dir):
	current_dir = start_search_dir

	while current_dir != os.path.abspath(os.sep):
		package_json_path = os.path.join(current_dir, '#packages.json')

		if os.path.exists(package_json_path):
			return package_json_path

		current_dir = os.path.dirname(current_dir)

	return None


class ModuleLocator():
	def __init__(self, packages):
		if packages != None:
			self.workspace = packages["workspace"]
			self.modules = packages["modules"]
		else:
			self.workspace = None
			self.modules = {}

	def resolve_path(self, current_module, path, tags):
		if tags != None and "abspath" in tags:
			return path

		return os.path.abspath(os.path.join(current_module._abs_pipeline_dir, path))

	def try_resolve_path(self, current_module, path, tags):
		if tags != None and "abspath" in tags:
			if os.path.exists(path):
				return path

		path = os.path.abspath(os.path.join(current_module._abs_pipeline_dir, path))
		if os.path.exists(path):
			return path

		return None

	def resolve_abspath_or_die(self, current_module, path, tags):
		p = self.try_resolve_path(current_module, path, tags)
		if p == None:
			raise Exception(f"Could not find path {path} in module {current_module._abs_pipeline_path}")

		return p

	def try_resolve_module(self, current_module, path, tags):
		p = self.try_resolve_path(current_module, path, tags)
		if p != None:
			return p

		return self._try_get_modules(path)

	def resolve_module_or_die(self, current_module, path, tags):
		p = self.try_resolve_module(current_module, path, tags)
		if p == None:
			raise Exception(f"Could not find module {path} in module {current_module._abs_pipeline_path}")

		return p

	def _try_get_modules(self, path):

		mp = self.modules.get(path, None)
		if mp != None:
			rpath = os.path.join(self.workspace, mp)
			if os.path.exists(rpath):
				return rpath

		return None