from typing import List
from shutil import which
import yaml
import os
from pathlib import Path
import sys


class Configuration(object):
    def __init__(self, environ):
        home_path = Path(environ["HOME"])
        # per xdg spec:
        # https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
        config_home = Path(environ.get("XDG_CONFIG_HOME", str(home_path / ".config")))
        data_home = Path(
            environ.get("XDG_DATA_HOME", str(home_path / ".local/share"))
            if sys.platform == "linux"
            else home_path / "Library" / "Application Support"
        )
        cache_home = Path(
            environ.get("XDG_CACHE_HOME", str(home_path / ".cache"))
            if sys.platform == "linux"
            else str(home_path / "Library" / "Caches")
        )
        self.cache_directory = str(cache_home / "slipway")
        self.config_path = config_home / "slipway.yaml"
        self.data_directory = str(data_home / "slipway")
        self.runtime_dir = (
            environ.get("XDG_RUNTIME_DIR", str(Path("/run/user") / str(os.getuid())))
            if sys.platform == "linux"
            else str(data_home)
        )
        self.workspace = str(home_path / "workspace")
        self.alias = {}
        self.environment = []
        self.volume = []
        self.pull = False
        self.pull_daily = False
        self.mount_docker = False
        self.runtime = "podman" if sys.platform == "linux" else "docker"
        self.network = "host" if sys.platform == "linux" else "bridge"
        self.device = []
        self.shm_size = None
        self.port = []
        self.unshare_workspace = False
        self._proxy_commands = None

    @property
    def proxy_commands(self) -> List[str]:
        if self._proxy_commands is not None:
            return self._proxy_commands
        commands = [
            command
            for command in ["docker", "podman", "docker-compose"]
            if which(command) is not None
        ]
        commands.append("xdg-open")
        if sys.platform == "darwin":
            commands.append("xclip")
        return commands

    @property
    def log_directory(self) -> str:
        return str(Path(self.data_directory) / "logs")

    def load(self):
        if self.config_path.exists():
            with open(self.config_path) as file_descriptor:
                config = yaml.safe_load(file_descriptor)
                if "proxy_commands" in config:
                    self._proxy_commands = config["proxy_commands"]
                if "alias" in config:
                    self.alias = config["alias"]
                if "workspace" in config:
                    self.workspace = config["workspace"]
                if "environment" in config:
                    self.environment = config["environment"]
                if "volume" in config:
                    self.volume = config["volume"]
                if "device" in config:
                    self.device = config["device"]
                if "pull" in config:
                    self.pull = config["pull"]
                if "pull_daily" in config:
                    self.pull_daily = config["pull_daily"]
                if "mount_docker" in config:
                    self.mount_docker = config["mount_docker"]
                if "runtime" in config:
                    self.runtime = config["runtime"]
                if "shm_size" in config:
                    self.shm_size = config["shm_size"]
                if "unshare_workspace" in config:
                    self.unshare_workspace = config["unshare_workspace"]
                if "port" in config:
                    self.port = config["port"]
