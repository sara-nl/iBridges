import os
from pymongo import MongoClient
from pymongo import ASCENDING
from ibridges_connection import iBridgesConnection


class iBridgesMongo(iBridgesConnection):
    ARGUMENTS = [('mongodb_url', 'MongoDB connection string'),
                 ('mongodb', 'MongoDB name'),
                 ('mongodb_collection', 'collection name')]

    def __init__(self, *args, **kwargs):
        super(iBridgesMongo, self).__init__(*args, **kwargs)
        self.client = MongoClient(self.config.get('mongodb_url'))

    @property
    def collection(self):
        db = self.client[self.config.get('mongodb')]
        return db[self.config.get('mongodb_collection')]

    def write(self, key, document):
        collection = self.collection
        collection.create_index([(k, ASCENDING) for k in key],
                                unique=True)
        return collection.insert_one(document).inserted_id

    def read(self, key):
        return self.collection.find_one(key)

    def open(self, key, mode='r'):
        workdir = self.mkdir()
        return open(os.path.join(workdir, '{0}.json'.format(key)), mode)

    def test_connection(self):
        db = self.client[self.config.get('mongodb')]
        if db is None:
            raise RuntimeError('cannot connect to mongo db')
