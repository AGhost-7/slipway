"""
This script accepts a bind url, and commands which are allowed to execute on
the host system.
"""

from asyncio import StreamReader, StreamWriter
import asyncio
from asyncio.subprocess import Process
import json
import sys
import os
import stat
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Any
from urllib.parse import urlparse
from slipway.command_proxy.protocol import MessageType, encode, decode


url = urlparse(sys.argv[1])
allowed_commands = sys.argv[2:]


def log(*args: Any, **kwargs: Any) -> None:
    print(*args, **kwargs, file=sys.stdout)


def request_cwd(request: Dict[str, Any]) -> Optional[str]:
    """
    Checks if the cwd provided by the client is valid. Ignores invalid ones.
    """
    cwd = request["cwd"]
    if cwd is not None and not Path(cwd).exists():
        log(f"The path {cwd} does not exist on the host, ignoring")
        cwd = None
    return cwd


def translate_darwin_call(command: str, args: List[str]) -> Tuple[str, List[str]]:
    """
    Handles converting linux-only commands to darwin compatible ones.
    """

    if command == "xdg-open":
        return ("open", args)
    elif command == "xclip" or command == "xclip-nvim":
        if "-o" not in args and "-out" not in args:
            return ("pbcopy", [])
        else:
            return ("pbpaste", [])
    return (command, args)


async def poll_client(reader: StreamReader, process: Process, stdin: StreamWriter):
    """
    Continuously waits to receive a stdin message from the client.
    """
    while True:
        (message_type, body) = await decode(reader)
        if message_type == MessageType.STDIN:
            if len(body) == 0:
                stdin.write_eof()
            else:
                stdin.write(body)
        elif message_type == MessageType.SIGNAL:
            signal = int.from_bytes(body, "big", signed=False)
            log("Got signal", signal)
            process.send_signal(signal)


async def poll_pipe(
    writer: StreamWriter, message_type: MessageType, pipe: StreamReader
):
    """
    Continuously waits for stdout/stderr chunks which are then sent back to the
    client.
    """
    while True:
        body = await pipe.read(1024)
        if len(body) == 0:
            break
        writer.write(encode(message_type, body))


async def client_connected(reader: StreamReader, writer: StreamWriter):
    """
    Handles a new client connection.
    """
    (message_type, body) = await decode(reader)
    if message_type == MessageType.INIT:
        request = json.loads(body)
        command = request["command"]

        cwd = request_cwd(request)
        args = request["args"]
        if command not in allowed_commands and command != "xclip-nvim":
            writer.write(
                encode(
                    MessageType.STDERR,
                    bytes(
                        f"Command {command} is not permitted to run on the host\n",
                        "utf8",
                    ),
                )
            )
            writer.write(
                encode(MessageType.EXIT, (1).to_bytes(1, byteorder="big", signed=False))
            )
        else:
            if sys.platform == "darwin":
                (command, args) = translate_darwin_call(command, args)
            process = await asyncio.create_subprocess_exec(
                command,
                *args,
                cwd=cwd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            assert (
                process.stdin is not None
                and process.stdout is not None
                and process.stderr is not None
            )

            client_task = asyncio.create_task(
                poll_client(reader, process, process.stdin)
            )
            stdout_task = asyncio.create_task(
                poll_pipe(writer, MessageType.STDOUT, process.stdout)
            )
            stderr_task = asyncio.create_task(
                poll_pipe(writer, MessageType.STDERR, process.stderr)
            )

            await process.wait()
            assert process.returncode is not None
            client_task.cancel()
            await stdout_task
            await stderr_task

            writer.write(
                encode(
                    MessageType.EXIT,
                    process.returncode.to_bytes(1, byteorder="big", signed=False),
                )
            )


async def main():
    assert url.scheme in ("unix", "tcp"), f"Invalid scheme {url.scheme}"
    if url.scheme == "unix":
        socket_file = Path(url.path)
        if socket_file.exists():
            socket_file.unlink()
        server = await asyncio.start_unix_server(client_connected, socket_file)
    else:
        [host, port] = url.netloc.split(":")
        server = await asyncio.start_server(client_connected, host, port)
    print("Listening on addresss", sys.argv[1])
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
