

def configure(ctx):
	ctx.link("disabled.pak.py").disable()
	ctx.link("simple_component.pak.py")
	ctx.link("simple_option.pak.py")

def construct(ctx):
	pass
