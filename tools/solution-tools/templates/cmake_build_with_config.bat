@echo off

:: Generates a visual studio solution in the target folder

set BUILD_FOLDER=intermediate
set BUILD_CONFIG=%1

mkdir %BUILD_FOLDER%
cd %BUILD_FOLDER%

cmake -B%BUILD_CONFIG% -DCMAKE_CONFIGURATION_TYPES="Debug;Release" -DCMAKE_BUILD_TYPE=%BUILD_CONFIG% ../
cmake --build %BUILD_CONFIG%


