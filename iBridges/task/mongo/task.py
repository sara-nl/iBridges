__all__ = ['test_connection']


def test_connection(ibcontext, **kwargs):
    ibcontext['cache'].test_connection()
