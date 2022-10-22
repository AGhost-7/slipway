#!/usr/bin/env python3

import signal
from pathlib import Path
from typing import Optional
import json
import sys
from os import path, environ
import os
import json
from urllib.parse import urlparse
import socket
import asyncio
from asyncio import StreamWriter, StreamReader
import stat

try:
    from .stream import create_standard_streams
    from .protocol import MessageType, encode, decode, ConnectionClosedException
except (ModuleNotFoundError, ImportError):
    sys.path.append("/usr/local/lib/slipway/slipway")
    from command_proxy.stream import create_standard_streams  # type: ignore
    from command_proxy.protocol import MessageType, encode, decode, ConnectionClosedException  # type: ignore


output = open("/tmp/proxy-command.log", "w+")


def debug(*args):
    print(*args, file=output)


def host_cwd() -> Optional[str]:
    cwd = os.getcwd()
    mapping_path = Path("/run/user") / str(os.getuid()) / "slipway-mapping.json"
    debug("host_cwd::mapping_path", mapping_path)
    if not mapping_path.exists():
        return None
    with mapping_path.open() as file:
        mappings = json.loads(file.read())
    for mapping in mappings:
        if cwd.startswith(mapping["container"]):
            return cwd.replace(mapping["container"], mapping["host"])
    return None


async def poll_stdin(server_writer: StreamWriter, reader: StreamReader):
    """
    Forward stdin to server.
    """
    eof = False
    while not eof:
        chunk = await reader.read(1024)
        if len(chunk) == 0:
            eof = True
        server_writer.write(encode(MessageType.STDIN, chunk))


async def poll_replies(
    server_reader: StreamReader, stdout: StreamWriter, stderr: StreamWriter
) -> int:
    """
    Checks for messages from the server and send to appropriate pipe or exit.
    """
    while True:
        try:
            (message_type, body) = await decode(server_reader)
        except ConnectionClosedException:
            debug("connection closed")
            print("Connection to proxy server closed", file=sys.stderr)
            return 1

        if message_type == MessageType.STDOUT:
            debug("got stdout message", body)
            stdout.write(body)
        elif message_type == MessageType.STDERR:
            debug("got stderr message", body)
            stderr.write(body)
        elif message_type == MessageType.EXIT:
            debug("got exit message", body)
            return int.from_bytes(body, "big", signed=False)


async def main():
    args = sys.argv[1:]
    proxy_url = urlparse(environ["SLIPWAY_COMMAND_PROXY_URL"])
    debug("sending", proxy_url)
    if proxy_url.scheme == "unix":
        reader, writer = await asyncio.open_unix_connection(proxy_url.path)
    else:
        [host, port] = proxy_url.netloc.split(":")
        reader, writer = await asyncio.open_connection(host, int(port))

    command = path.basename(sys.argv[0])
    payload = json.dumps(
        {
            "args": args,
            "command": command,
            "cwd": host_cwd(),
            "tty": os.isatty(sys.stdout.fileno()),
        }
    )
    writer.write(encode(MessageType.INIT, bytes(payload, "utf8")))

    def handler(signal_number: int, frame):
        writer.write(
            encode(
                MessageType.SIGNAL,
                signal_number.to_bytes(4, byteorder="big", signed=False),
            )
        )

    signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGINT, handler)
    debug("sys.stdin", sys.stdin, "sys.stdout", sys.stdout, "sys.stderr", sys.stderr)
    stdin, stdout, stderr = await create_standard_streams(
        sys.stdin, sys.stdout, sys.stderr
    )
    stdin_task = asyncio.create_task(poll_stdin(writer, stdin))
    exit_code = await poll_replies(reader, stdout, stderr)
    stdin_task.cancel()
    writer.close()
    output.flush()
    # debug('returning')
    return exit_code


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    exit_code = loop.run_until_complete(main())
    debug("completed without issue")
    output.flush()
    output.close()
    loop.stop()
    loop.close()
    sys.exit(exit_code)
