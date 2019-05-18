from .irods_session import iRODSSession
from os.path import expanduser
from .ibridges import iBridgesConnection


class CollectionMetaDataMapping(iBridgesConnection):
    ARGUMENTS = [("collection_validator", ""),
                 ("object_validator", ""),
                 ("collection_mapper", ""),
                 ("object_mapper", "")]

    pass


class iRodsConnection(iBridgesConnection):
    ARGUMENTS = [('irods_env_file',
                  'path to irods env. file'),
                 ('irods_authentication_file',
                  'path to irods env. file'),
                 ('irods_host',
                  'irods host'),
                 ('irods_http_endpoint',
                  'http or davrods endpoint'),
                 ('irods_user',
                  'irods user'),
                 ('irods_zone',
                  'irods zone'),
                 ('irods_collection',
                  'irods collection to process')]

    def session(self):
        file_args = ["irods_authentication_file",
                     "irods_env_file"]
        kwargs = {k: expanduser(f) if k in file_args else f
                  for k, f in self.config.items()}
        return iRODSSession(**kwargs)
