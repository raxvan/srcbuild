
import os
import sys
import json
import argparse

_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_this_dir,"impl"))
sys.path.append(os.path.join(_this_dir,"tools","pytools"))

import package_graph
import package_config
import package_utils

def main_info(args):
	path = os.path.abspath(args.path)
	fwd = args.forward_arguments

	mg = package_graph.ModuleGraph()

	root_modules = mg.configure([path])

	mg.build(root_modules)

	mg.printer.print_status("DONE.")

	print("\n>MODULES:")

	mg.print_info(args.pkey, args.psha, args.ppath)
	if args.link_tree == True:
		print("LINKS:")
		mg.print_links()
	elif args.links == True:
		print("LINKS:")
		mg.print_links_shallow()


	if mg.configurator != None:
		print(">CONFIG:")
		print(mg.configurator._get_config_ini(mg))

def main_build(args):
	_this_dir = os.path.dirname(os.path.abspath(__file__))
	sys.path.append(os.path.join(_this_dir,"tools","solution-builder"))

	path = args.path
	force = args.force

	builder_list = args.builders
	
	import solution_builder
	solution_builder.build("/wspace/workspace", path, force, builder_list)

def main_version(args):
	_this_dir = os.path.dirname(os.path.abspath(__file__))
	sys.path.append(os.path.join(_this_dir,"tools","versioning"))

	path = args.path

	import package_versioning

	v = package_versioning.get_version(path)
	print(v)

def main(args):
	acc = args.action

	if acc == "build":
		main_build(args)
	elif acc == "version":
		main_version(args)
	elif acc == "info":
		main_info(args)

	

if __name__ == '__main__':
	user_arguments = sys.argv[1:]

	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(description='Actions:')

	#
	info_parser = subparsers.add_parser('info', description='Show Information on a module')
	info_parser.set_defaults(action='info')
	info_parser.add_argument('-k', '--key', dest='pkey', action='store_true', help="Print module key.")
	info_parser.add_argument('-s', '--sha', dest='psha', action='store_true', help="Print module sha.")
	info_parser.add_argument('-p', '--path', dest='ppath', action='store_true', help="Print module absolute path.")
	info_parser.add_argument('-l', '--links', dest='links', action='store_true', help="Print Links.")
	info_parser.add_argument('-rl', '--rlinks', dest='link_tree', action='store_true', help="Print Links recursive.")
	info_parser.add_argument('path', help='Path to module to inspect')
	info_parser.add_argument('forward_arguments', nargs=argparse.REMAINDER)

	build_parser = subparsers.add_parser('build', description='Runs a builder bundle on module')
	build_parser.set_defaults(action='build')
	build_parser.add_argument('-f', '--force', dest='force', action='store_true', help="Regenerate config.ini from build folder.")
	build_parser.add_argument('path', help='Path to root module')
	build_parser.add_argument('builders', nargs='+', help='List of builders separated by spaces, in order!')

	version_parser = subparsers.add_parser('version', description='Version tool for packages')
	version_parser.set_defaults(action='version')
	version_parser.add_argument('path', help='Path to root module')

	args = parser.parse_args(user_arguments)
	if hasattr(args, 'action'):
		main(args)
	else:
		print("Missing operation:")
		for k,_ in subparsers.choices.items():
			print("\t-> " + k)
