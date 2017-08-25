#! /usr/bin/env bash

set -e
set -v

OS_VERSION=$1

# Clean the yum cache
yum -y clean all
yum -y clean expire-cache

pwd
ls -l
uname -a