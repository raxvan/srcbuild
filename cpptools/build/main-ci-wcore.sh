#!/bin/bash
set -e -o pipefail

MAIN_WORKSPACE=$1
THIS_WORKSPACE=$2

python3 ${THIS_WORKSPACE}/srcbuild/cpptools/prj.info.py -a make linux
python3 ${THIS_WORKSPACE}/srcbuild/cpptools/prj.info.py -a cmake linux

#build and stuff
cd ${THIS_WORKSPACE}/srcbuild/cpptools/build/info_linux_make
make config=debug_x64 all
make config=release_x64 all

cd ${THIS_WORKSPACE}/srcbuild/cpptools/build/info_linux_cmake
chmod +x _build.sh
source _build.sh Debug
source _build.sh Release


#run executables
cd ${THIS_WORKSPACE}/srcbuild/cpptools/build/info_linux_make
./bin/x64/Debug/_info
./bin/x64/Release/_info

cd ${THIS_WORKSPACE}/srcbuild/cpptools/build/info_linux_cmake
./bin/Debug/_info
./bin/Release/_info
