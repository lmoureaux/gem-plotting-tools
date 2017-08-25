#! /usr/bin/env bash

# Script to setup data paths

# For Ubuntu 14.04: add pyroot to PYTHON_PATH
export PYTHONPATH="/usr/share/python-support/root:/usr/lib/python2.7/dist-packages/"

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