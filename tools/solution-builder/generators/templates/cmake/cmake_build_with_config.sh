#!/bin/bash

# Can build on linux/unix/etc with "default" builder using a config

#https://stackoverflow.com/questions/24460486/cmake-build-type-is-not-being-used-in-cmakelists-txt

#export CC=/usr/bin/clang
#export CXX=/usr/bin/clang++


echo ----------------------------------------------------------------------------------------------------------------
echo ...
echo ----------------------------------------------------------------------------------------------------------------

if [ $# -eq 0 ]
then
	>&2 echo "Missing configudation argument, use any of [Debug,Release]"
	exit -1
fi

export BUILD_FOLDER=intermediate
export BUILD_CONFIG=$1
	#^ Debug/Release

ADDRESS_SANITIZER=-DENABLE_ADDRESS_SANITIZER=NO


for arg in "$@"
do
    if [ "$arg" == "--use-address-sanitizer" ]; then
        ADDRESS_SANITIZER=-DENABLE_ADDRESS_SANITIZER=YES
        break
    fi
done


mkdir -p $BUILD_FOLDER
cd $BUILD_FOLDER

cmake -B$BUILD_CONFIG ${ADDRESS_SANITIZER} -DACTIVE_BUILD_CONFIGURATION="${BUILD_CONFIG}" -DCMAKE_CONFIGURATION_TYPES="Debug;Release" -DCMAKE_BUILD_TYPE=$BUILD_CONFIG ../
cmake --build $BUILD_CONFIG

cd -
