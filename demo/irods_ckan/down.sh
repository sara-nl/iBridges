#!/bin/bash

PDIR=$( dirname $(readlink -f $0))

docker-compose -f $PDIR/docker-compose.yml down
