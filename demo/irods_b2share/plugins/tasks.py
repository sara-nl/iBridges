import datetime
import re
import os
from iBridges.task.irods.utils import get_irods_zone
from iBridges.task.irods.utils import extract_irods_collecion_data
from iBridges.task.irods.utils import validate_collection_meta_data
from iBridges.task.irods.utils import validate_objects_meta_data
from iBridges.task.irods.utils import transform_meta_data


def get_pixel_data_size(obj):
    if 'PixelData' in obj:
        return len(obj.PixelData)
    else:
        return 0


def normalize_name(obj):
    title = obj['TITLE']
    return re.sub(r"[^-a-z-_]", "", title.lower())


def get_date_time(obj):
    if 'InstanceCreationTime' in obj and 'InstanceCreationDate' in obj:
        time = re.sub('([0-9]+)(\.[0-9]*)?', r'\1', obj.InstanceCreationTime)
        dtg = obj.InstanceCreationDate + '_' + time
        dt = datetime.datetime.strptime(dtg, "%Y%m%d_%H%M%S")
        return dt.isoformat()
    else:
        return ''


COLLECTION_META_DATA_VALIDATION = {
    "TITLE": True,
    "OWNER": True
}


OBJECT_META_DATA_VALIDATION = {
    "Title": True,
    "url": True
}

COLLECTION_META_DATA_MAPPING = {
    "title": "TITLE",
    "author": "OWNER",
    "pid": "IRODS/PID",
    "name": normalize_name
}

OBJECT_META_DATA_MAPPING = {
    'title': 'Title',
    'url': 'url',
    'name': 'name',
    'pid': 'IRODS/PID',
    'PhotometricInterpretation': 'PhotometricInterpretation',
    'Manufacturer': 'Manufacturer',
    'InstanceCreationTime': get_date_time,
    'InstitutionName': 'InstitutionName',
    'InstitutionalDepartmentName': 'InstitutionalDepartmentName',
    'ScanOptions': 'ScanOptions',
    'PatientPosition': 'PatientPosition',
    'PixelDataSize': get_pixel_data_size
}


def irods_validate_meta_data(ibcontext, **kwargs):
    """
    Validate meta data
    """
    cfg = ibcontext['irods'].get_config(kwargs)
    key = {'irods_zone': get_irods_zone(cfg),
           'irods_collection': cfg['irods_collection']}
    data = ibcontext['cache'].read(key)
    if data is None:
        raise ValueError('collection not found in cache: {0} (zone: {1})'
                         .format(key['irods_collection'],
                                 key['irods_zone']))
    validate_collection_meta_data(data,
                                  cfg['irods_collection'],
                                  COLLECTION_META_DATA_VALIDATION)

    validate_objects_meta_data(data,
                               cfg['irods_collection'],
                               OBJECT_META_DATA_VALIDATION)


def irods_transform_meta_data(ibcontext, **kwargs):
    """
    Transform meta data
    """
    cfg = ibcontext['irods'].get_config(kwargs)
    key = {'irods_zone': get_irods_zone(cfg),
           'irods_collection': cfg['irods_collection']}
    data = ibcontext['cache'].read(key)
    if data is None:
        raise ValueError('collection not found in cache: {0} (zone: {1})'
                         .format(key['irods_collection'],
                                 key['irods_zone']))

    data = extract_irods_collecion_data(ibcontext['cache'].read(key),
                                        cfg['irods_collection'])
    md = {cfg['irods_collection']:
          transform_meta_data(data['meta_data'], COLLECTION_META_DATA_MAPPING)}
    for obj in data['objects']:
        obj['meta_data']['name'] = os.path.basename(obj['path'])
        md[obj['path']] = transform_meta_data(obj['meta_data'],
                                              OBJECT_META_DATA_MAPPING)
    ibcontext['cache'].update(key, {'target_meta_data': md})
