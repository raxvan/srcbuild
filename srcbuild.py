
import os
import sys
import json
import argparse

_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_this_dir,"impl"))
sys.path.append(os.path.join(_this_dir,"tools","pytools"))

import package_graph
import package_config

def main_info(args):
	path = os.path.abspath(args.path)
	fwd = args.forward_arguments

	mg = package_graph.ModuleGraph()

	cfg = mg.configure([path])

	mg.print_info(args.pkey, args.psha, args.ppath, args.links)

	if cfg != None:
		print("-CONFIG:")
		print(package_config.get_config_ini(cfg))

def main_cmake(args):
	_this_dir = os.path.dirname(os.path.abspath(__file__))
	sys.path.append(os.path.join(_this_dir,"tools","cpptools"))

	import cpp_solution_generator

	target = args.target
	path = args.path
	force = args.force

	cpp_solution_generator.create_solution(path, target, force)

def main(args):

	acc = args.action
	if acc == "info":
		main_info(args)

	elif acc == "cmake":
		main_cmake(args)	


if __name__ == '__main__':

	#pack_database = sys.argv[1]
	#workspace = sys.argv[2]

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
	info_parser.add_argument('path', help='Path to module to inspect')
	info_parser.add_argument('forward_arguments', nargs=argparse.REMAINDER)

	#list_parser = subparsers.add_parser('list', description='Lists package information.')
	#list_parser.set_defaults(action='list')
	
	make_parser = subparsers.add_parser('cmake', description='Generate c++ solutions.')
	make_parser.set_defaults(action='cmake')
	make_parser.add_argument('-f', '--force', dest='force', action='store_true', help="Regenerate solution")
	make_parser.add_argument('target', choices=['win', 'linux'], help='Path to root module')
	make_parser.add_argument('path', help='Path to root module')
	make_parser.add_argument('forward_arguments', nargs=argparse.REMAINDER)

	args = parser.parse_args(user_arguments)
	main(args)


