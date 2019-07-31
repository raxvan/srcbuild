
import os

def files_equal(file_path_a,file_path_b):
	import sys
	if not os.path.exists(file_path_a):
		print("FAILURE\nMissing file:" + file_path_a)
		sys.exit(-1)

	if not os.path.exists(file_path_b):
		print("FAILURE\nMissing file:" + file_path_b)
		sys.exit(-1)

	_af = os.path.abspath(file_path_a)
	_bf = os.path.abspath(file_path_b)
	import filecmp
	if filecmp.cmp(_af, _bf):
		print("files equal:SUCCESS\n	" + _af + "\n	" + _bf)
		return;

	print("FAILURE\nFiles are not equal\n" + _af + "\n" + _bf)
	sys.exit(-1)


def rmdir(dir_path):
	abs_dir = os.path.abspath(dir_path)
	message = "Removing [" + abs_dir + "]"

	if not os.path.exists(abs_dir):
		print(message + " ... not found ...")
		return

	print(message)

	for path in os.listdir(abs_dir):
		dpath = os.path.join(abs_dir,os.fsdecode(path))
		#print(dpath)
		if os.path.isfile(dpath):
			os.remove(dpath)
			continue
		if os.path.isdir(dpath):
			rmdir(dpath)
			continue

	os.rmdir(abs_dir)
