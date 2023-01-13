#!/bin/bash

if [ $# -eq 0 ]
then
	>&2 echo "Missing configudation argument, use any of [Debug Release]"
	exit -1
fi

export BUILD_CONFIG=$1

#https://stackoverflow.com/questions/2264428/how-to-convert-a-string-to-lower-case-in-bash

mkdir unix-make-${1,,}
cd unix-make-${1,,}

cmake -G "Unix Makefiles" -DCMAKE_CONFIGURATION_TYPES="Debug;Release" -DCMAKE_BUILD_TYPE=$BUILD_CONFIG ../

cd -

echo ""


