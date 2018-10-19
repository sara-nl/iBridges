import sys
import os
import irods_repository_connector
sys.path.insert(0,
                os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             "dataverse-client-python"))
# default draft directory
sys.path.insert(0,
                os.path.join(os.path.dirname(__file__),
                             "drafts"))

iRodsRepositoryConnector = irods_repository_connector.iRodsRepositoryConnector
