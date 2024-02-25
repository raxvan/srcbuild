

def configure(ctx):
	ctx.option("simple_option","test", ["value0","value1"])
	ctx.option("null_option",None, ["value0","value1"])
	ctx.option("yolo_option","yolo1")


def construct(ctx):
	
	assert(ctx.get_option("simple_option") in ["value0","value1"])
	#^ because at the end of the configure process, there is not other accepted value "test" added

	assert(ctx.get_option("null_option") == None)

	assert(ctx.get_option("yolo_option") == "yolo1")


	ctx.setoption("simple_option")


