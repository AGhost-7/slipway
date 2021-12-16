from socketserver import UnixStreamServer, TCPServer, StreamRequestHandler, BaseServer
from subprocess import run, PIPE
import json
import sys
import os
import stat
from pathlib import Path
from urllib.parse import urlparse


url = urlparse(sys.argv[1])
allowed_commands = sys.argv[2:]


class CommandProxyHandler(StreamRequestHandler):
    def _request_cwd(self, request):
        cwd = request["cwd"]
        if cwd is not None and not Path(cwd).exists():
            print(
                f"The path {cwd} does not exist on the host, ignoring", file=sys.stdout
            )
            cwd = None
        return cwd

    def _run_command(self, command, args, cwd):
        try:
            print(f"Running {command} with arguments {args}")
            result = run(
                [command] + args,
                shell=False,
                check=False,
                stdout=PIPE,
                stderr=PIPE,
                cwd=cwd,
            )
            response = json.dumps(
                {
                    "returncode": result.returncode,
                    "stdout": str(result.stdout, "utf8"),
                    "stderr": str(result.stderr, "utf8"),
                }
            )

            self.request.sendall(bytes(response + "\n", "utf8"))
        except PermissionError:
            response = json.dumps(
                {
                    "returncode": 127,
                    "stdout": "",
                    "stderr": f"{command} not found on host machine\n",
                }
            )
            self.request.sendall(bytes(response + "\n", "utf8"))

    def handle(self):
        request = json.loads(self.rfile.readline().strip())
        command = request["command"]
        if command not in allowed_commands:
            response = json.dumps(
                {
                    "returncode": 1,
                    "stdout": "",
                    "stderr": f"Command {command} is not permitted to run on the host\n",
                }
            )
            self.request.sendall(bytes(response + "\n", "utf-8"))
        else:
            cwd = self._request_cwd(request)
            self._run_command(command, request["args"], cwd)


def serve(server: BaseServer):
    try:
        print("Starting server on socket", socket_file, file=sys.stdout)
        server.serve_forever()
    except KeyboardInterrupt:
        pass


assert url.scheme in ("unix", "tcp"), f"Invalid scheme {url.scheme}"

if url.scheme == "unix":
    socket_file = Path(url.path)

    if socket_file.exists():
        socket_file.unlink()

    with UnixStreamServer(str(socket_file), CommandProxyHandler) as server:
        os.chmod(socket_file, stat.S_IRUSR | stat.S_IWUSR)
        serve(server)
else:
    [host, port] = url.netloc.split(":")
    with TCPServer((host, int(port)), CommandProxyHandler) as tcp_server:
        serve(tcp_server)
