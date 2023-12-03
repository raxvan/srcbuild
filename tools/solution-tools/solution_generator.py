
import os
import sys

import package_graph
import package_config
import package_constructor
import package_utils

class ProjectModule(package_graph.Module):
	def __init__(self, modkey, modpath, graph):
		package_graph.Module.__init__(self, modkey, modpath, graph)

		self.content = None

class Solution(package_graph.ModuleGraph):
	def __init__(self, builder, override_config):
		package_graph.ModuleGraph.__init__(self)

		#self.platform = platform
		self.builder = builder

		self.override_config = override_config

	def create_configurator(self):
		cfg = package_graph.ModuleGraph.create_configurator(self)

		cfg.option("builder", self.builder, ["vs", "cmake", "zip"])
		cfg.option("cppstd","20",["11","14","17","20"])
		cfg.option("type","exe",["exe","lib"])
		cfg.option("warnings","full",["off","default", "full"])
		cfg.option("default-visual-studio","vs2022",["vs2015","vs2017", "vs2019", "vs2022"])

		return cfg

	def create_module(self, modkey, modpath):
		return ProjectModule(modkey, modpath, self)

	def run_autogenerate(self, autogenerate_map):
		if not autogenerate_map:
			return

		import source_generator

		for k,v in autogenerate_map.items():
			source_generator.generate(k, v)


	def collect_autogenerate(self, module, autogenerate_map, autogen_list):
		for a in autogen_list:
			tags, path = package_utils._parse_key(a)
			abs_module_path = self.locator.resolve_abspath_or_die(module, path, tags)
			basepath, name = os.path.split(abs_module_path)

			autogenerate_map.setdefault(name.replace(".autogen.py", ""), []).append(abs_module_path)
			#source_generator.generate(name.replace(".autogen.py", ""), abs_module_path, basepath)

	def generate(self, path):

		cfg, root_modules = self.configure([path])

		root_module = root_modules[0]

		output = os.path.join(root_module.get_package_dir(),"build",self.builder + "-" + root_module.get_simplified_name())
		output = os.path.abspath(output)
		metaout = os.path.join(output, "modules")
		if not os.path.exists(metaout):
			os.makedirs(metaout)

		self.sync_config(os.path.join(output, "config.ini"), self.override_config)

		self.forward_disable(root_modules)

		all_modules = self.modules

		assets_ini = {}

		package_utils.display_status("GENERATING...")

		#collect autogenerate
		autogenerate_map = {}
		for mk, m in all_modules.items():
			autogenerate_proc = m.get_proc("autogenerate")
			if autogenerate_proc != None:
				self.collect_autogenerate(m, autogenerate_map, autogenerate_proc())

		self.run_autogenerate(autogenerate_map)

		for mk, m in all_modules.items():
			if m.enabled == False:
				print(f"> {m.get_name()}".ljust(16) + " -> not enabled ...")
				continue
			
			print(f"> {m.get_name()}".ljust(16) + " -> ok!")

			m.content = self.create_constructor(m)

			m.content.assign_option("builder")
			m.content.assign_option("cppstd")
			m.content.assign_option("type")
			m.content.assign_option("warnings")


			construct_proc = m.get_proc("construct")
			if construct_proc == None:
				raise Exception(f"Could not find 'construct' function in {m.get_name()}")

			construct_proc(m.content)

			#save name for later use
			if m.content.get_property_or_die("type").value == "exe":
				m.content.assign("exe-name","_" + m.get_name())

			#get assets with relative path
			assets = list(set([p.path for p in m.content.query_files(["asset"])]))
			for a in assets:
				h,t = os.path.split(a)
				if t in assets_ini:
					raise Exception("Duplicate asset foud: " + a)
				assets_ini[t] = a

			#save json files
			j = {}
			m.serialize(j)
			m.content.serialize(j)

			package_utils.save_json(j, os.path.join(metaout, m.get_name() + ".json"))

		if assets_ini:
			package_utils.save_assets_ini(assets_ini, output)

		package_utils.display_status("DONE...")

		return (root_module.get_name(), output, cfg)


def _import_generators():
	_this_dir = os.path.dirname(os.path.abspath(__file__))
	sys.path.append(os.path.join(_this_dir,"generators"))
	return _this_dir

def generate_premake_project(root_workspace, mg, solution_name, out_dir, config):
	_this_dir = _import_generators()

	import generator_premake

	g = generator_premake.PremakeContext(os.path.join(_this_dir,"templates"), mg, config)
	g.run(solution_name, out_dir)

	return mg

def generate_cmake_project(root_workspace, mg, solution_name, out_dir, config):
	_this_dir = _import_generators()

	import generator_cmake

	g = generator_cmake.CmakeContext(os.path.join(_this_dir,"templates"), mg, config)
	g.run(solution_name, out_dir)

	return mg

def generate_zip_project(root_workspace, mg, solution_name, out_dir, config):
	_this_dir = _import_generators()

	import generator_zip

	g = generator_zip.ZipContext(mg, config, root_workspace)
	return g.run(solution_name, out_dir)

def create_solution(root_workspace, path, target, force):
	path = os.path.abspath(path)

	builder = target
	mg = Solution(builder, force)

	solution_name, out_dir, config = mg.generate(path)

	builder = config.query_option_value("builder")

	if builder == "vs":
		return generate_premake_project(root_workspace, mg, solution_name, out_dir, config)
	elif builder == "cmake":
		return generate_cmake_project(root_workspace, mg, solution_name, out_dir, config)
	elif builder == "zip":
		return generate_zip_project(root_workspace, mg, solution_name, out_dir, config)
	else:
		raise Exception(f"Unknown builder {builder}")
