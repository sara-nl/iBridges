from os.path import dirname
from os.path import basename
from irods.data_object import iRODSDataObject
from irods.collection import iRODSCollection
from irods.models import DataAccess
from irods.models import User
from irods.models import Collection
from irods.models import DataObject
from irods.models import CollectionAccess
from irods.exception import UserDoesNotExist
from irods.exception import NoResultFound
from irods.access import iRODSAccess


class PatchedAccessManager(object):
    def __init__(self, session):
        self.session = session
        self.orig_permissions = session.permissions

    def _get_user_by_id(self, user_id):
        q = self.session.query(User.name,
                               User.zone).filter(User.id == user_id)
        try:
            res = q.one()
            return res[User.name], res[User.zone]
        except NoResultFound:
            raise UserDoesNotExist()

    def get(self, target, *args, expand_groups=True, **kwargs):
        if expand_groups:
            for i in self.orig_permissions.get(target, *args, **kwargs):
                yield i
            raise StopIteration()
        else:
            if type(target) == iRODSDataObject:
                access_type = DataAccess
                conditions = [
                    Collection.name == dirname(target.path),
                    DataObject.name == basename(target.path)
                ]
            elif type(target) == iRODSCollection:
                access_type = CollectionAccess
                conditions = [
                    Collection.name == target.path
                ]
            else:
                raise TypeError
            results = self.session.query(access_type.user_id,
                                         access_type.name)\
                                  .filter(*conditions)\
                                  .all()
            for row in results:
                user, zone = self._get_user_by_id(row[access_type.user_id])
                access = iRODSAccess(access_name=row[access_type.name],
                                     user_name=user,
                                     path=target.path,
                                     user_zone=zone)
                yield access
            raise StopIteration()

    def set(self, *args, **kwargs):
        return self.orig_permissions.set(*args, **kwargs)
