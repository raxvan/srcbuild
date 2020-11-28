
import srcbuild

ctx = srcbuild.Generator()

ctx.run("exe",
	src = ctx.glob("info",[".cpp",".h"])
)
