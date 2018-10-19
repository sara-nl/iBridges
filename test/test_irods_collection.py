import unittest
from iBridges import iRodsCollection
from irods_mock import iRodsSessionMock


class TestIRodsCollection(unittest.TestCase):
    def test_empty_collection(self):
        session = iRodsSessionMock()
        coll = iRodsCollection("empty_collection", session)
        self.assertEqual(coll.uri, "irods://http://localhost/empty_collection")
        self.assertEqual(coll.size(), 0)
        self.assertFalse(coll.isPublished(['REPO/KEY']))
        self.assertFalse(coll.validate())
        self.assertEqual(coll.getMetaData(), {})
        self.assertEqual(coll.getMetaDataByKey("key"), {})
        self.assertEqual([f for f in coll.downloadCollection()], [])

    def test_read_collection_with_data(self):
        session = iRodsSessionMock()
        coll = iRodsCollection("collection_with_data", session)
        self.assertEqual(coll.uri,
                         "irods://http://localhost/collection_with_data")
        self.assertEqual(coll.size(), 30)
        self.assertFalse(coll.isPublished(['REPO/KEY']))
        self.assertTrue(coll.validate())
        self.assertEqual(coll.getMetaData(), {})
        self.assertEqual(coll.getMetaDataByKey("key"), {})
        self.assertEqual(len([f for f in coll.downloadCollection()]), 3)
