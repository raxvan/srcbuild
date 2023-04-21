#!/bin/bash

#https://stackoverflow.com/questions/24460486/cmake-build-type-is-not-being-used-in-cmakelists-txt

#export CC=/usr/bin/clang
#export CXX=/usr/bin/clang++

if [ $# -eq 0 ]
then
	>&2 echo "Missing configudation argument, use any of [Debug Release]"
	exit -1
fi


export BUILD_CONFIG=$1
	#^ Debug/Release

mkdir -p $BUILD_CONFIG
cmake -B$BUILD_CONFIG -DCMAKE_CONFIGURATION_TYPES="Debug;Release" -DCMAKE_BUILD_TYPE=$BUILD_CONFIG .
cmake --build $BUILD_CONFIG
