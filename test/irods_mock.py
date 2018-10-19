import os
import json
from collections import namedtuple
from irods.exception import CollectionDoesNotExist


class iRodsMetaData(object):
    def __init__(self, lst):
        self._items = [namedtuple("Meta",
                                  d.keys())(*d.values())
                       for d in lst]

    def items(self):
        return self._items

    def keys(self):
        return [i.name for i in self._items]


class iRodsCollection(object):
    def __init__(self, obj):
        self.metadata = iRodsMetaData(obj.get('metadata', []))
        self.subcollections = [iRodsCollection(s)
                               for s in obj.get('subcollections', [])]
        self.data_objects = []


class iRodsCollectionsMock(object):
    def __init__(self):
        self.collection_dir = os.path.dirname(os.path.abspath(__file__))

    def get(self, ipath):
        fname = os.path.join(self.collection_dir,
                             ipath.replace('/', '#') + ".json")
        if os.path.isfile(fname):
            with open(fname) as fp:
                return iRodsCollection(json.load(fp))
        else:
            raise CollectionDoesNotExist(ipath)


class iRodsSessionMock(object):
    def __init__(self):
        self.collections = iRodsCollectionsMock()
        self.host = "http://localhost"
