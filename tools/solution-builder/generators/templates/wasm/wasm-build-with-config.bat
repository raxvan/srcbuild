::@echo off

:: Generates a visual studio solution in the target folder

set ENVNAME=emscripten-build
set BUILD_CONFIG=%1

set WORKSPACE_RELPATH=%~dp0__WORKSPACE_RELPATH__

cd %WORKSPACE_RELPATH%
set WORKSPACE_ABSPATH=%cd%
cd %~dp0

docker build -t %ENVNAME% -f %~dp0emscripten/wasm-emscripten.dockerfile %~dp0emscripten

docker run ^
	--rm -it ^
	-v %WORKSPACE_ABSPATH%:/workspace ^
	-e "TERM=xterm-256color" ^
	%ENVNAME% ^
	/bin/bash /wasmbuild/wasm-emscripten-build.sh %BUILD_CONFIG%


