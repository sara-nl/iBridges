import requests
from ibridges_connection import iBridgesConnection


class CkanConnection(iBridgesConnection):
    ARGUMENTS = [('ckan_api_token',
                  'API token'),
                 ('ckan_api_url',
                  'CKAN url'),
                 ('cakn_org',
                  'CKAN organization')]

    def action(self, action, data=None):
        if data is None:
            data = {}
        action_url_fmt = '{api}/action/{action}'
        action_url = action_url_fmt.format(api=self.config['ckan_api_url'],
                                           action=action)

        self.logger.debug('request {0}'.format(action_url))
        res = requests.get(action_url, params=data)
        return res.json()
