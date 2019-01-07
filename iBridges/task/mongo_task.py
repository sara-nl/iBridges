__all__ = ['mongo_test_connection']


def mongo_test_connection(ibcontext, **kwargs):
    ibcontext['cache'].test_connection()
