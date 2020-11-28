@echo on

set "MAIN_WORKSPACE=%~1"
set "THIS_WORKSPACE=%~2"

::ENVCONF_DEVENV 
::ENVCONF_MSBUILD

::-------------------------------------------------------------------------------------
::compile and run
powershell %MAIN_WORKSPACE%/exec.cmd %THIS_WORKSPACE% python3 /wcore/workspace/srcbuild/cpptools/prj.info.py -a vs2019 win32

cd %THIS_WORKSPACE%/srcbuild/cpptools/build/info_win32_vs2019

"%ENVCONF_DEVENV%" _info.sln /Build Debug
"bin/x32/Debug/_info.exe"
