from subprocess import Popen, DEVNULL
import os
from os import path


class XdgOpen(object):
    def __init__(self, slipway_dir):
        self._script_dir = path.dirname(path.realpath(__file__))
        self._slipway_dir = slipway_dir
        self._socket_file = path.join(slipway_dir, "xdg-open.sock")
        self._pid_file = path.join(slipway_dir, "xdg-open.pid")

    @property
    def runtime_dir(self):
        return self._slipway_dir

    @property
    def client_path(self):
        return path.join(self._script_dir, "client.py")

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
        script_dir = path.dirname(path.realpath(__file__))
        server_script = path.join(script_dir, "server.py")
        process = Popen(
            ["python3", server_script, self._socket_file],
            stdin=DEVNULL,
            stdout=DEVNULL,
            stderr=DEVNULL,
            **child_process_args
        )
        with open(self._pid_file, "w+") as file:
            file.write(str(process.pid))

    def start_server(self, **kwargs):
        if not path.exists(self._slipway_dir):
            os.makedirs(self._slipway_dir)

        if path.exists(self._pid_file):
            if not self.is_server_running():
                self._remove_file(self._pid_file)
                self._remove_file(self._socket_file)
                self._start_background_process(kwargs)
        else:
            self._start_background_process(kwargs)

    def stop_server(self):
        if self.is_server_running():
            self._kill(15)  # SIGTERM
