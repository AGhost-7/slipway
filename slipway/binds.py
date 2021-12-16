import pwd
import os
from sys import platform
from os import environ, path


class Bind(object):
    def __init__(self, host_path, container_path, type="d"):
        self.host_path = host_path
        self.container_path = container_path
        self.type = type


class Binds(object):
    """
    A bind is a type of volume which maps a directory or file from the host
    into the container.
    """

    def __init__(self, client, args, image):
        self.client = client
        self.args = args
        self.image = image

    def initialize(self):
        """
        Creates the directory with appropriate permissions if it doesn't
        exist. Otherwise if we let docker do this the permissions will be
        set as root, which we don't want.
        """
        for bind in self.list():
            if not path.exists(bind.host_path):
                if "d" in bind.type:
                    os.makedirs(bind.host_path)
                elif "f" in bind.type:
                    dirname = path.dirname(bind.host_path)
                    if not path.exists(dirname):
                        os.makedirs(path.dirname(bind.host_path))
                    open(bind.host_path, "w+").close()

    def _gpg_binds(self):
        uid = pwd.getpwnam(environ["USER"]).pw_uid
        gnupg_socket_path = path.join("/run/user", str(uid), "gnupg")
        if path.exists(gnupg_socket_path):
            yield Bind(gnupg_socket_path, f"/run/user/{self.image.user_id}/gnupg", "d")

        gnupg_path = path.join(environ["HOME"], ".gnupg")
        if path.exists(gnupg_path):
            container_path = path.join(self.image.home, ".gnupg")
            yield Bind(gnupg_path, container_path, "d")

    def list(self):
        """
        List all bind mounts, including the default ones.
        """
        home_mappings = [
            ("d", ".ssh"),
            ("f", ".gitconfig"),
            # TODO: find a way to delegate to the image instead.
            ("f", ".yarnrc"),
            ("f", ".cargo/credentials"),
            ("f", ".pypirc"),
        ]
        for type, mapping in home_mappings:
            host_path = path.join(environ["HOME"], mapping)
            container_path = path.join(self.image.home, mapping)
            yield Bind(host_path, container_path, type)

        workspace_base = path.basename(self.args.workspace)
        workspace_path = path.join(self.image.home, workspace_base)
        yield Bind(self.args.workspace, workspace_path, "d")

        if path.isfile("/etc/localtime") and platform != "darwin":
            yield Bind("/etc/localtime", "/etc/localtime", "fro")
        if path.exists("/tmp/.X11-unix"):
            yield Bind("/tmp/.X11-unix", "/tmp/.X11-unix", "fro")

        yield from self._gpg_binds()

        for volume in self.args.volume or []:
            parts = volume.split(":")
            host_path = parts[0]
            container_path = parts[1]
            type = "d"
            if path.isfile(host_path):
                type = "f"
            if len(parts) == 3 and parts[2] == "ro":
                type += "ro"
            yield Bind(host_path, container_path, type)
