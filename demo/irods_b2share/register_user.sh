#!/bin/bash

echo email:
read EMAIL
docker exec irods_b2share_b2share_1 b2share access allow -e $EMAIL superuser-access
