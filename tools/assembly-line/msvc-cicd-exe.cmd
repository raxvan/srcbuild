@echo on
setlocal enabledelayedexpansion
set "WORKSPACE_HUB=%~1"
set "THIS_WORKSPACE=%~2"

set "TARGET_PROJECT_IN_WORKSPACE=%~3"

::-------------------------------------------------------------------------------------
::prepare
for /f "delims=" %%G in ('python3 %THIS_WORKSPACE%/srcbuild/tools/assembly-line/prepare_environment.py win-exe') do (
    %%G
)

::-------------------------------------------------------------------------------------
::generate solution
powershell %WORKSPACE_HUB%/_enter_wspace.cmd %THIS_WORKSPACE% python3 /wspace/workspace/srcbuild/srcbuild.py solution win %TARGET_PROJECT_IN_WORKSPACE%

call %WORKSPACE_HUB%/.user/workspace_config.cmd

::-------------------------------------------------------------------------------------
::compile

"%ENVCONF_DEVENV%" %ABS_SOLUTION_DIR%/%SOLUTION_NAME% /Build "Debug|x64"
"%ENVCONF_DEVENV%" %ABS_SOLUTION_DIR%/%SOLUTION_NAME% /Build "Release|x64"

::-------------------------------------------------------------------------------------
::static code analysis
"%ENVCONF_MSBUILD%" %ABS_SOLUTION_DIR%/%SOLUTION_NAME% /m /p:RunCodeAnalysis=true /p:Configuration=Release /p:Platform=x64

::-------------------------------------------------------------------------------------
:: run files

cd %ABS_SOLUTION_DIR%

"bin/x64/Debug/%EXECUTABLE_NAME%"

"bin/x64/Release/%EXECUTABLE_NAME%"

