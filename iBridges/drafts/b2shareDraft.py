"""
@licence: Apache 2.0
@Copyright (c) 2018, Christine Staiger (SURFsara)
@author: Christine Staiger
@author: Stefan Wolfsheimer
"""

import os
import logging
import json
import uuid
import requests
#from urllib2 import urlopen
#from urllib2 import Request
#from urllib2 import quote
#from urllib2 import HTTPError
#from iBridges.draft import Draft


class B2shareDraft():
    argument_prefix = "b2share"

    @staticmethod
    def add_arguments(parser):
        fields = ['api_token', 'api_url', 'org', 'id', 'group']
        for i in fields:
            parser.add_argument('--b2share_' + i,
                                type=str)

    def __init__(self, api_token, api_url, org, draftUrl=None):
        self.logger = logging.getLogger('ipublish')
        self.apiToken = api_token
        self.apiUrl = api_url
        self.b2shareOrg = org
        self.draftUrl   = draftUrl
        self.__dataset = None
        self.B2shareID = None

    @property
    def uri(self):
        return self.apiUrl

    @property
    def url(self):
        return self.apiUrl

    @property
    def publicId(self):
        return self.B2shareID

    @property
    def repoName(self):
        return 'B2SHARE'

    @property
    def hasData(self):
        return True

    def validateMetaData(self, ipc):
        required = ['TITLE', 'ABSTRACT', 'CREATOR', 'SERIESINFORMATION', 'OTHER']
        if not set(required).issubset(ipc.md.keys()):
            self.logger.error('%s PUBLISH ERROR: Keys not defined: ',
                              self.repoName)
            self.logger.error(' ' + str(set(required).
                                        difference(ipc.md.keys())))
            return False
        else:
            self.logger.info('%s PUBLISH NOTE: all metadata defined:',
                             self.repoName)
            self.logger.info(' ' + str(required))
            return True

    def create(self, title):
        '''
        Create a draft in B2SHARE.
        '''
        if self.draftUrl != None:
            self.logger.info('%s PUBLISH NOTE: Draft already exists.', self.repoName)
            #set draft ID
            self.draftId = requests.get(self.draftUrl).json()['id'] 
            return
        
        #create draft
        createUrl = self.apiUrl + "records/?access_token=" + self.apiToken
        data = '{"titles":[{"title":"'+title+'"}], "community":"' + self.b2shareOrg + \
            '", "open_access":true, "community_specific": {}}'
        headers = {"Content-Type":"application/json"}
        try:
            request = requests.post(url = createUrl, headers=headers, data = data )
            self.draftUrl = self.apiUrl + "records/" + request.json()['id'] + "/draft?access_token=" + self.apiToken
            self.draftId = request.json()['id']
        except Exception as e:
        #request.status_code not in range(200, 300):
            print 'B2SHARE PUBLISH ERROR: Draft not created: ' + str(request.status_code)
            self.logger.error('B2SHARE PUBLISH ERROR: Draft not created: ' + str(request.status_code)) 
            raise   
 
    def patch(self, metadata, collPath='irods'):
        '''
        Adds and updates metadata to a B2SHARE draft.
        Mandatory metadata entries: CREATOR, TITLE, ABSTRACT, SUBJECT
        If data is not uploaded it is advised to provide pids pointing
        to the data in iRODS or
        to provide tickets for anonym ous data download.
        NOTE: If the draft already contains files,
        the update of metadata will fail.
        Parameters:
        metadata = ipc.getMetaData()
        collPath = iRODS path or webdav access to collection or data object
        '''
        headers = {"Content-Type":"application/json-patch+json"}
       
 
        # CREATOR --> creators
        patch = '[{"op":"add","path":"/creators","value":[{"creator_name":"' + \
            metadata['CREATOR'] + '"}]}]'
        response = requests.patch(url=self.draftUrl, headers=headers, data=patch)
        if response.status_code not in range(200, 300):
            print('B2SHARE PUBLISH ERROR: Draft not patched with creators. ' + \
            str(response.status_code))
        else:
            print "added creator"

        patch = '[{"op":"add","path":"/descriptions","value":[{"description":"'+ metadata['ABSTRACT'] + \
            '", "description_type":"Abstract"},{"description":"'+ metadata['OTHER'] + \
            '", "description_type":"Other"},{"description":"'+metadata['SERIESINFORMATION'] + \
            '", "description_type":"SeriesInformation"}]}]'

        response = requests.patch(url=self.draftUrl, headers=headers, data=patch)

        if response.status_code not in range(200, 300) and response.status_code!=500:
            print('B2SHARE PUBLISH ERROR: Draft not patched with description. ' + \
            str(response.status_code))
        else:
            print "added abstract, other, seriesinformation"


    def patchTickets(self, tickets):
        print "Not implemented"

    def patchPIDs(self, pids):
        prefix = 'hdl.handle.net/'
        self.patchRefs({'key': 'File Handles',
                        'value': str([os.path.basename(ref) +
                                      '> ' + prefix + value
                                      for ref, value in pids.items()])})

    def patchRefs(self, obj):
        '''
        Patches a draft with tickets and pids for data objects
        as otherReferences.
        Expects a dictionary irods obj path --> ticket
        '''
        errorMsg = []
        headers = {"Content-Type":"application/json-patch+json"}
        tmp = []
        for pid in obj:
            tmp.append('{"alternate_identifier": "'+obj[pid]+\
                '", "alternate_identifier_type": "EPIC;'+\
                pid+'"}')
        patch = '[{"op":"add","path":"/alternate_identifiers","value":[' + ','.join(tmp)+']}]'
        request = requests.patch(url=self.draftUrl, headers=headers, data=patch)
        if request.status_code not in range(200, 300):
            errorMsg.append('B2SHARE PUBLISH ERROR: Draft not patched with pids. ' + str(request.status_code))

        return errorMsg

    def uploadData(self, folder):
        '''
        Uploads local files from a folder to the draft.
        '''
        r = json.loads(requests.get(self.draftUrl).text)

        for f in os.listdir(folder):
            upload_files_url = r['links']['files'] + "/" + f + "?access_token=" + self.apiToken
            file = open(folder+"/"+f, 'rb')
            headers = {'Accept':'application/json',
                'Content-Type':'application/octet-stream --data-binary'}
            response = requests.put(url=upload_files_url,
                headers = headers, data = file)
            if response.status_code not in range(200, 300):
                print('B2SHARE PUBLISH ERROR: File not uploaded ' +
                    folder+"/"+f +', ' + str(request.status_code))

    def publish(self):

        headers = {"Content-Type":"application/json-patch+json"}
        patch = '[{"op":"add", "path":"/publication_state", "value":"submitted"}]'
        response = requests.patch(url=self.draftUrl, headers=headers, data=patch)
        r = json.loads(requests.get(self.draftUrl).text)    
        self.B2shareID = r['metadata']['DOI']        

