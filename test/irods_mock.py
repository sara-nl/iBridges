import os
import json
from collections import namedtuple
from irods.exception import CollectionDoesNotExist
from irods.exception import DataObjectDoesNotExist


class iRodsMetaData(object):
    def __init__(self, lst):
        self._items = [namedtuple("Meta",
                                  d.keys())(*d.values())
                       for d in lst]

    def items(self):
        return self._items

    def keys(self):
        return [i.name for i in self._items]

    def add(self, k, value):
        self._items.append(namedtuple("Meta",
                                      ['name', 'value'])(k, value))


class iRodsDataObject(object):
    def __init__(self, parent, obj):
        self.collection = parent
        self.name = obj.get('name')
        self.owner_name = obj.get('owner_name', 'auto')
        self.metadata = iRodsMetaData(obj.get('metadata', []))

    @property
    def size(self):
        return os.path.getsize(self.real_path)

    @property
    def path(self):
        return os.path.join(self.collection.path, self.name)

    @property
    def real_path(self):
        return os.path.join(self.collection.session.collection_dir,
                            self.collection.path.replace('/', '#'),
                            self.name)


class iRodsCollection(object):
    def __init__(self, session, ipath, obj, parent=None):
        self.parent = parent
        self.session = session
        self.path = ipath
        self.name = os.path.basename(ipath)
        self.owner_name = obj.get('owner_name', 'auto')
        self.metadata = iRodsMetaData(obj.get('metadata', []))
        self.subcollections = [iRodsCollection(session, s, parent=self)
                               for s in obj.get('subcollections', [])]
        self.data_objects = [iRodsDataObject(self, o)
                             for o in obj.get('data_objects', [])]

    @property
    def zone(self):
        return self.session.zone


class iRodsCollectionsMock(object):
    def __init__(self, session):
        self.session = session
        self.collections = {}

    def get(self, ipath):
        if ipath not in self.collections:
            fname = os.path.join(self.session.collection_dir,
                                 ipath.replace('/', '#') + ".json")
            if os.path.isfile(fname):
                with open(fname) as fp:
                    coll = iRodsCollection(self.session,
                                           ipath,
                                           json.load(fp))
                    self.collections[ipath] = coll
            else:
                raise CollectionDoesNotExist(ipath)
        return self.collections[ipath]


class iRodsDataObjectsMock(object):
    def __init__(self, session):
        self.session = session

    def get(self, path):
        name = os.path.basename(path)
        coll = self.session.collections.get(os.path.dirname(path))
        for obj in coll.data_objects:
            if obj.name == name:
                return obj
        raise DataObjectDoesNotExist(path)

    def open(self, path, mode):
        obj = self.get(path)
        return open(obj.real_path, mode)


class iRodsPermissionsMock(object):
    def __init__(self, session):
        self.session = session
        self._data = {}

    def set(self, acl):
        user_zone = '{0}#{1}'.format(acl.user_name, acl.user_zone)
        if acl.path not in self._data:
            self._data[acl.path] = {}
        self._data[acl.path][user_zone] = acl.access_name


class iRodsSessionMock(object):
    def __init__(self):
        self.host = "http://localhost"
        self.zone = "mock"
        self.collection_dir = os.path.dirname(os.path.abspath(__file__))
        self.collections = iRodsCollectionsMock(self)
        self.data_objects = iRodsDataObjectsMock(self)
        self.permissions = iRodsPermissionsMock(self)
