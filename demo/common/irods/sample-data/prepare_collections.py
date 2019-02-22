#!/usr/bin/env python
import os
import json
# import exifread
from irods.session import iRODSSession
from irods.exception import UserGroupDoesNotExist
from irods.exception import UserDoesNotExist
from irods.access import iRODSAccess
import irods.keywords as kw


def create_data_owners(session):
    try:
        group = session.user_groups.get('data_owners')
    except UserGroupDoesNotExist:
        group = session.user_groups.create('data_owners')
    except Exception:
        raise
    users = ['john', 'mara']
    for uname in users:
        try:
            user = session.users.get(uname)
        except UserDoesNotExist:
            user = session.users.create(uname, 'rodsuser')
            group.addmember(user.name)
        except Exception:
            raise


def write_collection(session, data):
    collname = '/tempZone/public/{0}'.format(data['collection'])
    print("create {0}".format(collname))
    # options = {kw.COLL_OWNER_NAME_KW: data['metadata']['OWNER']}
    options = {}
    coll = session.collections.create(collname, **options)
    session.permissions.set(iRODSAccess('own',
                                        coll.path,
                                        data['metadata']['OWNER'],
                                        'tempZone'))
    for k, v in data['metadata'].items():
        coll.metadata.add(k, str(v))
    for k, obj in data['objects'].items():
        objpath = os.path.join(collname, k)
        print("put {0} -> {1}".format(obj['file'], objpath))
        options = {kw.DATA_OWNER_KW: data['metadata']['OWNER']}
        session.data_objects.put(obj['file'], objpath, **options)
        irods_obj = session.data_objects.get(objpath)
        for k, v in obj['metadata'].items():
            v = str(v)
            v = v[:2048]
            print("meta data {0} '{1}' '{2}'".format(objpath, k, v))
            irods_obj.metadata.add(k, v)
        session.permissions.set(iRODSAccess('own',
                                            objpath,
                                            data['metadata']['OWNER'],
                                            'tempZone'))
        session.permissions.set(iRODSAccess('null',
                                            objpath,
                                            'rods',
                                            'tempZone'))
    session.permissions.set(iRODSAccess('null',
                                        coll.path,
                                        'rods',
                                        'tempZone'))


def read_space_in_images(directory=None):
    if directory is None:
        directory = "SpaceInImages"
    dirname = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                           directory)
    with open(os.path.join(dirname, "metadata.json")) as fp:
        metadata = json.load(fp)
    ret = {'path': dirname,
           'collection': directory,
           'metadata': metadata,
           'objects': {}}
    for root, d, files in os.walk(dirname):
        for f in [x for x in files if x.endswith(".jpg")]:
            absfile = os.path.join(dirname, f)
            metafile = os.path.join(dirname, f.replace('.jpg', '.json'))
            with open(metafile) as fp:
                metadata = json.load(fp)
            ret['objects'][f] = {'file': absfile,
                                 'metadata': metadata}
    return ret


def main():
    with iRODSSession(host='localhost',
                      port=1247,
                      user='rods',
                      password='test',
                      zone='tempZone') as session:
        # test connection
        coll = session.collections.get("/tempZone/home/rods")
        create_data_owners(session)
        data = read_space_in_images()
        write_collection(session, data)


if __name__ == "__main__":
    main()
