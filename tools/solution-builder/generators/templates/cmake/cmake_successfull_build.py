
import os
import sys
import shutil
import json


_this_dir = os.path.dirname(os.path.abspath(__file__))
_solution_output = os.path.dirname(_this_dir)

_message_header = " >>> "

project_type = sys.argv[1]
project_name = sys.argv[2]
active_configuration = sys.argv[3] #Debug, Release
active_architecture = sys.argv[4]
active_compiler = sys.argv[5]
abs_binary_file = sys.argv[6]


########################################################################################

def main():
	perform_binary_copy()
	write_stamps()

########################################################################################

def perform_binary_copy():
	print(f"{_message_header}Running post build for [{project_name}] ({project_type})...")
	binary_input = abs_binary_file
	output_filename = os.path.basename(binary_input)

	print(f"{_message_header}Binary (main): {os.path.relpath(binary_input, _solution_output)}")

	if project_type == "exe" and active_compiler != "MSVC":
		binary_output = os.path.join(_solution_output,"bin", active_configuration)

		if not os.path.exists(binary_output):
			os.makedirs(binary_output)

		binary_output = os.path.join(binary_output, output_filename)

		shutil.copyfile(binary_input, binary_output)
		
		print(f"{_message_header}Binary (aux): {os.path.relpath(binary_output, _solution_output)}")


def write_stamps():
	if not project_type == "exe":
		return

	stamp_file = os.path.join(_solution_output, "make_stamp.py")
	if not os.path.exists(stamp_file):
		return
	sys.path.append(_solution_output)
	import make_stamp

	config = active_configuration.lower()
	arch = active_architecture.lower()
	builder = active_compiler.lower()

	stamp = f"cmake-{builder}-{config}-{arch}"
	outfile = make_stamp.make_stamp(stamp)
	print(f"{_message_header} Stamp:{stamp} -> {outfile}")

main()