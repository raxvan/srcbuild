import os
import sys
import hashlib

_this_dir = os.path.dirname(os.path.abspath(__file__))

def compute_sha512(file_path):
	
	hash_sha512 = hashlib.sha512()
	with open(file_path, 'rb') as file:
		for chunk in iter(lambda: file.read(4096), b""):
			hash_sha512.update(chunk)
	return hash_sha512.hexdigest()

def combine_hashes_and_compute_final_sha512(file_paths):
	
	combined_hash_string = ''
	for file_path in file_paths:
		file_hash = compute_sha512(file_path)
		combined_hash_string += file_hash
	
	final_sha512 = hashlib.sha512(combined_hash_string.encode()).hexdigest()
	return final_sha512

def get_sha_from_stamps(stampfile):
	combined_hash_string = ''

	stampfile = os.path.join(_this_dir, stampfile);

	with open(stampfile, 'r') as file:
		file_count = int(file.readline().rstrip("\n"))
		index = 1
		
		line = file.readline().rstrip("\n")
		while line:
			file_path = os.path.abspath(os.path.join(_this_dir, line))
			print(f"{index}/{file_count} | ".rjust(12) + file_path)
			index += 1

			combined_hash_string += compute_sha512(file_path)

			line = file.readline().rstrip("\n")

	final_sha512 = hashlib.sha512(combined_hash_string.encode()).hexdigest()
	return final_sha512

def write_stamp(outdir, sha, value):
	outdir = os.path.join(_this_dir, outdir)
	if not os.path.exists(outdir):
		os.makedirs(outdir)

	abs_path = os.path.join(outdir, sha)
	f = open(abs_path, "a+")
	f.write(value)
	f.write("\n")
	f.close()

infile = "./.srcbuild/stamps.txt"
outdir = "./stamps"
value = sys.argv[1]

sha = get_sha_from_stamps(infile)
write_stamp(outdir, sha, value)
print(f"generated: {outdir}/{sha}")

