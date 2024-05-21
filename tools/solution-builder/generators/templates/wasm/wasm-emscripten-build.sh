#!/bin/bash
set -e -o pipefail

cd /workspace/__WORKSPACE_PATH__

BUILD_CONFIG=$1

mkdir -p $BUILD_CONFIG
mkdir -p www
mkdir -p www/$BUILD_CONFIG

cd ./$BUILD_CONFIG

emcmake cmake -DACTIVE_BUILD_CONFIGURATION="${BUILD_CONFIG}" -DCMAKE_CONFIGURATION_TYPES="Debug;Release" -DCMAKE_BUILD_TYPE=$BUILD_CONFIG ../
emmake make

cd -