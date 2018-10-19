#!/usr/bin/env python
import sys
import os
import argparse
import json
import importlib
import getpass
import pprint
import logging
import traceback

# iRODS
from irods.session import iRODSSession

# iBridges
from iBridges.logger import LoggerFactory
from iBridges.logger import format_error
from iBridges.logger import format_question
from iBridges import CollectionLock
from iBridges import iRodsCollection
from iBridges import iRodsRepositoryConnector


def parse_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--config', '-c',
                        type=str,
                        help=('config file ' +
                              '(parameters from config file can be ' +
                              'overwritten with CLI arguments)'))
    parser.add_argument('--type', '-t',
                        type=str,
                        help='Draft type (e.g. DataverseDraft)')
    parser.add_argument('--verbose', '-v',
                        action='store_true',
                        help="show debug level logs")
    parser.add_argument('--nocolor',
                        action='store_true',
                        help="don't display colored logs")
    parser.add_argument('--nocleanup',
                        action='store_true',
                        help="don't remove temporary files")
    parser.add_argument('--batch', '-b',
                        action='store_true',
                        help=("batch mode: " +
                              "don't ask any interactive questions"))
    parser.add_argument('--nopublish',
                        action='store_true',
                        help="dont publish draft, save ticket instead")
    parser.add_argument('--ticket',
                        type=str,
                        help=('save draft information to ticket ' +
                              'for later continuation or reference'))
    parser.add_argument('--continue',
                        action='store_true',
                        dest='continue_publish',
                        help=('continue with publication of ' +
                              'prepared draft ' +
                              '(filename given by --ticket argument ' +
                              'in previous phase)'))
    parser.add_argument('--force',
                        action='store_true',
                        help=("force publishing " +
                              "(even on upload / metadata errors)\n" +
                              "if not in batch mode, " +
                              "user is asked interactively "))
    parser.add_argument('collection', type=str, nargs='?')
    args, unknown = parser.parse_known_args([a for a in argv
                                             if a not in ['-h', '--help']])
    irods_group = parser.add_argument_group('irods configuration')
    iRodsCollection.add_arguments(irods_group)

    try:
        config = read_config(args)
        draft_name = config.get('type')
        if draft_name is None:
            print(format_error('missing argument --type or ' +
                               'type entry in configuration file'))
            parser.print_help()
            sys.exit(8)
        draft_name = str(draft_name)
        draft_class = get_draft_class(draft_name)
        draft_group = parser.add_argument_group(draft_name +
                                                ' configuration')
        draft_class.add_arguments(draft_group)
        if args.collection is None and 'collection' not in config:
            raise ValueError('Missing CLI argument collection')
        return parser.parse_args(argv)
    except Exception:
        parser.print_help()
        raise


def read_config(args):
    config = {}
    if args.config is not None:
        with open(os.path.abspath(args.config)) as f:
            config = json.load(f)
    if args.type is not None:
        config['type'] = args.type
    return config


def module_name_of_draft(s):
    if len(s) == 0:
        return s
    else:
        return s[0].lower() + s[1:]


def get_draft_class(draft):
    draft_module = module_name_of_draft(draft)
    mod = importlib.import_module(draft_module)
    return getattr(mod, draft)


def overlay_config(config, args, draft_class):
    irods_prefix = iRodsCollection.argument_prefix + "_"
    draft_prefix = draft_class.argument_prefix + "_"
    for k, v in vars(args).items():
        if k.startswith(irods_prefix) and v is not None:
            config['irods'][k[len(irods_prefix):]] = v
        if k.startswith(draft_prefix) and v is not None:
            config['draft'][k[len(draft_prefix):]] = v
    return config


def get_irods_session(config, args):
    logger = logging.getLogger('ipublish')
    env_file = config.get('env_file', None)
    if env_file:
        logger.info('iRODSSession from env_file %s', env_file)
        return iRODSSession(irods_env_file=env_file)
    else:
        host = config.get('host', 'ibridges')
        user = config.get('user', 'data')
        zone = config.get('zone', 'myZone')
        port = config.get('port', 1247)
        password = config.get('password', None)
        if password is None:
            if args.batch:
                raise RuntimeError("Missing password for iRods session")
            password = getpass.getpass('Password for iRods user %s:' % user)
        logger.info('iRODSSession from parameters:')
        logger.info('host=%s, user=%s zone=%s password=***', host, user, zone)
        return iRODSSession(host=host, port=port, user=user,
                            password=password, zone=zone)


