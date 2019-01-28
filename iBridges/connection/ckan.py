import requests
import pprint
from .ibridges import iBridgesConnection


class CkanConnection(iBridgesConnection):
    ARGUMENTS = [('ckan_api_token',
                  'API token'),
                 ('ckan_api_url',
                  'CKAN url'),
                 ('cakn_org',
                  'CKAN organization')]

    def log_rest_error(self, action_url, res, data=None):
        msg = 'failed to perform rest call: {0}'.format(action_url)
        self.logger.error(msg)
        if data is not None:
            self.logger.error('data:')
            for line in pprint.pformat(data, indent=4).split('\n'):
                self.logger.error(line)
        try:
            errdata = pprint.pformat(res.json(), indent=4)
        except Exception:
            errdata = res.text
        self.logger.error('result:')
        for line in errdata.split('\n'):
            self.logger.error(line)

    def action(self, action, data=None, method=None):
        if data is None:
            data = {}
        if method is None:
            method = 'get'
        if method == 'get':
            data_method = 'params'
        elif method in ['put', 'post']:
            data_method = 'data'
        else:
            msg = 'method {0} not supported'.format(method)
            raise NotImplementedError(msg)
        _action = getattr(requests, method)
        api_url = self.config['ckan_api_url']
        action_url = '{api}/action/{action}'.format(api=api_url,
                                                    action=action)
        api_token = self.config['ckan_api_token']
        self.logger.debug('request {0}'.format(action_url))
        res = _action(action_url,
                      **{data_method: data,
                         'headers': {'Authorization': api_token}})
        try:
            res.raise_for_status()
        except Exception:
            self.log_rest_error(action_url, res, data=data)
            raise
        return res.json()
