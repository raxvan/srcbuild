
import os


class ModuleLocator():
	def __init__(self):
		pass

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
		
		return None

	def resolve_module_or_die(self, current_module, path, tags):
		p = self.try_resolve_module(current_module, path, tags)
		if p == None:
			raise Exception(f"Could not find module {path} in module {current_module._abs_pipeline_path}")

		return p
