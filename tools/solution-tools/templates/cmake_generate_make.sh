#!/bin/bash

# Generates a `make` solution on a single config

if [ -z "$2" ]
then
	>&2 echo "Missing configudation argument, use any of [Debug,Release]"
	exit -1
fi

export BUILD_OUT_DIR=$1
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

echo "Build folder: ${BUILD_OUT_DIR}"
mkdir -p $BUILD_OUT_DIR
cd $BUILD_OUT_DIR

cmake -G "Unix Makefiles" ${ADDRESS_SANITIZER} -DOUTPUT_BINSUBDIR="${BUILD_OUT_DIR}" -DCMAKE_CONFIGURATION_TYPES="Debug;Release" -DCMAKE_BUILD_TYPE=$BUILD_CONFIG ../

cd -

echo "Build: cd ${BUILD_OUT_DIR} && make"


