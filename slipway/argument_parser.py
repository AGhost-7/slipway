from typing import List
from .configuration import Configuration
from argparse import ArgumentParser


def create_parser(configuration: Configuration) -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--data-directory", default=configuration.data_directory)
    parser.add_argument("--cache-directory", default=configuration.cache_directory)
    parser.add_argument("--log-directory", default=configuration.log_directory)
    subparsers = parser.add_subparsers(dest="mode")
    subparsers.required = True

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("image")
    start_parser.add_argument(
        "--mount-docker", action="store_true", default=configuration.mount_docker
    )
    start_parser.add_argument("--device", action="append", default=configuration.device)
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
    start_parser.add_argument(
        "--proxy-command",
        dest="proxy_commands",
        action="append",
        default=configuration.proxy_commands,
    )
    start_parser.add_argument("--runtime", "-r", default=configuration.runtime)
    start_parser.add_argument("--workspace", default=configuration.workspace)
    start_parser.add_argument("--network", default=configuration.network)
    start_parser.add_argument("--runtime-dir", default=configuration.runtime_dir)
    start_parser.add_argument("--shm-size", default=configuration.shm_size)

    purge_parser = subparsers.add_parser("purge")
    purge_parser.add_argument("image")

    command_proxy = subparsers.add_parser("command-proxy")
    command_proxy.add_argument("--runtime-dir", default=configuration.runtime_dir)
    command_proxy_subparser = command_proxy.add_subparsers(dest="command")
    proxy_start = command_proxy_subparser.add_parser("start")
    proxy_start.add_argument(
        "commands", nargs="*", default=configuration.proxy_commands
    )
    proxy_stop = command_proxy_subparser.add_parser("stop")
    proxy_logs = command_proxy_subparser.add_parser("logs")
    return parser


def parse_args(configuration: Configuration, raw_args: List[str] = None):
    parser = create_parser(configuration)
    args = parser.parse_args(raw_args)

    if args.mode != "command-proxy" and args.image in configuration.alias:
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

        if "device" in alias:
            args.device.extend(alias["device"])
    return args
