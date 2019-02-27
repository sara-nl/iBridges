import logging
import requests
import json
import time
from iBridges.task.irods.utils import get_irods_zone
from posixpath import join as urljoin
__all__ = ['test_connection']


class B2ShareCommunityNotFound(Exception):
    def __init__(self, community):
        msg = "community {0} not found in B2SHARE".format(community)
        super(B2ShareCommunityNotFound, self).__init__(msg)


def test_connection(ibcontext, **kwargs):
    logger = logging.getLogger('ipublish')
    b2share_cfg = ibcontext['b2share'].get_config(kwargs)
    logger.debug(b2share_cfg)
    api_url = b2share_cfg.get('b2share_api_url')
    access_token = b2share_cfg.get('b2share_access_token')
    community = b2share_cfg.get('b2share_community')
    url = urljoin(api_url,
                  'communities',
                  community)
    logger.info('checking community %s, url: %s', community, url)
    req = requests.get(url, params={'access_token': access_token})
    req.raise_for_status()
    req.json()


def create_draft(ibcontext, **kwargs):
    logger = logging.getLogger('ipublish')
    irods_cfg = ibcontext['irods'].get_config(kwargs)
    config = ibcontext['b2share'].get_config(kwargs)
    key = {'irods_zone': get_irods_zone(irods_cfg),
           'irods_collection': irods_cfg['irods_collection']}
    logger.debug(config)
    meta_data = ibcontext['cache'].read(key)\
                                  .get('target_meta_data')\
                                  .get(irods_cfg['irods_collection'])
    logger.debug(meta_data)
    api_url = config.get('b2share_api_url')
    access_token = config.get('b2share_access_token')
    community = config.get('b2share_community')
    url = urljoin(api_url, 'records') + '/'
    data = {'titles': [{'title': meta_data['title']}],
            'community': community,
            'open_access': True,
            'community_specific': {}}
    logger.debug('url: %s', url)
    logger.debug(data)
    req = requests.post(url,
                        data=json.dumps(data),
                        params={"access_token": access_token},
                        headers={"Content-Type": "application/json"})
    req.raise_for_status()
    if req.status_code != 201:
        raise ValueError('unexpected status code %d', req.status_code)
    b2share_id = req.json()['id']
    logger.debug('created draft %s', b2share_id)
    ibcontext['cache'].update(key,
                              {'b2share_id': b2share_id})
    repo_url = urljoin(api_url,
                       'records',
                       b2share_id,
                       'draft')
    repository_info = {'PUBLIC_URL': repo_url,
                       'PUBLIC_REPO_TYPE': 'B2SHARE'}
    ibcontext['cache'].update(key,
                              {'repository_info': repository_info})


def patch_draft(ibcontext, **kwargs):
    logger = logging.getLogger('ipublish')
    irods_cfg = ibcontext['irods'].get_config(kwargs)
    config = ibcontext['b2share'].get_config(kwargs)
    api_url = config.get('b2share_api_url')
    access_token = config.get('b2share_access_token')
    key = {'irods_zone': get_irods_zone(irods_cfg),
           'irods_collection': irods_cfg['irods_collection']}
    logger.debug(config)
    meta_data = ibcontext['cache'].read(key)\
                                  .get('target_meta_data')\
                                  .get(irods_cfg['irods_collection'])
    b2share_id = ibcontext['cache'].read(key)\
                                   .get('b2share_id')
    logger.debug('b2share id: %s', b2share_id)
    pids = []
    for item in ibcontext['cache'].read(key)\
                                  .get('target_meta_data').values():
        pids.append({'alternate_identifier': item['pid'],
                     'alternate_identifier_type': 'http://hdl.handle.net/'})
    patch = [{'op': 'add',
              'path': '/creators',
              'value': [{'creator_name': meta_data['author']}]},
             {'op': 'add',
              'path': '/alternate_identifiers',
              'value': pids}]
    logger.debug(patch)
    url = urljoin(api_url,
                  'records',
                  b2share_id,
                  'draft')
    req = requests.patch(url=url,
                         params={'access_token':
                                 access_token},
                         headers={"Content-Type":
                                  "application/json-patch+json"},
                         data=json.dumps(patch))
    req.raise_for_status()


def wait_for_confirmation(ibcontext, **kwargs):
    logger = logging.getLogger('ipublish')
    b2share_cfg = ibcontext['b2share'].get_config(kwargs)
    irods_cfg = ibcontext['irods'].get_config(kwargs)
    api_url = b2share_cfg.get('b2share_api_url')
    access_token = b2share_cfg.get('b2share_access_token')
    key = {'irods_zone': get_irods_zone(irods_cfg),
           'irods_collection': irods_cfg['irods_collection']}
    b2share_id = ibcontext['cache'].read(key)\
                                   .get('b2share_id')
    logger.debug('b2share id: %s', b2share_id)
    url = urljoin(api_url,
                  'records',
                  b2share_id,
                  'draft')
    state = 'draft'
    while state == 'draft':
        req = requests.get(url=url,
                           params={'access_token': access_token})
        req.raise_for_status()
        state = req.json().get('metadata', {}).get('publication_state', None)
        logger.debug('url: %s:%s', url, state)
        if state == 'draft':
            time.sleep(5)
