from os import environ
import sys
from argparse import ArgumentParser

from .container import Container
from .configuration import Configuration
from .client import PodmanClient, DockerClient


def parse_args(configuration):
    parser = ArgumentParser()
    parser.add_argument("--data-directory", default=configuration.data_directory)
    parser.add_argument("--cache-directory", default=configuration.cache_directory)
    subparsers = parser.add_subparsers(dest="mode")
    subparsers.required = True

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("image")
    start_parser.add_argument(
        "--mount-docker", action="store_true", default=configuration.mount_docker
    )
    start_parser.add_argument("--pull", action="store_true", default=configuration.pull)
    start_parser.add_argument(
        "--pull-daily", action="store_true", default=configuration.pull_daily
    )
    start_parser.add_argument(
        "--volume", "-v", action="append", default=configuration.volume
    )
    start_parser.add_argument(
        "--environment", "-e", action="append", default=configuration.environment
    )
    start_parser.add_argument("--runtime", "-r", default=configuration.runtime)
    start_parser.add_argument("--workspace", default=configuration.workspace)
    start_parser.add_argument("--network", default=configuration.network)
    start_parser.add_argument("--runtime-dir", default=configuration.runtime_dir)

    purge_parser = subparsers.add_parser("purge")
    purge_parser.add_argument("image")

    args = parser.parse_args()

    if args.image in configuration.alias:
        alias = configuration.alias[args.image]
        if "image" in alias:
            args.image = alias["image"]
        else:
            args.image = alias

        if "environment" in alias:
            args.environment = alias["environment"]

        if "volume" in alias:
            args.volume.extend(alias["volume"])

        if "network" in alias:
            args.network = alias["network"]

    assert args.runtime == "podman", "Only podman is currently supported"
    return args


def main():
    if sys.version_info.major < 3:
        print("Python 2 is not supported")
        sys.exit(1)
    configuration = Configuration(environ)
    configuration.load()
    args = parse_args(configuration)
    client = None
    if args.runtime == "podman":
        client = PodmanClient()
    else:
        client = DockerClient()
    assert client.is_rootless(), "Only rootless mode is supported"
    container = Container(client, args)
    if args.mode == "start":
        container.image.initialize()
        container.volumes.initialize()
        container.binds.initialize()
        container.xdg_open.start_server()
        if container.exists():
            print("Container {} already exists".format(container.name))
            sys.exit(1)
        container.run()
    elif args.mode == "purge":
        container.volumes.purge()
