
import os
import sys
import importlib
import solution


def _load_module(abs_path_to_pyfile, load_location):
	ll = "builder." + load_location
	spec = importlib.util.spec_from_file_location(ll, abs_path_to_pyfile)
	module_context = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module_context)
	return module_context

def _add_generators_import():
	_gdir = os.path.dirname(os.path.abspath(__file__))
	_gdir = os.path.join(_gdir,"generators")
	_gimpldir = os.path.join(_gdir, "impl")
	sys.path.append(_gdir)
	sys.path.append(_gimpldir)
	return _gdir

def discover_buidlers():
	_generators_dir = _add_generators_import()
	return {
		"debug" : os.path.join(_generators_dir, "generator_debug.py"),
		"stamps" : os.path.join(_generators_dir, "generator_stamps.py"),
		"cmake" : os.path.join(_generators_dir, "generator_cmake.py"),
		"premake" : os.path.join(_generators_dir, "generator_premake.py"),
	}

def import_builder_stack(root_workspace, builder_stack):
	builders = discover_buidlers()
	result = {}

	priority = 0
	for b in builder_stack:
		bpath = builders.get(b, None)
		if bpath == None:
			raise Exception(f"Could not find builder {b}")

		builder_code = _load_module(bpath, b)
		if hasattr(builder_code, "create"):
			configure_func = getattr(builder_code, "create")
			result[b] = configure_func(root_workspace, priority)

		else:
			result[b] = builder_code

		print(">" + str(priority).rjust(2) + f":loaded {b} generator")
		priority += 1

	return [result[b] for b in builder_stack]



def build(root_workspace, path, output, force, builder_stack):
	builders = import_builder_stack(root_workspace, builder_stack)

	sol = solution.Solution(builders)

	sol.construct_from_path(os.path.abspath(path), output, force)

	return sol.output