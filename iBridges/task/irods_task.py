import logging
from irods.meta import iRODSMeta
from irods.models import Collection
from irods_collection import iRodsCollection
from irods_task_utils import iRodsCollectionNotFlat
from irods_task_utils import get_irods_zone


__all__ = ['irods_test_connection',
           'irods_lock_collection',
           'irods_unlock_collection',
           'irods_check_flatness',
           'irods_update_repository_info',
           'irods_remove_ownership']


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


def irods_update_repository_info(ibcontext, **kwargs):
    logger = logging.getLogger('ipublish')
    cfg = ibcontext['irods'].get_config(kwargs)
    logger.debug(cfg)
    key = {'irods_zone': get_irods_zone(cfg),
           'irods_collection': cfg['irods_collection']}
    data = ibcontext['cache'].read(key)
    with ibcontext['irods'].session() as sess:
        for k, value in data['repository_info'].items():
            logger.debug('set meta {0} {1}={2}'.format(cfg['irods_collection'],
                                                       k,
                                                       value))
            sess.metadata.add(Collection,
                              cfg['irods_collection'],
                              iRODSMeta(k, value))


def irods_remove_ownership(ibcontext, **kwargs):
    logger = logging.getLogger('ipublish')
    cfg = ibcontext['irods'].get_config(kwargs)
    logger.debug(cfg)
    with ibcontext['irods'].session() as sess:
        collection = iRodsCollection(sess, cfg['irods_collection'])
        collection.remove_ownership()
