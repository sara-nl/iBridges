BASEDIR=/usr/lib/airflow/airflow/logs/scheduler/latest
CONTAINER_NAME=irods_b2share_airflow_1

docker exec $CONTAINER_NAME tail -n 100 -f $BASEDIR/ibridges.py.log



