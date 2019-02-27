CONTAINER_NAME=irods_b2share_airflow_1

docker exec $CONTAINER_NAME airflow trigger_dag irods_to_b2share -c '{ "irods_collection": "/tempZone/public/SpaceInImages" }'
