#!/usr/bin/env python
# flake8: noqa
import os
import logging
from iBridges.dag import iBridgesDag
from iBridges import Context
import iBridges.task.ckan as task_ckan
import iBridges.task.irods as task_irods
import iBridges.task.mongo as task_mongo
import plugin_examples

# airflow will refresh this dag only if this module is imported
from airflow.models import DAG  # noqa: F401

logging.getLogger('ipublish').setLevel(logging.DEBUG)

context = Context("ibridges.json",
                  search_path=os.path.abspath(os.path.dirname(__file__)))
dag = iBridgesDag('itest', context)


init_task = dag.init_task()
mongo_test_connection = dag.task(task_mongo.test_connection)
irods_test_connection = dag.task(task_irods.test_connection)
ckan_test_connection = dag.task(task_ckan.test_connection)
irods_lock_collection = dag.task(task_irods.lock_collection)
irods_check_flatness = dag.task(task_irods.check_flatness)
irods_validate_meta_data = dag.task(plugin_examples.irods_validate_meta_data)
irods_transform_meta_data = dag.task(plugin_examples.irods_transform_meta_data)
ckan_create_package = dag.task(task_ckan.create_package)
irods_update_repository_info = dag.task(task_irods.update_repository_info)
irods_remove_ownership = dag.task(task_irods.remove_ownership)

irods_unlock_collection = dag.task(task_irods.unlock_collection, trigger_rule='one_failed')

final_success = dag.final_task(True)
final_failed = dag.final_task(False)
final_failed2 = dag.final_task(False, task_id='final_failed2')

init_task >> mongo_test_connection >> irods_lock_collection
init_task >> irods_test_connection >> irods_lock_collection
init_task >> ckan_test_connection >> irods_lock_collection

irods_lock_collection >> irods_check_flatness

irods_check_flatness >> irods_unlock_collection
irods_check_flatness >> irods_validate_meta_data

irods_validate_meta_data >> irods_unlock_collection
irods_validate_meta_data >> irods_transform_meta_data

irods_transform_meta_data >> ckan_create_package
irods_transform_meta_data >> irods_unlock_collection

ckan_create_package >> irods_update_repository_info
ckan_create_package >> irods_unlock_collection

irods_update_repository_info >> irods_remove_ownership
irods_update_repository_info >> irods_unlock_collection

irods_remove_ownership >> final_success
irods_remove_ownership >> final_failed

irods_unlock_collection >> final_failed2


if __name__ == "__main__":
    dag.cli()
