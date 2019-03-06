# fix for python2: cannot import from global package "irods" due to existence of
# local one with the same name.
# to import iRODSSession:
# from irods_session iRODSSession

import irods.session
iRODSSession = irods.session.iRODSSession

