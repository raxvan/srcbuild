
def read_text_file(abs_file_path):
	try:
		f = open(abs_file_path,"r")
		content = f.read()
		f.close()
		return content
	except:
		return None

def save_if_changed(abs_file_path, content):
	if read_text_file(abs_file_path) != content:
		f = open(abs_file_path,"w")
		f.write(content)
		f.close()
		return True
	return False



class GeneratorInterface():
	def __init__(self):
		pass

	def __str__(self):
		return "none"

	def configure(self, cfg):
		pass

	def prebuild(self, solution):
		pass

	def accept(self, solution, module):
		return True
		
	def build(self, solution, module, jout):
		pass

	def postbuild(self, solution):
		pass
