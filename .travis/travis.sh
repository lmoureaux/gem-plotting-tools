#! /usr/bin/env bash

set -e
set -v

# Version of CentOS/RHEL
el_version=$1

docker_image=gitlab-registry.cern.ch/sturdy/gemdaq_ci_worker:slc6
# Run tests in Container
if [ "$el_version" = "6" ]
then
    sudo docker run ${docker_image} /bin/bash -c "bash -xe ./.travis/docker.sh ${OS_VERSION}"
elif [ "$el_version" = "7" ]
then
    docker run --privileged -d -ti -e "container=docker"  -v /sys/fs/cgroup:/sys/fs/cgroup $docker_image /usr/sbin/init
    DOCKER_CONTAINER_ID=$(docker ps | grep centos | awk '{print $1}')
    docker logs $DOCKER_CONTAINER_ID
    docker exec -ti $DOCKER_CONTAINER_ID /bin/bash -xec "bash -xe ./.travis/docker.sh ${OS_VERSION};
  echo -ne \"------\nEND GEM-PLOTTING-TOOLS TESTS\n\";"
    docker ps -a
    docker stop $DOCKER_CONTAINER_ID
    docker rm -v $DOCKER_CONTAINER_ID
fi
