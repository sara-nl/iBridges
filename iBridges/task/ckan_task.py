import logging
from irods_task_utils import get_irods_zone


__all__ = ['ckan_test_connection',
           'ckan_create_package']


class CkanOrganizationNotFound(Exception):
    def __init__(self, orga):
        msg = "organization {0} not found in CKAN".format(orga)
        super(CkanOrganizationNotFound, self).__init__(msg)


def ckan_test_connection(ibcontext, **kwargs):
    logger = logging.getLogger('ipublish')
    config = ibcontext['ckan'].get_config(kwargs)
    logger.debug(config)
    result = ibcontext['ckan'].action('organization_list')
    if result['success']:
        if config['ckan_org'] not in result['result']:
            raise CkanOrganizationNotFound(config['ckan_org'])
    else:
        raise RuntimeError('CKAN connection error')


def ckan_create_package(ibcontext, **kwargs):
    logger = logging.getLogger('ipublish')
    irods_cfg = ibcontext['irods'].get_config(kwargs)
    ckan_cfg = ibcontext['ckan'].get_config(kwargs)
    key = {'irods_zone': get_irods_zone(irods_cfg),
           'irods_collection': irods_cfg['irods_collection']}
    data = ibcontext['cache'].read(key)
    if data is None:
        raise KeyError('No such key {0}'.format(key))
    collection = [x
                  for x in data.get('irods_data')
                  if x['path'] == irods_cfg['irods_collection']][0]
    target_meta_data = data['target_meta_data']
    md = target_meta_data[irods_cfg['irods_collection']].copy()
    md['owner_org'] = ckan_cfg['ckan_org']
    result = ibcontext['ckan'].action('package_create',
                                      data=md,
                                      method='post')
    id = result['result']['id']
    logger.info('created package with id {0}'.format(id))
    logger.debug(result['result'])
    result['result']['resources'] = []
    try:
        for obj in collection['objects']:
            obj_md = target_meta_data[obj['path']]
            obj_md['package_id'] = id
            obj_res = ibcontext['ckan'].action('resource_create',
                                               data=obj_md,
                                               method='post')
            result['result']['resources'].append(obj_res)
    except Exception:
        ibcontext['ckan'].action('package_delete',
                                 data={'id': id},
                                 method='post')
        raise
    ibcontext['cache'].update(key, {'ckan_package': result['result']})
    repo_url = ckan_cfg['ckan_dataset_url'] + '/' + md['name']
    repository_info = {'PUBLIC_URL': repo_url,
                       'PUBLIC_REPO_TYPE': 'CKAN'}
    ibcontext['cache'].update(key,
                              {'repository_info': repository_info})
