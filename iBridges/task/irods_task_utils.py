import json
from os.path import expanduser
__all__ = []


class iRodsCollectionNotFlat(Exception):
    def __init__(self, coll):
        msg = 'Collection {0} has subcollections'.format(coll)
        super(iRodsCollectionNotFlat, self).__init__(msg)


def get_irods_zone(cfg):
    if 'irods_zone_name' not in cfg or 'irods_host' not in cfg:
        env_file = cfg.get('irods_env_file')
        with open(expanduser(env_file)) as fp:
            fcfg = json.load(fp)
    else:
        fcfg = {}
    fcfg.update(cfg)
    return '{0}#{1}'.format(fcfg.get('irods_host'),
                            fcfg.get('irods_zone_name'))


def extract_irods_collecion_data(data, irods_collection):
    ret = [x for x in data.get('irods_data')
           if x['path'] == irods_collection]
    if len(ret) == 1:
        return ret[0]
    else:
        raise ValueError('collection {0} not found'.format(irods_collection))


def validate_meta_data(md, fields):
    errors = []
    missing = []
    for k, cfg in fields.items():
        if isinstance(cfg, bool) and cfg:
            if k not in md:
                missing.append(k)
        elif callable(cfg):
            if cfg(md):
                errors.append('validation failed {0}'.format(k))
    if len(errors) or len(missing):
        msg = "There are validations errors:\n"
        if len(missing):
            msg += ("missing: {0}\n" +
                    "available: {1}").format(missing,
                                             md.keys())
        if len(errors):
            msg += "errors: {0}\n".format(errors)
        raise ValueError(msg)
    return True


def validate_collection_meta_data(data, irods_collection, fields):
    md = extract_irods_collecion_data(data, irods_collection)['meta_data']
    return validate_meta_data(md, fields)


def validate_objects_meta_data(data, irods_collection, fields):
    msg = []
    for obj in extract_irods_collecion_data(data, irods_collection)['objects']:
        try:
            validate_meta_data(obj['meta_data'], fields)
        except ValueError as e:
            p = obj['path']
            msg.append(p + ":\n" + str(e))
    if len(msg):
        raise ValueError("\n".join(msg))
    return True


def transform_meta_data(md, fields):
    ret = {}
    for k, mapping in fields.items():
        if isinstance(mapping, str) and mapping in md:
            ret[k] = md[mapping]
        elif callable(mapping):
            value = mapping(md)
            if value is not None:
                ret[k] = value
    return ret
