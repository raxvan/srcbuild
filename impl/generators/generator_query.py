
import os
import package_builder

def make_relative_path(of_file, where_is_the_project):
	return os.path.relpath(of_file, where_is_the_project)

def get_dependency_list(project_stack, pack, visited, scan_private):
	next_queue = []
	for _dependency in pack.content.dependency:
		if _dependency.get_name() in visited:
			continue
		d = project_stack[_dependency.get_name()]
		if d.content.get_property_or_die("type") == "view":
			continue
		if not scan_private and _dependency.query_tags(["private"]):
			continue

		next_queue.append(d)
		visited.add(pack.get_name())

	return next_queue

def query_include_paths(project_stack, root_project):

	visited_projects = set([root_project.get_name()])
	query_queue = [root_project]

	result = []

	index = 0
	while len(query_queue) > 0:

		next_queue = []
		for c in query_queue:
			next_queue.extend(get_dependency_list(project_stack, c, visited_projects, index == 0))

			result.extend(c.content.query_paths(["include", "public"]))
			if index == 0:
				result.extend(c.content.query_paths(["include", "private"]))

		next_queue.sort(key=package_builder.get_package_priority)

		query_queue = next_queue
		index = index + 1

	return list(set([p.path.get_abs_path() for p in result]))

def query_sources(project_stack, root_project):

	result = root_project.content.query_files(["src"])

	return list(set(result))

def join_prop_values(result, pl):
	for k,v in pl:
		result[k] = v.value

def query_defines(project_stack, root_project):

	result = {}

	#global defines:
	for _, p in project_stack.items():
		join_prop_values(result, p.content.query_props(["define", "global"]))


	visited_projects = set()
	query_queue = [root_project]

	index = 0
	while len(query_queue) > 0:

		next_queue = []
		for c in query_queue:
			next_queue.extend(get_dependency_list(project_stack, c, visited_projects, index == 0))

			join_prop_values(result, c.content.query_props(["define", "public"]))
			if index == 0:
				join_prop_values(result, c.content.query_props(["define", "private"]))

		next_queue.sort(key=package_builder.get_package_priority)

		query_queue = next_queue
		index = index + 1

	return result



def query_libs(project_stack, root_project):

	result = []

	visited_projects = set()
	query_queue = [root_project]

	while len(query_queue) > 0:

		next_queue = []
		for c in query_queue:
			next_queue.extend(get_dependency_list(project_stack, c, visited_projects, True))

			result.extend(c.content.query_props(["lib"]))

			for _dependency in c.content.dependency:
				result.append(_dependency.get_name())

		query_queue = next_queue

	return result