#!/bin/bash

while ! curl airflowdb:5432 2>&1 | grep '52'
do
  sleep 1
done

while ! ( PGPASSWORD=airflow psql -h airflowdb airflow airflow -c '\q' );
do
    sleep 1
done


/usr/local/bin/airflow initdb
/usr/bin/supervisord -c /etc/supervisor/supervisord.conf
