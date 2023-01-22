
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
	def __init__(self, platform, builder, override_config):
		package_graph.ModuleGraph.__init__(self)

		self.platform = platform
		self.builder = builder

		self.override_config = override_config

	def create_configurator(self):
		cfg = package_graph.ModuleGraph.create_configurator(self)

		cfg.option("platform",self.platform,["win32"])
		cfg.option("builder",self.builder,["msvc","cmake"])
		cfg.option("cppstd","20",["11","14","17","20"])
		cfg.option("type","exe",["exe","lib"])
		cfg.option("warnings","full",["off","default", "full"])

		cfg.option("default-visual-studio","vs2022",["vs2015","vs2017", "vs2019", "vs2022"])

		return cfg

	def create_module(self, modkey, modpath):
		return ProjectModule(modkey, modpath, self)

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

		for mk, m in all_modules.items():
			m.content = self.create_constructor(m)

			m.content.config("platform")
			m.content.config("builder")
			m.content.config("cppstd")
			m.content.config("type")
			m.content.config("warnings")

			construct_proc = m.get_proc("construct")
			if construct_proc == None:
				raise Exception(f"Could not find 'construct' function in {m.get_name()}")

			construct_proc(m.content)

			assets = list(set([p.path for p in m.content.query_files(["asset"])]))
			for a in assets:
				h,t = os.path.split(a)
				if t in assets_ini:
					raise Exception("Duplicate asset foud: " + a)
				assets_ini[t] = a

			#save json
			j = {}
			m.serialize(j)
			m.content.serialize(j)
			package_utils.save_json(j, os.path.join(metaout, m.get_name() + ".json"))

		if assets_ini:
			package_utils.save_assets_ini(assets_ini, output)

		return (root_module.get_name(), output, cfg)


def generate_win_project(path, force):
	path = os.path.abspath(path)

	mg = Solution("win32","msvc", force)

	solution_name, out_dir, config = mg.generate(path)

	_this_dir = os.path.dirname(os.path.abspath(__file__))
	sys.path.append(os.path.join(_this_dir,"generators"))

	import generator_premake

	g = generator_premake.PremakeContext(os.path.join(_this_dir,"templates"), mg, config)
	g.run(solution_name, out_dir)

	return mg

def generate_cmake_project(path, force):
	path = os.path.abspath(path)

	mg = Solution("win32","cmake", force)

	solution_name, out_dir, config = mg.generate(path)

	_this_dir = os.path.dirname(os.path.abspath(__file__))
	sys.path.append(os.path.join(_this_dir,"generators"))

	import generator_cmake

	g = generator_cmake.CmakeContext(os.path.join(_this_dir,"templates"), mg, config)
	g.run(solution_name, out_dir)

	return mg



def create_solution(path, target, force):
	if target == "win":
		return generate_win_project(path, force)
	elif target == "cmake":
		return generate_cmake_project(path, force)

	return None


