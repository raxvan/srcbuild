import json
import hashlib

import package_utils

def sha256sum(filename, bufsize=128 * 1024):
	h = hashlib.sha256()
	buffer = bytearray(bufsize)
	buffer_view = memoryview(buffer)
	with open(filename, 'rb', buffering=0) as f:
		while True:
			n = f.readinto(buffer_view)
			if not n:
				break
			h.update(buffer_view[:n])
	return h.hexdigest()



def read_json(abspath):
	try:
		f = open(abspath, "r")
		if f == None:
			return None
		data = json.load(f)
		f.close()
		return data
	except FileNotFoundError:
		return None

def kwargskey_recursive(out, data):

	if isinstance(data, str):
		out.append(data)
	elif isinstance(data, list):
		r = []
		for d in data:
			kwargskey_recursive(r, d)
		out.append(",".join(r))
	elif isinstance(data, dict):
		for k,v in data.items():
			out.append(k)
			kwargskey_recursive(out, v)

	elif isinstance(data, package_utils.FileEntry):
		out.append(data.path)
	elif isinstance(data, package_utils.FolderEntry):
		out.append(data.path)
	elif isinstance(data, package_utils.PeropertyEntry):
		kwargskey_recursive(data.value)

def kwargskey(data):
	r = []
	kwargskey_recursive(r,data)
	jdata = "".join(sorted(set(r)))
	return hashlib.sha1( jdata.encode("utf-8") ).hexdigest()

