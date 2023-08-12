#!/bin/bash

set -e -o pipefail

export TARGET_PROJECT_IN_WORKSPACE=$1

cd /wspace/workspace

python3 /wspace/workspace/srcbuild/srcbuild.py solution cmake ${TARGET_PROJECT_IN_WORKSPACE}

eval "$(python3 /wspace/workspace/srcbuild/tools/assembly-line/prepare_environment.py wspace-exe)"

#-------------------------------------------------------------------------------------
#generate solutoins
cd ${ABS_SOLUTION_DIR}
chmod +x ./cmake_generate_make.sh

./cmake_generate_make.sh wspace-debug Debug
./cmake_generate_make.sh wspace-release Release

#-------------------------------------------------------------------------------------
#build solutions
cd ${ABS_SOLUTION_DIR}/wspace-debug
make

cd ${ABS_SOLUTION_DIR}/wspace-release
make

#-------------------------------------------------------------------------------------
#run builds
cd ${ABS_SOLUTION_DIR}

./bin/wspace-debug/${EXECUTABLE_NAME}
./bin/wspace-release/${EXECUTABLE_NAME}

#valgrind --leak-check=full --log-fd=1 --error-exitcode=1911 ./bin/wspace-debug/${EXECUTABLE_NAME}
#valgrind --leak-check=full --log-fd=1 --error-exitcode=1911 ./bin/wspace-debug/${EXECUTABLE_NAME}
