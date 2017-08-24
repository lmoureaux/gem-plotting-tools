#! /usr/bin/env bash

# Script to setup data paths

mkdir gemdata
mkdir gemelog

export BUILD_HOME="$TRAVIS_BUILD_DIR/.."
export DATA_PATH="$TRAVIS_BUILD_DIR/.travis/data"
export ELOG_PATH="$BUILD_HOME/gemelog"

cd "$BUILD_HOME"

echo "====== cmsgemos"
. cmsgemos/setup/paths.sh
echo "====== gem-plotting-tools"
. gem-plotting-tools/setup/paths.sh

# Finished
echo "GEM DAQ Environment Configured"
