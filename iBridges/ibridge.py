#!/usr/bin/env python
import sys
import argparse
from context import Context
import task
from logger import LoggerFactory


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
    task_func = getattr(task, args.task)
    task_func(ibcontext=ibcontext)


if __name__ == "__main__":
    sys.exit(main())
