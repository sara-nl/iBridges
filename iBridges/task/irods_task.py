import json
import logging
from os.path import expanduser
from irods_collection import iRodsCollection

__all__ = ['irods_test_connection',
           'irods_lock_collection',
           'irods_unlock_collection',
           'irods_check_flatness']


class iRodsCollectionNotFlat(Exception):
    def __init__(self, coll):
        msg = 'Collection {0} has subcollections'.format(coll)
        super(iRodsCollectionNotFlat, self).__init__(msg)


def get_irods_zone(cfg):
    if 'irods_zone_name' in cfg and 'irods_host' in cfg:
        return '{0}#{1}'.format(cfg.get('irods_host'),
                                cfg.get('irods_zone_name'))
    else:
        auth_file = cfg.get('irods_env_file')
        with open(expanduser(auth_file)) as fp:
            cfg = json.load(fp)
            return '{0}#{1}'.format(cfg.get('irods_host'),
                                    cfg.get('irods_zone_name'))


def irods_test_connection(ibcontext, **kwargs):
    logger = logging.getLogger('ipublish')
    config = ibcontext['irods'].get_config(kwargs)
    logger.debug(config)
    with ibcontext['irods'].session() as sess:
        logger.debug(vars(sess.users.get(sess.username)))


def irods_lock_collection(ibcontext, **kwargs):
    logger = logging.getLogger('ipublish')
    cfg = ibcontext['irods'].get_config(kwargs)
    logger.debug(cfg)
    with ibcontext['irods'].session() as sess:
        collection = iRodsCollection(sess, cfg['irods_collection'])
        ibcontext['cache'].write(['irods_zone', 'irods_collection'],
                                 {'irods_data': collection.lock(),
                                  'irods_zone': get_irods_zone(cfg),
                                  'irods_collection': cfg['irods_collection']})


def irods_unlock_collection(ibcontext, **kwargs):
    logger = logging.getLogger('ipublish')
    cfg = ibcontext['irods'].get_config(kwargs)
    logger.debug(cfg)
    with ibcontext['irods'].session() as sess:
        collection = iRodsCollection(sess, cfg['irods_collection'])
        key = {'irods_zone': get_irods_zone(cfg),
               'irods_collection': cfg['irods_collection']}
        data = ibcontext['cache'].read(key)
        collection.unlock(data.get('irods_data'))


def irods_check_flatness(ibcontext, **kwargs):
    """
    Checks if the collection is flat
    """
    logger = logging.getLogger('ipublish')
    cfg = ibcontext['irods'].get_config(kwargs)
    logger.debug(cfg)
    key = {'irods_zone': get_irods_zone(cfg),
           'irods_collection': cfg['irods_collection']}
    data = ibcontext['cache'].read(key)
    data = data.get('irods_data', [])
    if len(data) != 1 or data[0]['path'] != cfg['irods_collection']:
        raise iRodsCollectionNotFlat(cfg['irods_collection'])
