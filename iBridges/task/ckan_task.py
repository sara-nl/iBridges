import logging


class CkanOrganizationNotFound(Exception):
    def __init__(self, orga):
        msg = "organization {0} not found in CKAN".format(orga)
        super(CkanOrganizationNotFound, self).__init__(msg)


def ckan_test_connection(ibcontext, **kwargs):
    logger = logging.getLogger('ipublish')
    config = ibcontext['ckan'].get_config(kwargs)
    logger.debug(config)
    result = ibcontext['ckan'].action('organization_list')
    if result['success']:
        if config['ckan_org'] not in result['result']:
            raise CkanOrganizationNotFound(config['ckan_org'])
    else:
        raise RuntimeError('CKAN connection error')
