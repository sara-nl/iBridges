import os
import json
from .ibridges import iBridgesConnection


class iBridgesCache(iBridgesConnection):
    ARGUMENTS = [('ib_workdir',
                  'iBridges working directory')]

    def mkdir(self):
        workdir = os.path.expanduser(self.config['ib_workdir'])
        if not os.path.exists(workdir):
            os.makedirs(workdir)
        return workdir

    def write(self, key, document):
        key = key.replace('/', '#')
        with self.open(key, "wb") as fp:
            json.dump(document, fp, indent=4)

    def read(self, key):
        key = key.replace('/', '#')
        with self.open(key, "r") as fp:
            return json.load(fp)

    def open(self, key, mode='r'):
        workdir = self.mkdir()
        return open(os.path.join(workdir, '{0}.json'.format(key)), mode)
