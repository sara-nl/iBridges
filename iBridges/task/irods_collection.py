import os
import copy
from irods.access import iRODSAccess


class iRodsCollection(object):
    def __init__(self, session, collection_path):
        self.session = session
        self.collection_path = collection_path
        self._data = None

    @property
    def key(self):
        """
        Unique key of collection (host, zone, path)
        """
        return "{0}#{1}#{2}".format(self.session.host,
                                    self.session.zone,
                                    self.collection_path)

    @property
    def data(self):
        """
        Serialize iRodsCollection as dictionary
        """
        if self._data is None:
            self._update_data()
        return self._data

    def lock(self):
        ret = self.data
        coll = self.session.collections.get(self.collection_path)
        for collection, subcollections, objects in coll.walk(topdown=True):
            union = objects + [collection]
            for ooc in union:
                for acl in self.session.permissions.get(ooc):
                    cacl = copy.copy(acl)
                    if cacl.access_name == 'read object':
                        cacl.access_name = 'read'
                    if cacl.user_name != self.session.username or \
                       cacl.user_zone != self.session.zone:
                        acc = iRODSAccess('read',
                                          acl.path,
                                          acl.user_name,
                                          acl.user_zone)
                        self.session.permissions.set(acc)
                self.session.permissions.set(iRODSAccess('own',
                                                         ooc.path,
                                                         self.session.username,
                                                         self.session.zone))
        return ret

    def unlock(self, data):
        for coll in data:
            union = coll['objects'] + [coll]
            for ooc in union:
                old_access = {}
                for acl in ooc['acls'].values():
                    acc = iRODSAccess(str(acl.get('access_name')),
                                      str(acl.get('path')),
                                      str(acl.get('user_name')),
                                      str(acl.get('user_zone')))
                    if acc.access_name == 'read object':
                        acc.access_name = 'read'
                    self.session.permissions.set(acc)
                    old_access[(acc.user_name, acc.user_zone)] = acc
                pair = (self.session.username, self.session.zone)
                if pair not in old_access:
                    acc = iRODSAccess('null',
                                      str(ooc['path']),
                                      self.session.username,
                                      self.session.zone)
                    self.session.permissions.set(acc)

    def remove_ownership(self):
        coll = self.session.collections.get(self.collection_path)
        for collection, subcollections, objects in coll.walk(topdown=True):
            union = objects + [collection]
            for ooc in union:
                for acl in self.session.permissions.get(ooc):
                    acc = iRODSAccess('null',
                                      ooc.path,
                                      self.session.username,
                                      self.session.zone)
                    self.session.permissions.set(acc)

    def _update_data(self):
        lookup = {}
        self._data = []
        coll = self.session.collections.get(self.collection_path)
        for collection, subcollections, objects in coll.walk(topdown=True):
            acls = {acl.user_name: vars(acl)
                    for acl in self.session.permissions.get(collection)}
            p = collection.path
            parent_coll = self._get_parent_collection(p)
            lookup[p] = len(self._data)
            self._data.append({'type': 'collection',
                               'path': collection.path,
                               'meta_data': self._get_meta_data(collection),
                               'objects': self._get_object_acls(objects, p),
                               'subcollections': [s.path
                                                  for s in subcollections],
                               'parent': parent_coll,
                               'acls': acls})

    def _get_parent_collection(self, p):
        if p != self.collection_path:
            return os.path.dirname(p)
        else:
            return None

    def _get_meta_data(self, collobj):
        return {item.name: item.value
                for item in collobj.metadata.items()}

    def _get_object_acls(self, objects, parent):
        return [{'type': 'object',
                 'path': obj.path,
                 'meta_data': self._get_meta_data(obj),
                 'parent': parent,
                 'acls': {acl.user_name: vars(acl)
                          for acl in self.session.permissions.get(obj)}}
                for obj in objects]
