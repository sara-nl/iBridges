class iBridgesConnection(object):
    ARGUMENTS = []

    @classmethod
    def add_cli_args(cls, parser):
        group = parser.add_argument_group('irods')
        for arg, h in cls.ARGUMENTS:
            group.add_argument('--{0}'.format(arg),
                               type=str,
                               help=h)
        return group

    @classmethod
    def add_cli_args_to_kwargs(cls, args, kwargs):
        for arg, h in cls.ARGUMENTS:
            if hasattr(args, arg) and getattr(args, arg) is not None:
                kwargs[arg] = getattr(args, arg)

    def __init__(self, **kwargs):
        self.config = kwargs

    def get_config(self, kwargs):
        config = self.config.copy()
        if 'dag_run' in kwargs:
            config.update(kwargs['dag_run'].conf)
        return config
