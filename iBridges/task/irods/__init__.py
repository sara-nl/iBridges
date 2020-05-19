import logging
import os
import re
import datetime
from irods.meta import iRODSMeta
from irods.models import Collection
from irods.models import User, UserGroup
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
           'copy_collection',
           'clear_cache']


def test_connection(ibcontext, **kwargs):
    """
    Test theconnection to irods server
    """
    logger = logging.getLogger('ipublish')
    config = ibcontext['irods'].get_config(kwargs)
    logger.debug(config)
    with ibcontext['irods'].session() as sess:
        logger.debug(vars(sess.users.get(sess.username)))


def clear_cache(ibcontext, **kwargs):
    logger = logging.getLogger('ipublish')
    cfg = ibcontext['irods'].get_config(kwargs)
    logger.debug(cfg)
    key = {'irods_zone': get_irods_zone(cfg),
           'irods_collection': cfg['irods_collection']}
    ibcontext['cache'].remove_if_exists(key)


def lock_collection(ibcontext, **kwargs):
    """
    Transfer ownership of collection to current user.
    """
    logger = logging.getLogger('ipublish')
    cfg = ibcontext['irods'].get_config(kwargs)
    logger.debug(cfg)
    with ibcontext['irods'].session() as sess:
        collection = iRodsCollection(sess, cfg['irods_collection'],
                                     target_user=cfg.get('target_user', None),
                                     target_zone=cfg.get('target_zone', None))
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


def get_owner(data, path):
    for obj in data:
        if obj['path'] == path:
            for acl in obj.get('acls').values():
                if acl['access_name'] == 'own' and \
                   acl['path'] == path:
                    return acl['user_name']
    return None


def get_research_group(sess, user, group_tag):
    result = sess.query(User, UserGroup.name).filter(User.name == user).all()
    groups = [row[UserGroup.name] for row in result.rows]
    for gr in groups:
        for meta in sess.metadata.get(User, gr):
            if meta.name == group_tag:
                return gr
    return None


def get_metadata(data, path):
    meta_data = None
    for obj in data:
        if obj['path'] == path:
            meta_data = obj.get('meta_data')
            break
    if not meta_data:
        raise RuntimeError("no meta_data for {0}".format(path))
    return meta_data


def determine_target_dir(sess, data, source, target, logger=None):
    if target[-1] == '/':
        target = target[:-1]
    for g in re.findall('{BASENAME}', target):
        target = target.replace(g, os.path.basename(source))
    for g in re.findall('(\\{BASENAME:([^/}]+)\\})', target):
        if source.startswith("/"):
            lst = source.split("/")[1:]
        else:
            lst = source.split("/")
        index = int(g[1])
        target = target.replace(g[0], lst[index])
    for g in re.findall('{USER}', target):
        target = target.replace(g, get_owner(data, source))
    for g in re.findall('{TIME}', target):
        dtg = datetime.datetime.utcnow()
        dtg = dtg.replace(tzinfo=datetime.timezone.utc,
                          microsecond=0)
        target = target.replace(g, dtg.isoformat())
    for g in re.findall('(\\{GROUP:([^/}]+)\\})', target):
        owner = get_owner(data, source)
        if not owner:
            msg = 'could not determine owner of irods collection {0}'
            msg = msg.format(source)
            raise RuntimeError(msg)
        group = get_research_group(sess, owner, g[1])
        if not group:
            msg = 'user {0} not in a {1} group'
            msg = msg.format(owner, g[1])
            raise RuntimeError(msg)
        target = target.replace(g[0], group)
    for g in re.findall('({META:([^/}]+)})', target):
        meta = get_metadata(data, source)
        meta_value = meta.get(g[1], None)
        if not meta_value:
            msg = 'could not find meta data value for key {0}'
            msg = msg.format(g[1])
            raise RuntimeError(msg)
        target = target.replace(g[0], meta_value)
    if logger:
        logger.debug("target %s", target)
    return target


def copy_collection(ibcontext, **kwargs):
    logger = logging.getLogger('ipublish')
    cfg = ibcontext['irods'].get_config(kwargs)
    key = {'irods_zone': get_irods_zone(cfg),
           'irods_collection': cfg['irods_collection']}
    logger.debug(cfg)
    with ibcontext['irods'].session() as sess:
        data = ibcontext['cache'].read(key)
        data = data.get('irods_data', [])
        target = determine_target_dir(sess,
                                      data,
                                      cfg['irods_collection'],
                                      cfg['irods_target'],
                                      logger)

        if not sess.collections.exists(target):
            logger.debug("create %s", target)
            sess.collections.create(target, recurse=True)
        meta_data = get_metadata(data, cfg['irods_collection'])
        for k, v in meta_data.items():
            logger.debug("add meta %s %s %s", target, k, v)
            sess.metadata.set(Collection, target,
                              iRODSMeta(k, v))
        for item in data:
            if item.get('type') == 'collection':
                subpath = item.get('path')[len(cfg['irods_collection']):]
                logger.debug("subpath {0}".format(subpath))
                if subpath:
                    target_coll = target + "/" + subpath
                    if not sess.collections.exists(target_coll):
                        sess.collections.create(target_coll, recurse=True)
                else:
                    target_coll = target
                for obj in item.get('objects', []):
                    options = {kw.VERIFY_CHKSUM_KW: '',
                               kw.METADATA_INCLUDED_KW: ''}
                    logger.debug("%s -> %s", obj.get('path'), target_coll)
                    sess.data_objects.copy(obj.get('path'),
                                           target_coll,
                                           **options)
            else:
                print(item.get('path'))
