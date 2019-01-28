# Using the docker container

## Requirements

- docker
- docker-compose


## Buiding the containers

```
cd ib-airflow
docker-compose build
```

## Starting the container composite

```
./ib-airflow/up.sh
```

## Applications

* airflow http://localhost:8080
* mongoDB http://127.0.0.1:8081
* ckan http://localhost:5000


## Debug tools
