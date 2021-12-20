from os import environ
import sys
from argparse import ArgumentParser

from .command_proxy import CommandProxy
from .container import Container
from .configuration import Configuration
from .client import PodmanClient, DockerClient
from .argument_parser import parse_args


def main():
    if sys.version_info.major < 3:
        print("Python 2 is not supported")
        sys.exit(1)
    configuration = Configuration(environ)
    configuration.load()
    args = parse_args(configuration)

    if args.mode == "command-proxy":
        command_proxy = CommandProxy(args.runtime_dir, args.log_directory)
        if args.command == "start":
            command_proxy.start_server()
        elif args.command == "stop":
            command_proxy.stop_server()
        elif args.command == "logs":
            print(command_proxy.logs())
    else:
        client = None

        if args.runtime == "podman":
            client = PodmanClient()
        else:
            client = DockerClient()

        if sys.platform == "linux":
            assert client.is_rootless(), "Only rootless mode is supported on linux"
            assert (
                args.runtime == "podman"
            ), "Only podman is currently supported on linux"

        container = Container(client, args)

        if args.mode == "start":
            container.image.initialize()
            container.volumes.initialize()
            container.binds.initialize()
            #container.command_proxy.start_server()
            if container.exists():
                print("Container {} already exists".format(container.name))
                sys.exit(1)
            container.run()
        elif args.mode == "purge":
            container.volumes.purge()
