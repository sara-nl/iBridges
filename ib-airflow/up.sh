#!/bin/bash

PDIR=$( dirname $(readlink -f $0))
DIR=$( dirname $PDIR )

VOLUME=$DIR docker-compose -f $PDIR/docker-compose.yml up 
