#!/usr/bin/env python
# flake8: noqa
import os
import logging
from iBridges.dag import iBridgesDag
from iBridges import Context
import iBridges.task.ckan as task_ckan
import iBridges.task.b2share as task_b2share
import iBridges.task.irods as task_irods
import iBridges.task.mongo as task_mongo
import demo.irods_b2share.plugins.tasks as plugins

# airflow will refresh this dag only if this module is imported
from airflow.models import DAG  # noqa: F401

logging.getLogger('ipublish').setLevel(logging.DEBUG)

context = Context("ibridges.json",
                  search_path=os.path.abspath(os.path.dirname(__file__)))
dag = iBridgesDag('irods_to_b2share', context)


init_task = dag.init_task()
mongo_test_connection = dag.task(task_mongo.test_connection)
irods_test_connection = dag.task(task_irods.test_connection)
b2share_test_connection = dag.task(task_b2share.test_connection)
irods_lock_collection = dag.task(task_irods.lock_collection)
irods_check_flatness = dag.task(task_irods.check_flatness)
irods_validate_meta_data = dag.task(plugins.irods_validate_meta_data)
irods_transform_meta_data = dag.task(plugins.irods_transform_meta_data)
b2share_create_draft = dag.task(task_b2share.create_draft)
b2share_patch_draft = dag.task(task_b2share.patch_draft)
b2share_wait_for_confirmation = dag.task(task_b2share.wait_for_confirmation)
irods_update_repository_info = dag.task(task_irods.update_repository_info)

irods_remove_ownership = dag.task(task_irods.remove_ownership)

irods_unlock_collection = dag.task(task_irods.unlock_collection, trigger_rule='one_failed')

final_success = dag.final_task(True)
final_failed = dag.final_task(False)

init_task >> mongo_test_connection >> irods_lock_collection
init_task >> irods_test_connection >> irods_lock_collection
init_task >> b2share_test_connection >> irods_lock_collection

irods_lock_collection >> irods_check_flatness

irods_check_flatness >> irods_unlock_collection
irods_check_flatness >> irods_validate_meta_data

irods_validate_meta_data >> irods_unlock_collection
irods_validate_meta_data >> irods_transform_meta_data

irods_transform_meta_data >> b2share_create_draft
irods_transform_meta_data >> irods_unlock_collection

b2share_create_draft >> b2share_patch_draft
b2share_patch_draft >> b2share_wait_for_confirmation
b2share_wait_for_confirmation >> irods_update_repository_info
b2share_wait_for_confirmation >> irods_unlock_collection

irods_update_repository_info >> irods_remove_ownership
irods_update_repository_info >> irods_unlock_collection

irods_remove_ownership >> final_success
irods_remove_ownership >> final_failed

irods_unlock_collection >> final_failed


if __name__ == "__main__":
    dag.cli()
