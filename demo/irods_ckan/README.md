# iRODS to CKAN demo workflow

## Requirements

- docker
- docker-compose


## Buiding the containers

```
cd demo/irods_ckan
docker-compose build
```

## Start the container composite

```
./demo/irods_ckan/up.sh
```

## Create test organization in CKAN

Login to CKAN (http://localhost:5000)[http://localhost:5000] as
user *ckadmin* (password *ckadminckadmin*) and create orginaization with name *test*.
(http://127.0.0.1:5000/organization/new)[http://127.0.0.1:5000/organization/new]


## Restarting Airflow services

```
./demo/irods_ckan/restart_airflow.sh
```


## Activate Airflow DAG

Goto to airflow web interface and activate the dag

(http://127.0.0.1:8080/admin/)[http://127.0.0.1:8080/admin/]


## Trigger the a dag run

```
EXEC="docker exec irods_ckan_airflow_1 "
$EXEC airflow trigger_dag irods_to_ckan -c '{ "irods_collection": "/tempZone/public/SpaceInImages" }'
```

## Follow the state changes in MongoDB

(http://127.0.0.1:8081/db/ibridges/ibridges)[http://127.0.0.1:8081/db/ibridges/ibridges]

## Run a specific task manually

```
./ibridge --config demo/irods_ckan/ibridges-cli.json iBridges.task.ckan.test_connection
```


## Troubleshooting 


### Show logs for airflow scheduler and webserver

```
# inside irods_ckan_airflow_1 container
cd /usr/lib/airflow

# logs for scheduler
cat supervisor/airflow_scheduler-stdout---supervisor-*.log

# logs for webserver
cat supervisor/airflow_webserver-stdout---supervisor-*.log
```

### Show logs for DAG:

```
./demo/irods_ckan/log_irbridges.sh
```



## Shut down the system

```
./demo/irods_ckan/down.sh
```

## Applications

* airflow http://localhost:8080
* mongoexpress mongoDB http://127.0.0.1:8081
* ckan http://localhost:5000


## Debug tools
