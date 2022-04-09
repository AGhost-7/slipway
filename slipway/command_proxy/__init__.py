from subprocess import Popen, DEVNULL, PIPE, check_output
import os
from os import path
from pathlib import Path
import sys


class CommandProxy(object):
    def __init__(self, runtime_dir, logs_directory, commands=["xdg-open"]):
        self._socket_file = Path(runtime_dir) / "slipway" / "command-proxy.sock"
        self._pid_file = Path(runtime_dir) / "slipway" / "command-proxy.pid"
        self._log_file = Path(logs_directory) / "command-proxy-server.log"
        self._script_dir = Path(__file__).parent
        self._commands = commands

    @property
    def client_path(self) -> Path:
        return self._script_dir / "client.py"

    @property
    def server_url(self) -> str:
        if sys.platform == "linux":
            return "unix:///run/slipway/command-proxy.sock"
        else:
            return "tcp://host.docker.internal:7272"

    @property
    def bind_url(self) -> str:
        return (
            f"unix://{self._socket_file}"
            if sys.platform == "linux"
            else "tcp://127.0.0.1:7272"
        )

    @property
    def server_script(self) -> Path:
        return self._script_dir / "server.py"

    def _pid(self) -> int:
        with open(self._pid_file) as pid_file:
            pid = str(pid_file.read())
            return int(pid)

    def is_server_running(self):
        try:
            pid = self._pid()
            # per documentation, this will just check if the process is
            # running:
            # https://linux.die.net/man/2/kill
            os.kill(pid, 0)

            # If there is a system restart, the pids will reset to 0 and start
            # incrementing again. Handle that by checking the command name.
            process_command = str(
                check_output(["ps", "-p", str(pid), "-o", "args="]), "utf8"
            )
            return str(self.server_script) in process_command
        except OSError:
            return False

    def _remove_file(self, file):
        try:
            os.remove(file)
        except FileNotFoundError:
            pass

    def _start_background_process(self, child_process_kwargs):
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        self._log_file.touch(exist_ok=True)
        log_file = open(self._log_file)
        args = ["python3", self.server_script, self.bind_url] + self._commands
        print("starting with", args)

        process = Popen(
            args,
            stdin=DEVNULL,
            stdout=log_file,
            stderr=log_file,
            **(
                {
                    # Makes the subprocess its own parent, prevents the process
                    # from becoming defunct once it exits.
                    "preexec_fn": os.setsid,
                    **child_process_kwargs,
                }
            ),
        )
        with open(self._pid_file, "w+") as file:
            file.write(str(process.pid))

    def start_server(self, **kwargs):
        self._pid_file.parent.mkdir(parents=True, exist_ok=True)

        if self._pid_file.exists():
            print("pid exists")
            if not self.is_server_running():
                print("server not running")
                self._remove_file(self._pid_file)
                self._remove_file(self._socket_file)
                self._start_background_process(kwargs)
        else:
            # starting background process
            self._start_background_process(kwargs)

    def stop_server(self):
        if self.is_server_running():
            os.kill(self._pid(), 15)  # SIGTERM
        else:
            print("Server is not running")

    def logs(self) -> str:
        with open(self._log_file) as file:
            return file.read()
