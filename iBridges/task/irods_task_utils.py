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


def extract_required_fields(fields):
    def is_required(cfg):
        if isinstance(cfg, str):
            return True
        elif isinstance(cfg, tuple) and len(cfg) == 1:
            return True
        elif isinstance(cfg, tuple) and len(cfg) > 1:
            return cfg[1]

    return [k for k, cfg in fields.items() if is_required(cfg)]


def check_collection_metadata_fields(_data, _fields):
    fields = extract_required_fields(_fields)
    irods_collection = _data.get('irods_collection')
    data = [x for x in _data.get('irods_data')
            if x['path'] == irods_collection][0]
    missing = [k
               for k in fields
               if k not in data['meta_data']]
    if len(missing):
        avail = [k
                 for k in fields
                 if k in data['meta_data']]
        msg = ("Missing collection metadata fields\n" +
               "collection: {0}\n" +
               "missing: {1}\n" +
               "avail: {2}")
        raise ValueError(msg.format(irods_collection,
                                    ', '.join(missing),
                                    ', '.join(avail)))


def check_object_metadata_fields(_data, _fields):
    fields = extract_required_fields(_fields)
    irods_collection = _data.get('irods_collection')
    data = [x for x in _data.get('irods_data')
            if x['path'] == irods_collection][0]
    missing = []
    for obj in data['objects']:
        missing += ['{0}:{1}'.format(obj['path'], k)
                    for k in fields
                    if k not in obj['meta_data']]
    if len(missing):
        msg = ("Missing object metadata fields\n" +
               "collection: {0}\n" +
               "missing: {1}")
        raise ValueError(msg.format(irods_collection,
                                    ', '.join(missing)))


def _aux_get_target_metadata(meta_data, mapping):
    ret = {}
    for k, val in mapping.items():
        if k in meta_data:
            if isinstance(val, str):
                ret[val] = meta_data[k]
            elif isinstance(val, tuple) and len(val) < 3:
                ret[val[0]] = meta_data[k]
            elif isinstance(val, tuple) and len(val) >= 3:
                ret[val[0]] = val[2](meta_data[k])
    return ret


def get_target_metadata(_data, collection_mapping=None, object_mapping=None):
    irods_collection = _data.get('irods_collection')
    data = [x for x in _data.get('irods_data')
            if x['path'] == irods_collection][0]
    ret = {}
    if collection_mapping is not None:
        ret[irods_collection] = _aux_get_target_metadata(data['meta_data'],
                                                         collection_mapping)
    if object_mapping is not None:
        for obj in data['objects']:
            ret[obj['path']] = _aux_get_target_metadata(obj['meta_data'],
                                                        object_mapping)
    return ret


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
