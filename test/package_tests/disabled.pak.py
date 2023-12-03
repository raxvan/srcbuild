

def configure(ctx):
	ctx.option("disabled_option","value", ["value0","value1"]);
	ctx.component("disabled_component",False)
	ctx.component("disabled_component_empty")
	ctx.link("empty.pak.py")
	
def construct(ctx):
	pass


