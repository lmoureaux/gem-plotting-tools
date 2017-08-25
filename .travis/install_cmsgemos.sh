#! /usr/bin/env bash

# Travis script to install cmsgemos

cd $TRAVIS_BUILD_DIR/..
git clone --depth 1 https://github.com/cms-gem-daq-project/cmsgemos.git

pip install -r cmsgemos/gempython/requirements.txt
