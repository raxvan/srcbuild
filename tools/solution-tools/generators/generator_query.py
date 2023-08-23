
import os

def make_relative_path(of_file, where_is_the_project):
	return os.path.relpath(of_file, where_is_the_project)

def get_dependency_list(solution, pack, visited, scan_private):
	next_queue = []
	for _dependency_key, _dependency_metadata in pack.links.items():
		_dependency = solution.get_module_with_key(_dependency_key)
		
		if _dependency.enabled == False:
			continue

		if _dependency.get_name() in visited:
			continue

		#if d.content.get_property_or_die("type") == "view":
		#	continue
		if not scan_private and "private" in _dependency_metadata.tags:
			continue

		next_queue.append(_dependency)
		visited.add(pack.get_name())

	return next_queue

def query_include_paths(solution, root_project):

	visited_projects = set([root_project.get_name()])
	query_queue = [root_project]

	result = []

	index = 0
	while len(query_queue) > 0:

		next_queue = []
		for c in query_queue:
			next_queue.extend(get_dependency_list(solution, c, visited_projects, index == 0))

			result.extend(c.content.query_paths(["include", "public"]))
			if index == 0:
				result.extend(c.content.query_paths(["include", "private"]))

		query_queue = next_queue
		index = index + 1

	return list(set([p.path for p in result]))

def query_sources(solution, root_project):

	result = root_project.content.query_files(["src"])

	return list(set([p.path for p in result]))

def join_prop_values(result, pl):
	for k,v in pl:
		result[k] = v.value

#def join_prop_keys(result, pl):
#	for k,v in pl:
#		result.append(k)

def query_defines(solution, root_project):

	result = {}

	visited_projects = set()
	query_queue = [root_project]

	index = 0
	while len(query_queue) > 0:

		next_queue = []
		for c in query_queue:
			next_queue.extend(get_dependency_list(solution, c, visited_projects, index == 0))

			join_prop_values(result, c.content.query_props(["define", "public"]))
			if index == 0:
				join_prop_values(result, c.content.query_props(["define", "private"]))

		query_queue = next_queue
		index = index + 1

	return result

def query_libs(solution, root_project):

	result = []

	visited_projects = set()
	query_queue = [root_project]

	while len(query_queue) > 0:

		next_queue = []
		for c in query_queue:
			dl = get_dependency_list(solution, c, visited_projects, True)
			next_queue.extend(dl)
			result.extend(dl)

		query_queue = next_queue

	return result

def query_extra_libs(solution, root_project):

	result = []

	visited_projects = set()
	query_queue = [root_project]

	index = 0
	while len(query_queue) > 0:

		next_queue = []
		for c in query_queue:
			next_queue.extend(get_dependency_list(solution, c, visited_projects, index == 0))

			result.extend(c.content.query_paths(["lib", "public"]))
			if index == 0:
				result.extend(c.content.query_paths(["lib", "private"]))

		query_queue = next_queue
		index = index + 1
		
	return list(set([p.path for p in result]))
