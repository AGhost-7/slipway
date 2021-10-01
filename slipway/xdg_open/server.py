from socketserver import UnixStreamServer, StreamRequestHandler
from subprocess import run, PIPE
import json
import sys
import os
import stat
from pathlib import Path


socket_file = sys.argv[1]
log_file = open(sys.argv[2], "w+")

sys.stdout = log_file
sys.stderr = sys.stdout

class XdgOpenHandler(StreamRequestHandler):
    def handle(self):
        request = json.loads(self.rfile.readline().strip())
        cwd = Path(request["cwd"])
        if not cwd.exists():
            print(f"The path {cwd} does not exist on the host, ignoring", file=sys.stdout)
            cwd = None
        try:
            print(f"Running xdg-open with arguments {request['args']}")
            result = run(
                ["xdg-open"] + request["args"],
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
                    "stderr": "xdg-open not found on host machine",
                }
            )
            self.request.sendall(bytes(response + "\n", "utf8"))


with UnixStreamServer(socket_file, XdgOpenHandler) as server:
    os.chmod(socket_file, stat.S_IRUSR | stat.S_IWUSR)
    try:
        print('Starting server on socket', socket_file, file=sys.stdout)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
