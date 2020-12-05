#!/bin/bash
set -e

MAIN_WORKSPACE=$1
THIS_WORKSPACE=$2

/bin/bash $MAIN_WORKSPACE/exec.sh $THIS_WORKSPACE python3 /wcore/workspace/srcbuild/cpptools/prj.info.py -a make linux
/bin/bash $MAIN_WORKSPACE/exec.sh $THIS_WORKSPACE python3 /wcore/workspace/srcbuild/cpptools/prj.info.py -a cmake linux

#build
cd ${THIS_WORKSPACE}/srcbuild/cpptools/build/info_linux_make
make config=debug_arm all
make config=release_arm all

cd ${THIS_WORKSPACE}/srcbuild/cpptools/build/info_linux_cmake
cmake .
cmake --build . --config Debug


#run exe
cd ${THIS_WORKSPACE}/srcbuild/cpptools/build/info_linux_make
./bin/ARM/Debug/_info
./bin/ARM/Release/_info


cd ${THIS_WORKSPACE}/srcbuild/cpptools/build/info_linux_cmake
./bin/_info


