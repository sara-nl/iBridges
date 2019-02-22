CONTAINER_NAME=irods_ckan_airflow_1

docker exec $CONTAINER_NAME airflow trigger_dag irods_to_ckan -c '{ "irods_collection": "/tempZone/public/SpaceInImages" }'
