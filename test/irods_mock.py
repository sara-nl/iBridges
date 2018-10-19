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


class iRodsDataObject(object):
    def __init__(self, parent, obj):
        self.collection = parent
        self.name = obj.get('name')
        self.metadata = iRodsMetaData(obj.get('metadata', []))

    @property
    def size(self):
        return os.path.getsize(self.real_path)

    @property
    def path(self):
        return os.path.join(self.collection.ipath, self.name)

    @property
    def real_path(self):
        return os.path.join(self.collection.session.collection_dir,
                            self.collection.ipath.replace('/', '#'),
                            self.name)


class iRodsCollection(object):
    def __init__(self, session, ipath, obj, parent=None):
        self.parent = parent
        self.session = session
        self.ipath = ipath
        self.metadata = iRodsMetaData(obj.get('metadata', []))
        self.subcollections = [iRodsCollection(session, s, parent=self)
                               for s in obj.get('subcollections', [])]
        self.data_objects = [iRodsDataObject(self, o)
                             for o in obj.get('data_objects', [])]


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


class iRodsSessionMock(object):
    def __init__(self):
        self.collection_dir = os.path.dirname(os.path.abspath(__file__))
        self.collections = iRodsCollectionsMock(self)
        self.data_objects = iRodsDataObjectsMock(self)
        self.host = "http://localhost"
