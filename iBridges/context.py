import json
import connection
import os


class Context(object):
    @staticmethod
    def add_cli_args(config_file, parser, search_path=None):
        """ add configuration specific CLI arguments to
            argument parser
        """
        ret = []
        if not os.path.isabs(config_file) and search_path is not None:
            config_file = os.path.normpath(os.path.join(search_path,
                                                        config_file))
        with open(config_file) as fp:
            config = json.load(fp)
            for k, cfg in config.items():
                klass = Context.get_connection_class(cfg)
                if klass is not None and hasattr(klass, 'add_cli_args'):
                    gr = klass.add_cli_args(parser)
                    if gr is not None:
                        ret.append(gr)
        return ret

    @staticmethod
    def get_connection_class(cfg):
        """ determine connection class from configuration entry
        """
        if '_connection' not in cfg:
            return None
        connection_class_name = cfg.pop('_connection')
        try:
            if hasattr(connection, connection_class_name):
                connection_class = getattr(connection,
                                           connection_class_name)
                return connection_class
            else:
                raise ImportError('{0} not a standard Connector'
                                  .format(connection_class_name))
        except ImportError:
            # todo fallback solution, plugins
            raise

    def __init__(self, config_file, parser_args=None, search_path=None):
        self._connectors = {}
        self._config = {}
        self.config_file = config_file
        self.search_path = search_path
        self.parser_args = parser_args

    def __getitem__(self, key):
        if key not in self._connectors:
            self.load_config()
        if key not in self._connectors:
            raise KeyError('{0} not configured'.format(key))
        else:
            return self._connectors[key]

    def load_config(self):
        config_file = self.config_file
        if not os.path.isabs(config_file) and self.search_path is not None:
            config_file = os.path.normpath(os.path.join(self.search_path,
                                                        config_file))
        with open(config_file) as fp:
            self.config = json.load(fp)
            for k, cfg in self.config.items():
                klass = Context.get_connection_class(cfg)
                if klass is not None:
                    if hasattr(klass, 'add_cli_args_to_kwargs'):
                        klass.add_cli_args_to_kwargs(self.parser_args, cfg)
                    self._connectors[k] = klass(**cfg)
