import os
from pymongo import MongoClient
from pymongo import ASCENDING
from .ibridges import iBridgesConnection


def encode_struct(document):
    def encode_str(k):
        k = k.replace("\\", "\\\\")
        k = k.replace("$", "\\u0024")
        k = k.replace(".", "\\u002e")
        return k

    if isinstance(document, dict):
        return {encode_str(k): encode_struct(v) for k, v in document.items()}
    elif isinstance(document, list):
        return [encode_struct(item) for item in document]
    else:
        return document


def decode_struct(document):
    def decode_str(k):
        k = k.replace("\\\\", "\\")
        k = k.replace("\\u0024", "$")
        k = k.replace("\\u002e", ".")
        return k

    if isinstance(document, dict):
        return {decode_str(k): decode_struct(v) for k, v in document.items()}
    elif isinstance(document, list):
        return [decode_struct(item) for item in document]
    else:
        return document


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
        import pprint
        pprint.pprint(encode_struct(document))
        return collection.insert_one(encode_struct(document)).inserted_id

    def read(self, key):
        document = self.collection.find_one(encode_struct(key))
        return decode_struct(document)

    def open(self, key, mode='r'):
        workdir = self.mkdir()
        return open(os.path.join(workdir, '{0}.json'.format(key)), mode)

    def update(self, key, sub_doc):
        key = encode_struct(key)
        obj = {'$set': encode_struct(sub_doc)}
        self.collection.update_one(key, obj)

    def remove_if_exists(self, key):
        key = encode_struct(key)
        self.collection.delete_one(key)

    def test_connection(self):
        db = self.client[self.config.get('mongodb')]
        if db is None:
            raise RuntimeError('cannot connect to mongo db')
