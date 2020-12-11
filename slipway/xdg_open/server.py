from socketserver import UnixStreamServer, StreamRequestHandler
from subprocess import run, PIPE
import json
import sys
import os

socket_file = sys.argv[1]


class XdgOpenHandler(StreamRequestHandler):
    def handle(self):
        url = self.rfile.readline().strip()
        try:
            result = run(
                ['xdg-open', url],
                shell=False,
                check=False,
                stdout=PIPE,
                stderr=PIPE)
            response = json.dumps({
                'returncode': result.returncode,
                'stdout': str(result.stdout, 'utf8'),
                'stderr': str(result.stderr, 'utf8')
            })

            self.request.sendall(bytes(response + '\n', 'utf8'))
        except PermissionError:
            response = json.dumps({
                'returncode': 127,
                'stdout': '',
                'stderr': 'xdg-open not found on host machine'
            })
            self.request.sendall(bytes(response + '\n', 'utf8'))


with UnixStreamServer(socket_file, XdgOpenHandler) as server:
    server.serve_forever()
