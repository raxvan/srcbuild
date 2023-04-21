#!/bin/bash

if [ -z "$2" ]
then
	>&2 echo "Missing configudation argument, use any of [Debug Release]"
	exit -1
fi

export BUILD_SUBDIR=$1
export BUILD_CONFIG=$2 #Debug Release ...

#https://stackoverflow.com/questions/2264428/how-to-convert-a-string-to-lower-case-in-bash


ADDRESS_SANITIZER=-DENABLE_ADDRESS_SANITIZER=NO


for arg in "$@"
do
    if [ "$arg" == "--use-address-sanitizer" ]; then
        ADDRESS_SANITIZER=-DENABLE_ADDRESS_SANITIZER=YES
        break
    fi
done


mkdir -p $BUILD_SUBDIR
cd $BUILD_SUBDIR

cmake -G "Unix Makefiles" ${ADDRESS_SANITIZER} -DOUTPUT_BINSUBDIR="${BUILD_SUBDIR}" -DCMAKE_CONFIGURATION_TYPES="Debug;Release" -DCMAKE_BUILD_TYPE=$BUILD_CONFIG ../

cd -

echo ""


