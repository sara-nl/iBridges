from .ibridges import iBridgesConnection


class B2ShareConnection(iBridgesConnection):
    ARGUMENTS = [('b2share_api_token',
                  'API token'),
                 ('b2share_api_url',
                  'B2SAHRE endpoint'),
                 ('b2share_community',
                  'B2SHARE community')]
