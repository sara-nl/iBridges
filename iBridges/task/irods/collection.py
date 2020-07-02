import os
import copy
from irods.access import iRODSAccess


class iRodsCollection(object):
    """
    A class representing the iRods collection
    """
    def __init__(self, session, collection_path,
                 target_user=None, target_zone=None):
        self.session = session
        self.collection_path = collection_path
        self.target_users = {}
        self.target_users[(self.session.username, self.session.zone)] = True
        if target_user is not None:
            if target_zone is None:
                target_zone = self.session.zone
            self.target_users[(target_user, target_zone)] = True
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
        """
        Change the ownership to current user.
        Set readonly ownership to original user.
        Return json document.
        """
        ret = self.data
        coll = self.session.collections.get(self.collection_path)
        perm = self.session.permissions
        for collection, subcollections, objects in coll.walk(topdown=True):
            union = objects + [collection]
            for ooc in union:
                for acl in perm.get(ooc, expand_groups=False):
                    cacl = copy.copy(acl)
                    if cacl.access_name == 'read object':
                        cacl.access_name = 'read'
                    p = (cacl.user_name, cacl.user_zone)
                    if p not in self.target_users:
                        acc = iRODSAccess('read',
                                          acl.path,
                                          acl.user_name,
                                          acl.user_zone)
                        perm.set(acc, admin=True)
                for p in self.target_users.keys():
                    perm.set(iRODSAccess('own',
                                         ooc.path,
                                         p[0],
                                         p[1]),
                             admin=True)
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
                    self.session.permissions.set(acc, admin=True)
                    old_access[(acc.user_name, acc.user_zone)] = acc
                if ooc['type'] == 'collection':
                    iooc = self.session.collections.get(ooc['path'])
                else:
                    iooc = self.session.data_objects.get(ooc['path'])
                for acl in self.session.permissions.get(iooc,
                                                        expand_groups=False):
                    pair = (acl.user_name, acl.user_zone)
                    if pair not in old_access:
                        acc = iRODSAccess('null',
                                          str(ooc['path']),
                                          pair[0],
                                          pair[1])
                        self.session.permissions.set(acc, admin=True)

    def remove_ownership(self):
        coll = self.session.collections.get(self.collection_path)
        for collection, subcollections, objects in coll.walk(topdown=True):
            union = objects + [collection]
            for ooc in union:
                for acl in self.session.permissions.get(ooc,
                                                        expand_groups=False):
                    for pair in self.target_users.keys():
                        acc = iRODSAccess('null',
                                          ooc.path,
                                          pair[0],
                                          pair[1])
                        self.session.permissions.set(acc, admin=True)

    def _update_data(self):
        lookup = {}
        self._data = []
        coll = self.session.collections.get(self.collection_path)
        for collection, subcollections, objects in coll.walk(topdown=True):
            acls = {acl.user_name: vars(acl)
                    for acl in self.session.permissions.get(collection,
                                                            expand_groups=False)}
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
        perm = self.session.permissions
        return [{'type': 'object',
                 'path': obj.path,
                 'meta_data': self._get_meta_data(obj),
                 'parent': parent,
                 'acls': {acl.user_name: vars(acl)
                          for acl in perm.get(obj,
                                              expand_groups=False)}}
                for obj in objects]
