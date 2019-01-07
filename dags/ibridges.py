#!/usr/bin/env python
import os
import logging
from iBridges.dag import iBridgesDag
from iBridges import Context
import iBridges.task as task

# airflow will refresh this dag only if this module is imported
from airflow.models import DAG  # noqa: F401

logging.getLogger('ipublish').setLevel(logging.DEBUG)

context = Context("ibridges.json",
                  search_path=os.path.abspath(os.path.dirname(__file__)))
dag = iBridgesDag('itest', context)

init_task = dag.init_task()
mongo_test_connection = dag.task(task.mongo_test_connection)
irods_test_connection = dag.task(task.irods_test_connection)
ckan_test_connection = dag.task(task.ckan_test_connection)
irods_lock_collection = dag.task(task.irods_lock_collection)
irods_check_flatness, \
    irods_check_flatness_ok, \
    irods_check_flatness_error = dag.branch_task(task.irods_check_flatness)

irods_unlock_collection = dag.task(task.irods_unlock_collection)

final_success = dag.final_task(True)
final_failed = dag.final_task(False)

init_task >> mongo_test_connection >> irods_lock_collection
init_task >> irods_test_connection >> irods_lock_collection
init_task >> ckan_test_connection >> irods_lock_collection
irods_lock_collection >> irods_check_flatness
irods_check_flatness_error >> irods_unlock_collection >> final_failed
irods_check_flatness_ok >> final_success


if __name__ == "__main__":
    dag.cli()
