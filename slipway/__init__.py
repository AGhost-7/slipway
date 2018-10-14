import sys
from argparse import ArgumentParser

import docker
from .container import Container


def parse_args():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='mode')
    subparsers.required = True

    start_parser = subparsers.add_parser('start')
    start_parser.add_argument('image')
    start_parser.add_argument('--volume', action='append')
    start_parser.add_argument('--environment', action='append')

    purge_parser = subparsers.add_parser('purge')
    purge_parser.add_argument('image')

    return parser.parse_args()


def main():
    if sys.version_info.major < 3:
        print('Python 2 is not supported')
        sys.exit(1)
    args = parse_args()
    client = docker.from_env()
    container = Container(client, args)
    if args.mode == 'start':
        container.image.initialize()
        container.volumes.initialize()
        container.binds.initialize()
        container.run()
    elif args.mode == 'purge':
        container.volumes.purge()
