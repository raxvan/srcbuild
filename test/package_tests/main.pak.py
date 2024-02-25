

def configure(ctx):
	ctx.link("disabled.pak.py").disable()
	ctx.link("simple_component.pak.py")
	ctx.link("simple_option.pak.py")

def construct(ctx):
	assert(ctx.module_enabled("disabled.pak.py") == False)