def execute_steps(cmds, batch=False, force=False):
    logger = logging.getLogger('ipublish')
    i = 1
    err = False
    for cmd in cmds:
        logger.info('execute step %d/%d %s', i, len(cmds),
                    str(cmd.__name__))
        try:
            cmd()
        except Exception as e:
            msg = str(e)
            if not msg:
                msg = e.__class__.__name__
            logger.error(msg)
            for line in traceback.format_exc().split('\n'):
                logger.error(line)
            if batch and not force:
                logger.error('raise')
                raise
            err = True
        i += 1
    if err:
        logger.error('Metadata/data upload failed')
        if force:
            logger.warning('continue with errors (due to --force flag)')
        elif batch:
            raise RuntimeError('Should have been raised earlier (--batch)')
        else:
            raw_input(format_error("Press Enter to continue..."))
            logger.warning('continue with errors')


def write_ticket(ticket, connector, lock):
    logger = logging.getLogger('ipublish')
    logger.info('writing data to ticket %s ' % ticket)
    obj = {"irods": connector.config.get('irods', {}),
           "type": connector.draftClass,
           "collection": connector.collection,
           "draft": connector.config.get('draft', {}),
           "collection_lock": lock.to_dict()}
    with open(ticket, "w") as fp:
        fp.write(json.dumps(obj, indent=4))


def continue_publish_draft(connector, logger_factory,
                           batch=True, force=False):
    logger = logging.getLogger('ipublish')
    config = connector.config
    do_lock = 'collection_lock' not in config
    try:
        with CollectionLock(connector.ipc,
                            do_lock=do_lock,
                            **config.get('collection_lock', {})) as lock:
            if connector.isPublished():
                logger.error('Data already published {%s=%s}',
                             connector.getRepoKey('URL'),
                             connector.getRepoValue('URL', default='?'))
                raise ValueError('Publication error')
            if not batch and not force:
                try:
                    raw_input(format_question('Press Enter to publish...'))
                    connector.publishDraft()
                    lock.finalize()
                except KeyboardInterrupt:
                    logger.error('KeyboardInterrupt')
                    # suppress unlock
                    lock.finalize()
            else:
                connector.publishDraft()
                connector.createReportNoRaise(logger_factory.get_logs())
                lock.finalize()
    except Exception:
        connector.createReportNoRaise(logger_factory.get_logs())
        raise


def publish_draft(connector, logger_factory,
                  batch=True, force=False, ticket=None):
    logger = logging.getLogger('ipublish')
    try:
        with CollectionLock(connector.ipc) as lock:
            connector.assignSeriesInformation()
            if connector.isPublished():
                logger.error('Data already published {%s=%s}',
                             connector.getRepoKey('URL'),
                             connector.getRepoValue('URL', default='?'))
                raise ValueError('Publication error')
            if not connector.checkCollection():
                raise ValueError('Metadata validation error')
            connector.assignTicket()
            connector.createDraft()
            execute_steps([connector.patchDraft,
                           connector.patchDraftTickets,
                           connector.patchDraftPIDs,
                           connector.uploadToRepo],
                          batch=batch,
                          force=force)
            if ticket is not None:
                write_ticket(ticket, connector, lock)
            if not batch and not force:
                raw_input(format_question('Press Enter to publish...'))
            connector.publishDraft()
            connector.createReportNoRaise(logger_factory.get_logs())
            lock.finalize()
    except Exception:
        connector.createReportNoRaise(logger_factory.get_logs())
        raise


def main(argv=sys.argv[1:]):
    args = parse_arguments(argv)

    logger_factory = LoggerFactory(verbose=args.verbose,
                                   colored=not args.nocolor)
    logger = logger_factory.get_logger()
    try:
        config = read_config(args)
        draft_name = str(config.get('type'))
        draft_class = get_draft_class(draft_name)
        # add cli arguments to config
        config = overlay_config(config, args, draft_class)
        if args.collection is None:
            collection = config.get('collection', None)
            if collection is None:
                raise ValueError('Missing CLI argument collection')
        else:
            collection = args.collection
        logger.debug('config:')
        for line in pprint.pformat(config, 2).split('\n'):
            logger.debug(' ' + line)

        # instanciate classes
        # 1. draft
        draft = draft_class(**config.get('draft', {}))

        # 2. iRodsCollection
        irodscfg = config.get('irods', {})
        irods_session = get_irods_session(irodscfg, args)
        http_endpoint = irodscfg.get('http_endpoint', '')
        ipc = iRodsCollection(collection,
                              session=irods_session,
                              http_endpoint=http_endpoint)

        # 3. connector
        connector = iRodsRepositoryConnector(ipc, draft, config=config)

        # perform publication
        if args.continue_publish:
            continue_publish_draft(connector, logger_factory,
                                   batch=args.batch,
                                   force=args.force)
        else:
            publish_draft(connector, logger_factory,
                          ticket=args.ticket,
                          batch=args.batch,
                          force=args.force)
        logger.info('done')

    except Exception as e:
        msg = str(e)
        if not msg:
            msg = e.__class__.__name__
        logger.critical(msg)
        raise


if __name__ == "__main__":
    sys.exit(main())
