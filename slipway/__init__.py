from os import environ, path
import sys
from argparse import ArgumentParser

import docker
from .container import Container
from .configuration import Configuration


def parse_args(configuration):
    parser = ArgumentParser()
    parser.add_argument(
        '--data-directory',
        default=configuration.data_directory)
    subparsers = parser.add_subparsers(dest='mode')
    subparsers.required = True

    start_parser = subparsers.add_parser('start')
    start_parser.add_argument('image')
    start_parser.add_argument('--mount-docker', action='store_true', default=configuration.mount_docker)
    start_parser.add_argument('--pull', action='store_true', default=configuration.pull)
    start_parser.add_argument('--pull-daily', action='store_true', default=configuration.pull_daily)
    start_parser.add_argument('--volume', '-v', action='append', default=configuration.volume)
    start_parser.add_argument('--environment', '-e', action='append', default=configuration.environment)
    start_parser.add_argument(
        '--workspace', default=configuration.workspace)

    purge_parser = subparsers.add_parser('purge')
    purge_parser.add_argument('image')

    args = parser.parse_args()

    if args.image in configuration.alias:
        args.image = configuration.alias[args.image]

    return args


def main():
    if sys.version_info.major < 3:
        print('Python 2 is not supported')
        sys.exit(1)
    configuration = Configuration(environ['HOME'])
    configuration.load()
    args = parse_args(configuration)
    client = docker.from_env()
    container = Container(client, args)
    if args.mode == 'start':
        container.image.initialize()
        container.volumes.initialize()
        container.binds.initialize()
        container.run()
    elif args.mode == 'purge':
        container.volumes.purge()
