#!/usr/bin/env python
import sys
import argparse
import importlib
import pprint
from context import Context
import task
from logger import LoggerFactory


def get_task_func(args, task_name):
    """
    Get the function for that task from name.
    First it searches the default task module.
    If it is not a standard task, the function
    is searched in a plugin module.
    """
    if hasattr(task, task_name):
        return getattr(task, task_name)
    else:
        module_path = task_name.split('.')
        module_name = '.'.join(module_path[:-1])
        func_name = module_path[-1]
        try:
            mod = importlib.import_module(module_name)
        except ImportError as e:
            print(str(e))
            pprint.pprint(sys.path)
            raise
        except Exception:
            raise
        if hasattr(mod, func_name):
            return getattr(mod, func_name)
        else:
            msg = 'function {0} not found in module {1}'.format(func_name,
                                                                module_name)
            raise ImportError(msg)


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--config', '-c',
                        type=str,
                        help=('config file ' +
                              '(parameters from config file can be ' +
                              'overwritten with CLI arguments)'))
    parser.add_argument('--nocolor',
                        action='store_true',
                        help="don't display colored logs")
    parser.add_argument('--verbose', '-v',
                        action='store_true',
                        help="show debug level logs")
    parser.add_argument('task', type=str)
    args, unknown = parser.parse_known_args([a for a in argv
                                             if a not in ['-h', '--help']])
    Context.add_cli_args(args.config, parser)
    args = parser.parse_args(argv)
    LoggerFactory(verbose=args.verbose,
                  colored=not args.nocolor)
    ibcontext = Context(args.config, args)
    task_func = get_task_func(args, args.task)
    task_func(ibcontext=ibcontext)


if __name__ == "__main__":
    sys.exit(main())
