

def configure(ctx):
	ctx.option("disabled_key","value", ["value","value1"]);
	ctx.component("disabled_component",False)
	ctx.component("disabled_component_empty")
	ctx.link("base1.pak.py")
	ctx.link("base2.pak.py")

def construct(ctx):
	pass


