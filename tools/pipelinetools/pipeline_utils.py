import json
import hashlib

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