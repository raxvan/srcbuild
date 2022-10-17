
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
		cfg.option("builder",self.builder,["msvc","make"])
		cfg.option("cppstd","17",["11","14","17","20"])
		cfg.option("type","exe",["exe","lib"])
		cfg.option("warnings","full",["off","default", "full"])

		return cfg

	def create_module(self, modkey, modpath):
		return ProjectModule(modkey, modpath, self)

	def generate(self, path):
		root_module = self.load_shallow([path])[0]

		output = os.path.join(root_module.get_package_dir(),"..","build",self.builder + "-" + root_module.get_name().replace(".","_").replace("-","_").lower())
		output = os.path.abspath(output)
		metaout = os.path.join(output, "modules")
		if not os.path.exists(metaout):
			os.makedirs(metaout)

		cfg = self.configure()

		self.sync_config(os.path.join(output, "config.ini"), self.override_config)

		self.forward_disable([root_module])

		all_modules = self.modules

		for mk, m in all_modules.items():
			m.content = self.create_constructor(m, cfg)

			m.content.config("platform")
			m.content.config("builder")
			m.content.config("cppstd")
			m.content.config("type")
			m.content.config("warnings")

			m.run_proc("construct", m.content)

			#save json
			j = {}
			m.content.serialize(j)
			package_utils.save_json(j, os.path.join(metaout,m.get_name() + ".json"))


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



def create_solution(path, target, force):
	if target == "win":
		generate_win_project(path, force)


