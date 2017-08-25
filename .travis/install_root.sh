#! /usr/bin/env bash

# Travis script to install ROOT version 5.34.36

cd $TRAVIS_BUILD_DIR/..

# Directory root/ is cached and may already contain ROOT.
if [ ! -d root ]; then
    wget https://root.cern.ch/download/root_v5.34.36.Linux-ubuntu14-x86_64-gcc4.8.tar.gz
    tar -xzf root_v5.34.36.Linux-ubuntu14-x86_64-gcc4.8.tar.gz
fi

. root/bin/thisroot.sh
