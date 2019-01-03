BASEDIR=/usr/lib/airflow/airflow/logs/scheduler/latest

docker exec airflow tail -n 100 -f $BASEDIR/ibridges.py.log



