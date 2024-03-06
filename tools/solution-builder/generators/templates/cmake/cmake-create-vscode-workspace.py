import os
import json

_this_dir = os.path.dirname(os.path.abspath(__file__))
_, _folder_name = os.path.split(_this_dir)

workspace = os.path.abspath(os.path.join(_this_dir,"..","..","..","..",".."))
vscode_dir = os.path.join(workspace,".vscode")

if not os.path.exists(vscode_dir):
	os.makedirs(vscode_dir)

#--------------------------------------------------------------------------------------------------------------------------------

class JsonContent():
	def __init__(self, path, default_content):
		self.path = path
		self.data = default_content
		if(os.path.exists(path)):
			f = open(path, "r")
			self.data = json.load(f)
			f.close()

	def save(self):
		f = open(self.path, "w")
		f.write(json.dumps(self.data, indent=4))
		f.close()

def project_path(relative_item):
	p = os.path.relpath(_this_dir, workspace)
	if relative_item != None:
		p = os.path.join(p, relative_item)
	return "${workspaceFolder}/" + p.replace("\\","/")


#--------------------------------------------------------------------------------------------------------------------------------


def get_build_debug_task(label):
	return {
		"label": label,
		"type": "shell",
		"command": "./cmake_build_with_config.sh",
		"windows" : {
			"command": "./cmake_build_with_config.bat"
		},
		"options": {
			"cwd": project_path(None),
		},
		"args" : [
			"Debug"
		],
		"group": {
			"kind": "build",
			"isDefault": True
		},
		"presentation": {
			"echo": False,
			"reveal": "always",
			"focus": False,
			"panel": "dedicated"
		}
	}

def get_build_release_task(label):
	return {
		"label": label,
		"type": "shell",
		"command": "./cmake_build_with_config.sh",
		"windows" : {
			"command": "./cmake_build_with_config.bat"
		},
		"options": {
			"cwd": project_path(None),
		},
		"args" : [
			"Release"
		],
		"group": "build",
		"presentation": {
			"echo": False,
			"reveal": "always",
			"focus": False,
			"panel": "dedicated"
		}
	}

def get_launch_config_win32_debug(name, exename):
	return {
		"name": name,
		"type": "cppvsdbg",
		"request": "launch",
		"program": project_path(f"bin/Debug/{exename}.exe"),
		"args": [],
		"stopAtEntry": False,
		"cwd": project_path(None),
		"environment": [],
		"externalConsole": False,
		"preLaunchTask": "",
		"windows": {
			"MIMode": "cppvsdbg"
		}
	}

def get_launch_config_linux_debug(name, exename):
	return {
		"name": name,
		"type": "cppdbg",
		"request": "launch",
		"program": project_path(f"bin/Debug/{exename}"),
		"args": [],
		"stopAtEntry": False,
		"cwd": project_path(None),
		"environment": [],
		"externalConsole": False,
		"MIMode": "gdb",
		"setupCommands": [
			{
				"description": "Enable pretty-printing for gdb",
				"text": "-enable-pretty-printing",
				"ignoreFailures": True
			}
		],
		"preLaunchTask": "",
		"miDebuggerArgs": "",
		"linux": {
			"miDebuggerPath": "/usr/bin/gdb"
		}
	}

def join_items(base_list, replace_map, item_name_key):
	newlist = []
	for i in base_list:
		name = i[item_name_key]
		r = replace_map.get(name, None)
		if r != None:
			newlist.append(r)
			del replace_map[name]
		else:
			newlist.append(i)

	for _, v in replace_map.items():
		newlist.append(v)

	return newlist


def scan_modules():
	json_map = {}
	folder_path = os.path.join(_this_dir,"modules")
	for filename in os.listdir(folder_path):
		if filename.endswith(".json"):
			full_path = os.path.join(folder_path, filename)

			# Read the json file and load its content
			file = open(full_path, 'r')
			try:
				content = json.load(file)
				json_map[filename.replace(".json","")] = content
			except json.JSONDecodeError:
				print(f"Error decoding JSON from {filename}. Skipping.")
			file.close()

	return json_map

def get_configurations():
	configs = []
	jf = scan_modules()
	for k,v in jf.items():
		t = v.get('content',{}).get("props",{}).get('exe-name',None)
		if t == None:
			continue

		t = t['data']
		configs.append(t)

	return configs

#--------------------------------------------------------------------------------------------------------------------------------

def update_tasks(tasks):
	tlist = tasks["tasks"]

	debug_label = f"[debug] {_folder_name} srcbuild"
	release_label = f"[release] {_folder_name} srcbuild"

	rmap = {}
	rmap[debug_label] = get_build_debug_task(debug_label);
	rmap[get_build_release_task] = get_build_release_task(release_label);

	tasks["tasks"] = join_items(tlist, rmap, "label")


def update_launch_configs(launchdata):
	tlist = launchdata["configurations"]

	cmap = {}
	for c in get_configurations():
		n = f"[win32-dbg] {c}"
		cmap[n] = get_launch_config_win32_debug(n, c)
		n = f"[linux-dbg] {c}"
		cmap[n] = get_launch_config_linux_debug(n, c)

	launchdata["configurations"] = join_items(tlist, cmap, "name")


default_tasks = {
	"version": "2.0.0",
	"tasks": []
}
tasks = JsonContent(os.path.join(vscode_dir,"tasks.json"), default_tasks)
update_tasks(tasks.data)
tasks.save();


default_launch = {
	"version": "0.2.0",
	"configurations": []
}
launch = JsonContent(os.path.join(vscode_dir,"launch.json"), default_launch)
update_launch_configs(launch.data)
launch.save();


