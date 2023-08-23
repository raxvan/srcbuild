
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

	cfg, root_modules = mg.configure([path])

	mg.forward_disable(root_modules)

	package_utils.display_status("DONE.")

	print("\n>MODULES:")

	mg.print_info(args.pkey, args.psha, args.ppath)
	if args.link_tree == True:
		print("LINKS:")
		mg.print_links()
	elif args.links == True:
		print("LINKS:")
		mg.print_links_shallow()


	if cfg != None:
		print(">CONFIG:")
		print(cfg._get_config_ini(mg))

def main_build(args):
	_this_dir = os.path.dirname(os.path.abspath(__file__))
	sys.path.append(os.path.join(_this_dir,"tools","solution-tools"))

	import solution_generator

	target = args.target
	path = args.path
	force = args.force

	solution_generator.create_solution(path, target, force)

def main_run(args):
	_this_dir = os.path.dirname(os.path.abspath(__file__))
	sys.path.append(os.path.join(_this_dir,"tools","pipeline-tools"))

	import pipeline_executor
	pipeline_executor.run_pipeline(args.path, args.reconfigure)


def main(args):

	acc = args.action

	if acc == "info":
		main_info(args)

	elif acc == "build":
		main_build(args)

	elif acc == "run":
		main_run(args);



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

	#list_parser = subparsers.add_parser('list', description='Lists package information.')
	#list_parser.set_defaults(action='list')

	build_parser = subparsers.add_parser('build', description='Generate c++ solutions.')
	build_parser.set_defaults(action='build')
	build_parser.add_argument('-f', '--force', dest='force', action='store_true', help="Regenerate config.ini from build folder.")
	build_parser.add_argument('target', choices=['vs', 'cmake', 'zip'], help='Which builder to use.')
	build_parser.add_argument('path', help='Path to root module')
	build_parser.add_argument('forward_arguments', nargs=argparse.REMAINDER)

	run_parser = subparsers.add_parser('run', description='Run tasks')
	run_parser.set_defaults(action='run')
	run_parser.add_argument('-r', '--reconfigure', dest='reconfigure', action='store_true', help="Reconfigure.")
	run_parser.add_argument('path', help='Path to root module')
	#run_parser.add_argument('forward_arguments', nargs=argparse.REMAINDER)


	args = parser.parse_args(user_arguments)
	if hasattr(args, 'action'):
		main(args)
	else:
		print("Missing operation:")
		for k,_ in subparsers.choices.items():
			print("\t-> " + k)
