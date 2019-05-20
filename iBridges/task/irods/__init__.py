import logging
from irods.meta import iRODSMeta
from irods.models import Collection
import irods.keywords as kw
from .collection import iRodsCollection
from .utils import iRodsCollectionNotFlat
from .utils import get_irods_zone


__all__ = ['test_connection',
           'lock_collection',
           'unlock_collection',
           'check_flatness',
           'update_repository_info',
           'remove_ownership',
           'copy_collection']


def test_connection(ibcontext, **kwargs):
    """
    Test theconnection to irods server
    """
    logger = logging.getLogger('ipublish')
    config = ibcontext['irods'].get_config(kwargs)
    logger.debug(config)
    with ibcontext['irods'].session() as sess:
        logger.debug(vars(sess.users.get(sess.username)))


def lock_collection(ibcontext, **kwargs):
    """
    Transfer ownership of collection to current user.
    """
    logger = logging.getLogger('ipublish')
    cfg = ibcontext['irods'].get_config(kwargs)
    logger.debug(cfg)
    with ibcontext['irods'].session() as sess:
        collection = iRodsCollection(sess, cfg['irods_collection'])
        ibcontext['cache'].write(['irods_zone', 'irods_collection'],
                                 {'irods_data': collection.lock(),
                                  'irods_zone': get_irods_zone(cfg),
                                  'irods_collection': cfg['irods_collection']})


def unlock_collection(ibcontext, **kwargs):
    """
    Revert ownerhip transer to original user
    """
    logger = logging.getLogger('ipublish')
    cfg = ibcontext['irods'].get_config(kwargs)
    logger.debug(cfg)
    with ibcontext['irods'].session() as sess:
        collection = iRodsCollection(sess, cfg['irods_collection'])
        key = {'irods_zone': get_irods_zone(cfg),
               'irods_collection': cfg['irods_collection']}
        data = ibcontext['cache'].read(key)
        collection.unlock(data.get('irods_data'))


def check_flatness(ibcontext, **kwargs):
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


def update_repository_info(ibcontext, **kwargs):
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


def remove_ownership(ibcontext, **kwargs):
    logger = logging.getLogger('ipublish')
    cfg = ibcontext['irods'].get_config(kwargs)
    logger.debug(cfg)
    with ibcontext['irods'].session() as sess:
        collection = iRodsCollection(sess, cfg['irods_collection'])
        collection.remove_ownership()


def copy_collection(ibcontext, **kwargs):
    logger = logging.getLogger('ipublish')
    cfg = ibcontext['irods'].get_config(kwargs)
    key = {'irods_zone': get_irods_zone(cfg),
           'irods_collection': cfg['irods_collection']}
    target = cfg['irods_target']
    if target[-1] == '/':
        target = target[:-1]

    logger.debug(cfg)
    with ibcontext['irods'].session() as sess:
        data = ibcontext['cache'].read(key)
        data = data.get('irods_data', [])
        for item in data:
            if item.get('type') == 'collection':
                p = item.get('path')[len(cfg['irods_collection']):]
                target_path = target + p
                logger.debug(target_path)
                sess.collections.create(target_path, recurse=True)
                for obj in item.get('objects', []):
                    options = {kw.VERIFY_CHKSUM_KW: '',
                               kw.METADATA_INCLUDED_KW: ''}
                    p = target + \
                        obj.get('path')[len(cfg['irods_collection']):]
                    logger.debug("%s -> %s", obj.get('path'), p)
                    sess.data_objects.copy(obj.get('path'),
                                           p,
                                           **options)
                    # todo test if succeeded
            else:
                print(item.get('path'))
