import yaml
import os
from os import path


class Configuration(object):
    def __init__(self, environ):
        home_path = environ["HOME"]
        # per xdg spec:
        # https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
        config_home = environ.get("XDG_CONFIG_HOME", path.join(home_path, ".config"))
        data_home = environ.get("XDG_DATA_HOME", path.join(home_path, ".local/share"))
        cache_home = environ.get("XDG_CACHE_HOME", path.join(home_path, ".cache"))
        self.cache_directory = path.join(cache_home, "slipway")
        self.config_path = path.join(config_home, "slipway.yaml")
        self.data_directory = path.join(data_home, "slipway")
        self.runtime_dir = environ.get(
            "XDG_RUNTIME_DIR", path.join("/run/user", str(os.getuid()))
        )
        self.workspace = path.join(home_path, "workspace")
        self.alias = {}
        self.environment = []
        self.volume = []
        self.pull = False
        self.pull_daily = False
        self.mount_docker = False
        self.runtime = "podman"
        self.network = "host"
        self.device = []

    def load(self):
        if path.exists(self.config_path):
            with open(self.config_path) as file_descriptor:
                config = yaml.safe_load(file_descriptor)

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
