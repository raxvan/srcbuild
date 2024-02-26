
import os
import sys
import git

import package_utils
import generator_utils

clrs = package_utils.Colors

class DebugContext(generator_utils.GeneratorInterface):
	def __init__(self):
		pass

	def __str__(self):
		return "debug"

	def configure(self, cfg):
		print(f"{clrs.LIGHT_RED}[DEBUG]{clrs.END} <configure>")

	def prebuild(self, solution):
		print(f"{clrs.LIGHT_RED}[DEBUG]{clrs.END} <prebuild>")

	def accept(self, solution, module):
		print(f"{clrs.LIGHT_RED}[DEBUG]{clrs.END} <accept:{module.get_name()}>")
		return True
		
	def build(self, solution, module, jout):
		#called only if accept() returns true
		print(f"{clrs.LIGHT_RED}[DEBUG]{clrs.END} <build:{module.get_name()}>")

	def postbuild(self, solution):
		#called regardless of accept() result
		print(f"{clrs.LIGHT_RED}[DEBUG]{clrs.END} <postbuild>")

			

def create(workspace, priority):
	print(f"{clrs.LIGHT_RED}[DEBUG]{clrs.END} <{priority}> creating debug context for {workspace} ")
	return DebugContext()
