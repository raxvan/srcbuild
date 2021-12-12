
import os
import sys
import json

_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_this_dir,"impl"))
sys.path.append(os.path.join(_this_dir,"tools","pytools"))


import package_builder
import build_options

#################################################################################################
#################################################################################################

def create_default_options(opt, builder, platform):
	opt.create("builder",builder, ["vs", "vs2019", "vs2017", "vs2015", "cmake"])
	opt.create("platform",platform, ["win32","linux"])
	opt.create("cppstd","20", ["11","14","17","20"])
	
	opt.create("instruments", "true", ["true","false"])
                             
	#project defaults:
	opt.create("warnings","full", ["off","default","full"])

#################################################################################################
#################################################################################################

class CppPackageBuilder(package_builder.PackageBuilder):
	def __init__(self, abs_path_to_constructor, options):
		package_builder.PackageBuilder.__init__(self, abs_path_to_constructor, options)

		self.incl = package_builder.PackageAggregator(self, self.content, ["include"])
		self.src = package_builder.PackageAggregator(self, self.content, ["src"])


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

def run_collect(project_stack, metadata_dir):
	print("COLLECTING...")

	output = {}

	index = 0
	for k , v in project_stack.items():
		print("\t" + str(index) + ":" + v.get_name())
		index = index + 1

		data = {}

		v.collect(data)

		outfile = os.path.join(metadata_dir, v.get_name() + ".json")
		f = open(outfile, "w")
		f.write(json.dumps(data, indent=4, sort_keys=True))
		f.close()

		output[k] = data

	return output


def run_generator(projects_map, solution_name, options, output_dir):
	print("GENERATING...")

	sys.path.append(os.path.join(_this_dir,"impl","generators"))

	builder = options.get_value_or_die("builder")
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
		generator_premake.run(projects_map, solution_name, options, output_dir)
	elif generator == "cmake":
		import generator_cmake
		generator_cmake.run(projects_map, solution_name, options, output_dir)

def main(builder, platform):
	abs_entrypoint_path = os.path.abspath(sys.argv[1])
	
	opt = build_options.BuildOptions()

	create_default_options(opt, builder, platform)
	
	root_project = CppPackageBuilder(abs_entrypoint_path, opt)

	#create output directoryT
	output_dir = package_builder.get_package_output(root_project, builder, platform)

	print("OUTPUT: " + output_dir)

	medatada_dir = os.path.join(output_dir,"metadata")
	config_file = os.path.join(medatada_dir,"config.ini")
	if os.path.exists(config_file):
		opt.add_ini_config(config_file)
	elif not os.path.exists(medatada_dir):
		os.makedirs(medatada_dir)

	project_stack = {}

	run_constructors(project_stack, root_project, opt);

	opt.save_ini_config(config_file)

	run_collect(project_stack, medatada_dir)

	run_generator(project_stack, root_project, opt, output_dir)


if __name__ == '__main__':
	main(sys.argv[2],sys.argv[3])


