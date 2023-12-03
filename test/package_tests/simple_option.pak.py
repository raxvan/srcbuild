

def configure(ctx):
	ctx.option("simple_option","value", ["value0","value1"])


def construct(ctx):
	

	ctx.assign_option("simple_option")


