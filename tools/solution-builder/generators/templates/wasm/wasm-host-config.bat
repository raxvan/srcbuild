::@echo off

:: Generates a visual studio solution in the target folder

set ENVNAME=emscripten-build-localhost
set BUILD_CONFIG=%1

set WWWSTATIC=%~dp0www/%BUILD_CONFIG%/

docker build -t %ENVNAME% -f %~dp0webhost/wasm-webserver.dockerfile %~dp0webhost

docker run ^
	--rm -it ^
	-p 8080:8080 ^
	-v %WWWSTATIC%:/www ^
	-e "TERM=xterm-256color" ^
	%ENVNAME% ^
	python3 /app/wasm-webhost.py


