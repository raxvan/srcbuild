
import os
import sys
import shutil
import json


_this_dir = os.path.dirname(os.path.abspath(__file__))

_message_header = " >>> "

active_configuration = sys.argv[1] #Debug, Release
abs_project_path = sys.argv[2]
abs_bniary_path = sys.argv[3]

########################################################################################

abs_bniary_path = os.path.abspath(abs_bniary_path)

########################################################################################

def main():
	perform_binary_copy()

########################################################################################

def perform_binary_copy():
	binary_input = abs_bniary_path
	output_filename = os.path.basename(binary_input)
	binary_output = os.path.join(_this_dir,"bin", active_configuration)

	if not os.path.exists(binary_output):
		os.makedirs(binary_output)

	binary_output = os.path.join(binary_output, output_filename)

	shutil.copyfile(binary_input, binary_output)
	
	binary_input = os.path.relpath(binary_input, _this_dir)
	binary_output = os.path.relpath(binary_output, _this_dir)
	print(f"{_message_header}Binary (main): {binary_input}")
	print(f"{_message_header}Binary (aux): {binary_output}")


main()