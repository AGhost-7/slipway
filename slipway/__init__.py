from os import environ, path
import sys
from argparse import ArgumentParser

import docker
from .container import Container
from .ssh_server import SshServer, host_key
import socket
from socket import AddressFamily
from uuid import uuid4
import paramiko


def parse_args():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='mode')
    subparsers.required = True

    start_parser = subparsers.add_parser('start')
    start_parser.add_argument('image')
    start_parser.add_argument('--volume', action='append')
    start_parser.add_argument('--environment', action='append')
    start_parser.add_argument(
        '--workspace', default=path.join(environ['HOME'], 'workspace'))

    purge_parser = subparsers.add_parser('purge')
    purge_parser.add_argument('image')

    share_parser = subparsers.add_parser('share')
    share_parser.add_argument('image')
    share_parser.add_argument('--bind', default='127.0.0.1')
    share_parser.add_argument('--port', type=int, default=2500)

    return parser.parse_args()


def share(args, container):
    user_name = uuid4()
    sock = socket.socket(AddressFamily.AF_INET, socket.SOCK_STREAM)
    sock.bind((args.bind, args.port))
    sock.listen(1)
    print('Command: ssh -p {} {}@localhost'.format(args.port, user_name))
    client, addr = sock.accept()
    transport = paramiko.Transport(client, gss_kex=False)
    transport.add_server_key(host_key)
    server = SshServer(user_name)
    transport.start_server(server)

    print('Getting channel')
    channel = transport.accept(20)

    if channel is None:
        raise Exception('lolwut')

    print('got channel')
    server.event.wait(10)
    if not server.event.is_set():
        raise Exception('Client never asked for shell')

    channel.send('\nWelcome!\n')
    channel.send('\nAnd goodbye\n')
    channel.close()


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
    elif args.mode == 'share':
        share(args, container)
