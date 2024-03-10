
import os
import json
import package_utils
import package_graph
import package_config
import package_constructor
import srcbuild_default_paths


def _filter_builder_with_function(builders, search_function):
	result = []
	for b in builders:
		if hasattr(b, search_function):
			result.append(b)
	return result

def _get_builder_function(builders, search_function):
	result = []
	for b in builders:
		if hasattr(b, search_function):
			sf = getattr(b, search_function)
			result.append(sf.__func__)
	return result

##########################################################################################

class ProjectModule(package_graph.Module):
	def __init__(self, modkey, modpath, graph):
		package_graph.Module.__init__(self, modkey, modpath, graph)

		self.content = True
		self.builders = []

		#for construct_self in graph.module_constructors:
		#	construct_self(self)

##########################################################################################

class Solution(package_graph.ModuleGraph):
	def __init__(self, builders):
		package_graph.ModuleGraph.__init__(self)

		self.name = None
		self.output = ""
		self.modules_folder = None

		self.builders = builders

	def create_configurator(self):
		cfg = package_graph.ModuleGraph.create_configurator(self)

		for b in self.builders:
			b.configure(cfg)

		return cfg

	def create_module(self, modkey, modpath):
		return ProjectModule(modkey, modpath, self)

	def _prebuild(self):
		self.printer.print_header("PRE-BUILD...")

		for b in self.builders:
			b.prebuild(self)

		for m in self.get_modules():
			if m.enabled == False:
				self.printer.print_progress(f"> {m.get_name()}".ljust(32) + " -> SKIPPING: not enabled.")
				continue
        
			m.content = self.create_constructor(m)

			for b in self.builders:
				if b.accept(self, m):
					m.builders.append(b)
        
			if m.builders:
				self.printer.print_progress(f"> {m.get_name()}".ljust(32) + f" -> ACCEPTED: " + " ".join(map(str, m.builders)))
			else:
				self.printer.print_progress(f"> {m.get_name()}".ljust(32) + f" -> SKIPPING: no interested builders.")

	def _build_module(self, m):
		module_json = os.path.join(self.modules_folder, m.get_name() + ".json")
		
		if m.builders:
			#run construct
			construct_proc = m.get_proc("construct")
			if construct_proc == None:
				raise Exception(f"Could not find 'construct' function in {m.get_name()}")

			construct_proc(m.content)

			jout = {}
			#run builders 
			for b in m.builders:
				b.build(self, m, jout)

			jout["module"] = m.serialize()
			jout["content"] = m.content.serialize()
			
			#save contents to json file

			package_utils.save_json(jout, module_json)

			builders_msg = " ".join(map(str, m.builders))
			self.printer.print_progress(f"> {m.get_name()}".ljust(32) + f" -> OK <{builders_msg}>")
		else:
			try:
				f = open(module_json, "r")
				content_json = json.load(f)
				f.close()

				m.content.deserialize(content_json)
				
				self.printer.print_progress(f"> {m.get_name()}".ljust(32) + f" -> OK <from cache>")
			except Exception as e:
				self.printer.print_failed_progress(f"> {m.get_name()}".ljust(32) + "-> ", f"FAILED: module was never built or it's corrupted ...")
				self.printer.print_failed_progress(f"Investigate cache file: `{module_json}`","")
				raise
			

	def _postbuild(self):
		self.printer.print_header("POST-BUILD...")
		for b in self.builders:
			self.printer.print_progress(f"> {str(b)}")
			b.postbuild(self)

	def construct_from_path(self, path, outname, override_config):

		root_modules = self.configure([path])

		root_module = root_modules[0]

		out = None
		if outname != "":
			out = srcbuild_default_paths.get_custom_build_folder(root_module.get_package_absolute_path(), outname)
		else:
			out = srcbuild_default_paths.get_build_folder(root_module.get_package_absolute_path())

		self.name = root_module.get_name()
		self.output = out

		self.modules_folder = srcbuild_default_paths.get_build_modules_data(out)

		if not os.path.exists(out):
			os.makedirs(out)
		if not os.path.exists(self.modules_folder):
			os.makedirs(self.modules_folder)

		self.sync_config(srcbuild_default_paths.get_build_config_init(out), override_config)

		#running prebuild:
		self._prebuild()

		#build tree with root module and get iterator
		itr = self.build(root_modules)

		self.printer.print_header("BUILDING...")

		while itr.count > 0:

			mk = itr.begin()

			m = self.modules[mk]
			if m.enabled == False:
				raise Exception(f"> {m.get_name()}".ljust(16) + " -> not enabled ...")

			self._build_module(m)

			itr.end(mk)

		#running post build
		self._postbuild()
		

		self.printer.print_header("DONE...")


