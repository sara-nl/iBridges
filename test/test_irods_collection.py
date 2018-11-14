import unittest
from mock import patch
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

    def test_assign_series_information(self):
        session = iRodsSessionMock()
        coll = iRodsCollection("collection_with_data", session)
        self.assertEqual(coll.getMetaData(), {})
        coll.assignSeriesInformation()
        self.assertEqual(coll.getMetaData(),
                         {'SERIESINFORMATION':
                          'iRODS Collection collection_with_data'})

    def test_assign_ticket(self):
        # @todo implement this test
        pass

    @patch('uuid.uuid1')
    def test_assign_pid(self, mock_uuid1):
        session = iRodsSessionMock()
        coll = iRodsCollection("collection_with_data", session)
        mock_uuid1.side_effect = ['1', '2', '3', '4']
        self.assertEqual(coll.assignPID("client", all=True),
                         {'collection_with_data': '1',
                          'object1.txt': '2',
                          'object2.txt': '3',
                          'object3.txt': '4'})

    def test_close_data_object(self):
        session = iRodsSessionMock()
        coll = iRodsCollection("collection_with_data", session)
        owners = coll.close(set(['me']))
        obj1 = 'collection_with_data/object1.txt'
        obj2 = 'collection_with_data/object2.txt'
        obj3 = 'collection_with_data/object3.txt'
        self.assertEqual(owners, set(['me', 'owner1', 'owner3', 'auto']))
        self.assertEqual(session.permissions._data['collection_with_data'],
                         {'auto#mock': 'read',
                          'me#mock': 'read',
                          'owner1#mock': 'read',
                          'owner3#mock': 'read',
                          'public#mock': 'read'})
        self.assertEqual(session.permissions._data[obj1],
                         {'me#mock': 'read',
                          'owner1#mock': 'read',
                          'public#mock': 'read'})
        self.assertEqual(session.permissions._data[obj2],
                         {'auto#mock': 'read',
                          'me#mock': 'read',
                          'owner1#mock': 'read',
                          'public#mock': 'read'})
        self.assertEqual(session.permissions._data[obj3],
                         {'auto#mock': 'read',
                          'me#mock': 'read',
                          'owner1#mock': 'read',
                          'owner3#mock': 'read',
                          'public#mock': 'read'})
        coll.open(owners)
        self.assertEqual(session.permissions._data['collection_with_data'],
                         {'auto#mock': 'write',
                          'me#mock': 'write',
                          'owner1#mock': 'write',
                          'owner3#mock': 'write',
                          'public#mock': 'read'})
        self.assertEqual(session.permissions._data[obj1],
                         {'auto#mock': 'write',
                          'me#mock': 'write',
                          'owner1#mock': 'write',
                          'owner3#mock': 'write',
                          'public#mock': 'read'})
        self.assertEqual(session.permissions._data[obj2],
                         {'auto#mock': 'write',
                          'me#mock': 'write',
                          'owner1#mock': 'write',
                          'owner3#mock': 'write',
                          'public#mock': 'read'})
        self.assertEqual(session.permissions._data[obj3],
                         {'auto#mock': 'write',
                          'me#mock': 'write',
                          'owner1#mock': 'write',
                          'owner3#mock': 'write',
                          'public#mock': 'read'})
