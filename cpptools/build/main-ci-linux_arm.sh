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
chmod +x _build.sh
source _build.sh Debug
source _build.sh Release


#run exe
cd ${THIS_WORKSPACE}/srcbuild/cpptools/build/info_linux_make
./bin/ARM/Debug/_info
./bin/ARM/Release/_info


cd ${THIS_WORKSPACE}/srcbuild/cpptools/build/info_linux_cmake
./bin/Debug/_info
./bin/Release/_info


