
import os
import sys
import hashlib

import package_constructor
import package_utils

class PipelineConstructor(package_constructor.PackageConstructor):
	def __init__(self, graph, target_module):
		package_constructor.PackageConstructor.__init__(self, graph, target_module)
		self.builder_names = []

	def builder(self, func):
		self._graph.add_builder(self._module, func.__name__, func)
		self.builder_names.append(func.__name__)

	def run(self, build_name, **kwargs):
		return self._graph.run_builder(build_name)

	def serialize(self, data):
		package_constructor.PackageConstructor.serialize(self,data)
		data['builders'] = sorted(self.builder_names)

	def depends(self, *args):
		for a in args:
			if isinstance(a, package_utils.FileEntry):
				self._add_path_internal(a.path, package_utils.FileEntry, None)
				self._files.append(a.path)
			elif isinstance(a, package_utils.FolderEntry):
				self._add_path_internal(a.path, package_utils.FolderEntry, None)
				self._folders.append(a.path)
			elif isinstance(a, str):
				if not os.path.exists(a):
					raise Exception(f"Dependency {a} could not be found.")
					
				if os.path.isfile(a):
					self._add_path_internal(a, package_utils.FileEntry, None)
					self._files.append(a)
				elif os.path.isdir(a):
					self._add_path_internal(a, package_utils.FolderEntry, None)
					self._folders.append(a)
			else:
				raise Exception("Unknown type:" + str(a))

	def dirty(self, *args):
		for a in args:
			if isinstance(a, package_utils.FileEntry):
				self._set_dirty(a.path)
			elif isinstance(a, str):
				self._set_dirty(a)
			else:
				raise Exception("Unknown type:" + str(a))

	def _set_dirty(self, f):
		self._graph.set_dirty(f)

#--------------------------------------------------------------------------------------------------------------------------------

class Pipeline(PipelineConstructor):
	def __init__(self, graph, target_module):
		PipelineConstructor.__init__(self, graph, target_module)
		self.internal_folder = None

	def _get_exec_file(self, path_to_file):
		script = None

		if isinstance(path_to_file, str):
			script = self.file(path_to_file)
		elif isinstance(path_to_file, package_utils.FileEntry):
			script = path_to_file
			self._paths[path_to_file.path] = path_to_file
			self._files.append(path_to_file.path)
		else:
			raise Exception("Invalid script...")

		return script

	def _run_command_sync(self, cmd):
		joined_cmd = " ".join(cmd)
		hcmd = hashlib.sha256(joined_cmd.encode("utf-8") ).hexdigest()
		self.assign(hcmd, cmd)

		import subprocess
		result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		self.assign(hcmd + "-returncode", result.returncode)
		
		log = f"CMD:\n{joined_cmd}"
		log = log + "\nSTDOUT:\n" + result.stdout.decode("utf-8")
		log = log + "\nSTDERR:\n" + result.stderr.decode("utf-8")
		logloc = self._graph.push_log_file(hcmd, log)
		if(result.returncode != 0):
			raise Exception("exec_shell_sync failed, check " + logloc)

	def exec_shell_sync(self, script_info, args = []):
		script = self._get_exec_file(script_info)
		cmd = ["/bin/bash", script.path] + args
		self._run_command_sync(cmd)

	def exec_binary_sync(self, executable_info, args = []):
		exe = self._get_exec_file(executable_info)
		cmd = [exe.path] + args
		self._run_command_sync(cmd)

	def exec_cmd_sync(self, cmd):
		self._run_command_sync(cmd)

	def exec_builder(self, builder_name, **kwargs):
		return self._graph.spawn_builder(self._module, builder_name, kwargs)

	def clean_folder(self, path_to_folder):
		for f in os.listdir(path_to_folder):
			abspath = os.path.join(path_to_folder, f)
			try:
				if os.path.isfile(abspath) or os.path.islink(abspath):
					os.unlink(abspath)
			except:
				continue
		

