import datetime
import re
from iBridges.task.irods_task_utils import get_irods_zone
from iBridges.task.irods_task_utils import check_collection_metadata_fields
from iBridges.task.irods_task_utils import check_object_metadata_fields
from iBridges.task.irods_task_utils import get_target_metadata


__all__ = ['irods_validate_meta_data',
           'irods_transform_meta_data']


def get_pixel_data_size(obj):
    if 'PixelData' in obj:
        return len(obj.PixelData)
    else:
        return 0


def get_date_time(obj):
    if 'InstanceCreationTime' in obj and 'InstanceCreationDate' in obj:
        time = re.sub('([0-9]+)(\.[0-9]*)?', r'\1', obj.InstanceCreationTime)
        dtg = obj.InstanceCreationDate + '_' + time
        dt = datetime.datetime.strptime(dtg, "%Y%m%d_%H%M%S")
        return dt.isoformat()
    else:
        return ''


COLLECTION_META_DATA_MAPPING = {
    'TITLE': ("title", True),
    'OWNER': ("author", True)
}

OBJECT_META_DATA_MAPPING = {
    'Title': ('title', True),
    'url': ('url', True),
    'PhotometricInterpretation': ('PhotometricInterpretation', False),
    'Manufacturer': ('Manufacturer', False),
    'InstanceCreationTime': ('InstanceCreationTime', False, get_date_time),
    'InstitutionName': ('InstitutionName', False),
    'InstitutionalDepartmentName': ('InstitutionalDepartmentName', False),
    'ScanOptions': ('ScanOptions', False),
    'PatientPosition': ('PatientPosition', False),
    'PixelDataSize': ('PixelDataSize', False, get_pixel_data_size)
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
        raise ValueError('collection not found in cache: {0}'
                         .format(cfg['irods_collection']))
    check_collection_metadata_fields(data,
                                     COLLECTION_META_DATA_MAPPING)
    check_object_metadata_fields(data,
                                 OBJECT_META_DATA_MAPPING)


def irods_transform_meta_data(ibcontext, **kwargs):
    """
    Transform meta data
    """
    cfg = ibcontext['irods'].get_config(kwargs)
    key = {'irods_zone': get_irods_zone(cfg),
           'irods_collection': cfg['irods_collection']}
    data = ibcontext['cache'].read(key)
    if data is None:
        raise ValueError('collection not found in cache: {0}'
                         .format(cfg['irods_collection']))

    md = get_target_metadata(data,
                             collection_mapping=COLLECTION_META_DATA_MAPPING,
                             object_mapping=OBJECT_META_DATA_MAPPING)
    ibcontext['cache'].update(key, {'target_meta_data': md})
