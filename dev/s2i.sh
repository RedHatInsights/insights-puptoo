#!/bin/bash

IMAGE_NAME=$1
TAG=$2

usage () {
    echo "Usage:"
    echo "sh s2i.sh IMAGE_NAME:TAG"
}

if [ $(ps -aef | grep docker | wc -l) -lt "2" ]
then
  echo "Docker Not Running"
  exit
fi

if [ "$(id -u)" != "0" ]
then
  echo "S2I must be run as root to access docker daemon"
  exit
fi

if [ -z "$1" ]
then
    usage
elif [ -z "$2" ]
then
    usage
fi

s2i build ../ centos/python-36-centos7 ${IMAGE_NAME}:${TAG} -e ENABLE_PIPENV=true