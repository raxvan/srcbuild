
import os
import hashlib

def _split_tags(tags_str):
	return [t.strip() for t in tags_str.replace(" ",",").split(",")]

def _parse_key_value(left, right):
	tags = _split_tags(left)
	name = right.strip()
	return (tags, name)

def _parse_key(name):
	if "|" in name:
		left, right = name.split("|")
		return _parse_key_value(left,right)
	elif ":" in name:
		left, right = name.split(":")
		return _parse_key_value(left,right)
	else:
		return (None,name)

def _path_to_modkey(abs_path_to_module):
	return hashlib.sha256(abs_path_to_module.lower().encode('utf-8')).hexdigest()

def save_json(j, abs_output_file):
	import json
	with open(abs_output_file, "w") as outfile:
		outfile.write(json.dumps(j, indent=1, sort_keys=True))

def save_ini_map(data, abs_file_name):
	with open(abs_file_name, "w") as outfile:
		for k,v in data.items():
			outfile.write(f"{k}={v}\n")

#--------------------------------------------------------------------------------------------------------------------------------

def make_tags(utag):
	if utag != None:
		if isinstance(utag, str):
			return set([utag])
		elif isinstance(utag, list):
			return set(utag)
		elif isinstance(utag, set):
			return utag
	return set()

class PackageEntry():
	def __init__(self, utag = None):
		self.tags = make_tags(utag)

	def packed_tags(self):
		lt = len(self.tags)
		if lt > 1:
			return list(self.tags)
		elif lt == 1:
			return next(iter(self.tags))
		return []

	def join_tags(self, utag):
		if utag != None:
			if isinstance(utag, str):
				self.tags.add(utag)
			elif isinstance(utag, list):
				self.tags = self.tags.union(set(utag))
			elif isinstance(utag, set):
				self.tags = self.tags.union(utag)
		return self

	def get_joined_tags_string(self):
		return ",".join(list(self.tags).sorted())

	def get_tags_str(self, suffix):
		if self.tags:
			return suffix + "[" + ",".join(list(self.tags)) + "]"
		return ""

	def serializeWithValue(self, value):
		if self.tags:
			return {
				"val" : value,
				"tag" : self.packed_tags()
			}
		else:
			return value

def deserializeValueTagsPair(svalue):
	if isinstance(svalue, dict):
		return svalue['val'], svalue['tag']
	
	return svalue['val'], None
#--------------------------------------------------------------------------------------------------------------------------------

class PathEntry(PackageEntry):
	def __init__(self, path, tags):
		PackageEntry.__init__(self, tags)
		self.path = path

	def get_path_relative_to(self, p):
		return os.path.relpath(self.get_abs_path(),p)

	def serialize(self):
		return self.serializeWithValue(self.path)

#--------------------------------------------------------------------------------------------------------------------------------

class ModuleLink(PathEntry):
	def __init__(self, abspath, tags):
		PathEntry.__init__(self, abspath, tags)

		self.module = None #module instance

	def enable(self):
		self.module.enabled = True

	def disable(self):
		self.module.enabled = False

	def enabled(self):
		return self.module.enabled;

#--------------------------------------------------------------------------------------------------------------------------------

class PeropertyEntry(PackageEntry):
	def __init__(self, value, tags):
		PackageEntry.__init__(self, tags)

		self.value = value

	def serialize(self):
		return self.serializeWithValue(self.value)

def deserializePeropertyEntry(svalue):
	v, t = deserializeValueTagsPair(svalue)
	return PeropertyEntry(v, t)


#--------------------------------------------------------------------------------------------------------------------------------

class FileEntry(PathEntry):
	def __init__(self, path, tags):
		PathEntry.__init__(self, path, tags)
		

class FolderEntry(PathEntry):
	def __init__(self, path, tags):
		PathEntry.__init__(self, path, tags)

def deserializeFileEntry(svalue):
	v, t = deserializeValueTagsPair(svalue)
	return FileEntry(v, t)

def deserializeFolderEntry(svalue):
	v, t = deserializeValueTagsPair(svalue)
	return FolderEntry(v, t)

#--------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------


class Colors:
	""" ANSI color codes """
	BLACK = "\033[0;30m"
	RED = "\033[0;31m"
	GREEN = "\033[0;32m"
	BROWN = "\033[0;33m"
	BLUE = "\033[0;34m"
	PURPLE = "\033[0;35m"
	CYAN = "\033[0;36m"
	LIGHT_GRAY = "\033[0;37m"
	DARK_GRAY = "\033[1;30m"
	LIGHT_RED = "\033[1;31m"
	LIGHT_GREEN = "\033[1;32m"
	YELLOW = "\033[1;33m"
	LIGHT_BLUE = "\033[1;34m"
	LIGHT_PURPLE = "\033[1;35m"
	LIGHT_CYAN = "\033[1;36m"
	LIGHT_WHITE = "\033[1;37m"
	BOLD = "\033[1m"
	FAINT = "\033[2m"
	ITALIC = "\033[3m"
	UNDERLINE = "\033[4m"
	BLINK = "\033[5m"
	NEGATIVE = "\033[7m"
	CROSSED = "\033[9m"
	END = "\033[0m"
	# cancel SGR codes if we don't write to a terminal
	if not __import__("sys").stdout.isatty():
		for _ in dir():
			if isinstance(_, str) and _[0] != "_":
				locals()[_] = ""
	else:
		# set Windows console in VT mode
		if __import__("platform").system() == "Windows":
			kernel32 = __import__("ctypes").windll.kernel32
			kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
			del kernel32

#--------------------------------------------------------------------------------------------------------------------------------

class EmptyPackagePrinter():
	def __init__(self):
		pass

	def print_key_value(self, message, package_path):
		pass

	def print_header(self, status_msg):
		pass

	def print_status(self, status_msg):
		pass


	def print_progress(self, progress_msg):
		pass

#--------------------------------------------------------------------------------------------------------------------------------

class LoggingPackagePrinter():
	def __init__(self, default_output):
		self.output = default_output

	def print_key_value(self, message, package_path):
		if self.output != None:
			self.output.append(f"{message}={package_path}")

	def print_header(self, status_msg):
		if self.output != None:
			self.output.append(status_msg)

	def print_status(self, status_msg):
		if self.output != None:
			self.output.append(status_msg)


	def print_progress(self, progress_msg):
		if self.output != None:
			self.output.append(progress_msg)

	def print_failed_progress(self, progress_msg, fail_msg):
		if self.output != None:
			self.output.append(progress_msg + fail_msg)

#--------------------------------------------------------------------------------------------------------------------------------

class DefaultPackagePrinter():
	def __init__(self):
		pass

	def print_key_value(self, message, package_path):
		print(f"{message}={package_path}")
		pass

	def print_header(self, status_msg):
		print(Colors.DARK_GRAY + "-" * 32 + "\n" + Colors.LIGHT_GREEN + status_msg + Colors.END)
		pass

	def print_status(self, status_msg):
		print(f"{Colors.YELLOW}{status_msg}{Colors.END}" )


	def print_progress(self, progress_msg):
		print(f"{Colors.BOLD}{progress_msg}{Colors.END}" )

	def print_failed_progress(self, progress_msg, fail_msg):
		print(f"{Colors.LIGHT_GRAY}{progress_msg}{Colors.END}{Colors.LIGHT_RED}{fail_msg}{Colors.END}" )


