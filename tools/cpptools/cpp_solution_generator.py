
import os
import sys

import package_graph
import package_config
import package_constructor
import package_utils

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
		cfg.option("cppstd","17",["11","14","17","20"])
		cfg.option("type","exe",["exe","slib"])
		cfg.option("warnings","full",["off","default", "full"])

		return cfg

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
			pc = self.create_constructor(m, cfg)

			root_module.run_proc("construct", pc)

			j = {}
			pc.serialize(j)
			package_utils.save_json(j, os.path.join(metaout,m.get_name() + ".json"))


def generate_win_project(path, force):
	path = os.path.abspath(path)

	mg = Solution("win32","msvc", force)
	mg.generate(path)


def create_solution(path, target, force):
	if target == "win":
		generate_win_project(path, force)


"""
#################################################################################################
#################################################################################################

def construct_package(ctx):

	iname = ctx.get_name().upper().replace("-","_") + "_INSTRUMENTS"
	iglobal = ctx.options.get_value_or_die("instruments")
	instruments_enabled = ctx.options.get(iname, iglobal)

	#inherit options
	ctx.prop("warnings", ctx.options.get("warnings")).tag("private")

	platform_define_map = {
		"win32" : "BUILD_PLATFORM_WIN32",
		"linux" : "BUILD_PLATFORM_LINUX",
	}

	if instruments_enabled == "true":
		ctx.prop(iname).tag("define").tag("global")

	if iglobal == "true":
		ctx.prop("INSTRUMENTS_ENABLED").tag("define").tag("global")

	ctx.prop(platform_define_map[ctx.options.get("platform")]).tag("define").tag("private")

	package_builder.construct_package(ctx)


def run_constructors(project_stack, root_project, opt):
	print("SCANNING...")
	
	project_stack[root_project.get_name()] = root_project
	construction_queue = [root_project]
	index = 0
	while len(construction_queue) > 0:

		print("\t" + str(index) + ":" + ",".join([c.get_name() for c in construction_queue]))
		index = index + 1
		for c in construction_queue:
			construct_package(c)

		next_queue = []
		for c in construction_queue:
			for _dependency in c.content.dependency:
				if not _dependency.get_name() in project_stack:
					builder = CppPackageBuilder(_dependency.path.get_abs_path(), opt)

					project_stack[builder.get_name()] = builder

					next_queue.append(builder)

		next_queue.sort(key=package_builder.get_package_priority)

		construction_queue = next_queue

def run_collect(project_stack, medatada_dir):
	print("COLLECTING...")

	output = {}

	index = 0
	for k , v in project_stack.items():
		print("\t" + str(index) + ":" + v.get_name())
		index = index + 1

		data = {}

		v.collect(data)

		outfile = os.path.join(medatada_dir, v.get_name() + ".json")
		f = open(outfile, "w")
		f.write(json.dumps(data, indent=4, sort_keys=True))
		f.close()

		output[k] = data

	return output


def run_generator(projects_graph, solution_name, solution_config, output_dir):
	print("GENERATING...")

	sys.path.append(os.path.join(_this_dir,"impl","generators"))

	builder = solution_config.option("builder")
	generator_map = {
		"vs" : "premake",
		"vs2019" : "premake",
		"vs2017" : "premake",
		"vs2015" : "premake",
		"cmake" : "cmake",
	}
	generator = generator_map[builder]

	if generator == "premake":
		import generator_premake
		generator_premake.run(projects_graph, solution_name, solution_config, output_dir)
	elif generator == "cmake":
		import generator_cmake
		generator_cmake.run(projects_graph, solution_name, solution_config, output_dir)


class CppConfigurator(package_config.Configurator):
	def __init__(self, od):
		package_config.Configurator.__init__(self)

		self.outdir = od
		self.medatada_dir = os.path.join(self.outdir,"metadata")
		self.config_file = os.path.join(self.medatada_dir,"config.ini")

		if os.path.exists(self.config_file):
			self._add_ini_config(self.config_file)
		elif not os.path.exists(self.medatada_dir):
			os.makedirs(self.medatada_dir)

class SolutionConfig(package_config.SolutionConfig):
	def __init__(self, base_config):
		package_config.SolutionConfig.__init__(self)
		self.medatada_dir = base_config.medatada_dir
		self.projects_dir = base_config.outdir


def _get_package_output(package, builder, platform):
	pak_dirname = builder + "-" + platform + "-" + package.get_name()
	if hasattr(package.pipeline, 'output'):
		return os.path.abspath(os.path.join(package.pipeline.output(package),pak_dirname))
	else:
		return os.path.abspath(os.path.join(package._abs_pipeline_dir,"build",pak_dirname))

class ProjectTree(package_graph.ModuleGraph):
	def __init__(self, b, p):
		package_graph.ModuleGraph.__init__(self)

		self.builder = b
		self.platform = p

	def create_configurator(self, root_modules):
		outdir = _get_package_output(root_modules[0], self.builder, self.platform)

		c = CppConfigurator(outdir)
		c.option("builder",self.builder, ["vs", "vs2019", "vs2017", "vs2015", "cmake"])
		c.option("platform",self.platform, ["win32","linux"])
		c.option("cppstd","20", ["11","14","17","20"])

		#c.component("instruments", False)

		#project defaults:
		#c.option("warnings","full", ["off","default","full"])

		return c

	def create_final_configuration(self, configurator):
		sc = SolutionConfig(configurator)
		configurator.sync(sc, configurator.config_file)
		return sc


def old_main(builder, platform):
	abs_entrypoint_path = os.path.abspath(sys.argv[1])

	t = ProjectTree(builder, platform)

	config = t.load([abs_entrypoint_path])
	
	modules = t.construct_all(config)
	
	for m in modules:
		sm = m.serialize()
		outfile = os.path.join(config.medatada_dir, m.get_name() + ".json")
		f = open(outfile, "w")
		f.write(json.dumps(sm, indent=4, sort_keys=True))
		f.close()

	solution_name = t.get_module_with_path(abs_entrypoint_path).get_name()

	run_generator(t, solution_name, config, config.projects_dir)
	
"""
