@echo off

:: Generates a visual studio solution in the target folder

cmake -G "Visual Studio 17 2022" -DCMAKE_CONFIGURATION_TYPES="Debug;Release" .

echo Build: "cmake --build . --config [Debug,Release]"

