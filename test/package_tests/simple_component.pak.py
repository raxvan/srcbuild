

def configure(ctx):
	ctx.component("simple_enabled_component",True)
	ctx.component("simple_disabled_component",False)


def construct(ctx):
	
	assert(ctx.component_enabled("simple_enabled_component"))
	assert(ctx.component_enabled("simple_disabled_component") == False)


