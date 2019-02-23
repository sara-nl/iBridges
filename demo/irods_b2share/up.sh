#!/bin/bash

PDIR=$( dirname $(readlink -f $0))
DIR=$( dirname $PDIR )
DIR=$( dirname $DIR )

VOLUME=$DIR docker-compose -f $PDIR/docker-compose.yml up 
