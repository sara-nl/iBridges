class Draft(object):
    argument_prefix = None

    @staticmethod
    def add_arguments(parser):
        raise NotImplementedError("add_arguments not implemented")

    @property
    def uri(self):
        raise NotImplementedError("uri not implemented")

    @property
    def url(self):
        raise NotImplementedError("url not implemented")

    @property
    def publicId(self):
        raise NotImplementedError("publicId not implemented")

    @property
    def repoName(self):
        raise NotImplementedError("repoName not implemented")

    @property
    def hasData(self):
        raise NotImplementedError("hasData not implemented")

    @property
    def hasObjectMetaData(self):
        return False

    def validateMetaData(self, ipc):
        raise NotImplementedError("validateMetaData not implemented")

    def create(self, title):
        raise NotImplementedError("create not implemented")

    def patch(self, metadata, collPath='irods'):
        raise NotImplementedError("patch not implemented")

    def patchMetaData(self, objects, coll):
        raise NotImplementedError("patchMetaData not implemented")

    def patchTickets(self, tickets):
        raise NotImplementedError("patchTickets not implemented")

    def patchPIDs(self, tickets):
        raise NotImplementedError("patchPIDs not implemented")

    def uploadFile(self, path):
        raise NotImplementedError("uploadFile not implemented")

    def publish(self):
        raise NotImplementedError("publish not implemented")
