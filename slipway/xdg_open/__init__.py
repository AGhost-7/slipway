from subprocess import Popen, DEVNULL, PIPE
import os
from os import path
from pathlib import Path


class XdgOpen(object):
    def __init__(self, runtime_dir, logs_directory):
        self._socket_file = Path(runtime_dir) / "slipway" / "xdg-open.sock"
        self._pid_file = Path(runtime_dir) / "slipway" / "xdg-open.pid"
        self._log_file = Path(logs_directory) / "xdg-server.log"
        self._script_dir = Path(__file__).parent

    @property
    def client_path(self):
        return self._script_dir / "client.py"

    def _kill(self, code):
        with open(self._pid_file) as file:
            pid = str(file.read())
            os.kill(int(pid), code)

    def is_server_running(self):
        try:
            # per documentation, this will just check if the process is
            # running:
            # https://linux.die.net/man/2/kill
            self._kill(0)
            return True
        except OSError:
            return False

    def _remove_file(self, file):
        try:
            os.remove(file)
        except FileNotFoundError:
            pass

    def _start_background_process(self, child_process_args):
        server_script = self._script_dir / "server.py"
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        process = Popen(
            ["python3", server_script, self._socket_file, self._log_file],
            stdin=DEVNULL,
            stdout=DEVNULL,
            stderr=DEVNULL,
            **child_process_args
        )
        with open(self._pid_file, "w+") as file:
            file.write(str(process.pid))

    def start_server(self, **kwargs):
        self._pid_file.parent.mkdir(parents=True, exist_ok=True)

        if self._pid_file.exists():
            if not self.is_server_running():
                self._remove_file(self._pid_file)
                self._remove_file(self._socket_file)
                self._start_background_process(kwargs)
        else:
            self._start_background_process(kwargs)

    def stop_server(self):
        if self.is_server_running():
            self._kill(15)  # SIGTERM
        else:
            print("Server is not running")

    def logs(self) -> str:
        with open(self._log_file) as file:
            return file.read()
