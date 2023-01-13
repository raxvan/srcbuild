
mkdir vs2019
cd vs2019

cmake -G "Visual Studio 16 2019" -DCMAKE_CONFIGURATION_TYPES="Debug;Release" ../

cd ..

@echo Run "cmake --build . --config [Debug,Release]"

