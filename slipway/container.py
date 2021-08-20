import os
from os import path
from .image import Image
from .volumes import Volumes
from .binds import Binds
from .util import snake_case
from .xdg_open import XdgOpen


class Container(object):
    def __init__(self, client, args):
        self.client = client
        self.args = args
        self.xdg_open = XdgOpen(path.join(args.runtime_dir, "slipway"))
        self.image = Image(self.client, self.args)
        self.volumes = Volumes(self.client, self.args, self.image)
        self.binds = Binds(self.client, self.args, self.image)
        self.name = "slipway_" + snake_case(self.args.image)

    def _entrypoint_script(self):
        module_dir = path.dirname(path.abspath(__file__))
        return path.abspath(path.join(module_dir, "./entrypoint.py"))

    def _volumes_env(self):
        return ",".join(list(map(lambda vol: vol.path, self.volumes.list())))

    def _append_docker_gid(self, arguments):
        with open("/etc/group") as file_descriptor:
            content = file_descriptor.read()
            for line in content.split("\n"):
                parts = line.split(":")
                if parts[0] == "docker":
                    arguments.append("-e")
                    arguments.append("SLIPWAY_DOCKER_GID={}".format(parts[2]))
                    break

    def _append_id_mappings(self, arguments):
        for (option, host_id, container_id, rest) in [
            ("uidmap", os.getuid(), self.image.user_id, self.image.user_ids),
            ("gidmap", os.getgid(), self.image.group_id, self.image.group_ids),
        ]:
            arguments.extend(
                [
                    f"--{option}={container_id}:0:1",
                    f"--{option}=0:1:{container_id}",
                ]
            )
            rest.sort()
            next_mapping = container_id + 1
            for id in rest:
                if id > container_id:
                    arguments.append(f"--{option}={id}:{next_mapping}:1")
                    next_mapping += 1

    def _run_arguments(self):
        arguments = []
        if self.args.runtime == "podman":
            arguments.append("podman")
        else:
            arguments.append("docker")

        arguments.extend(
            [
                "run",
                # Required for strace and other debugging tools to work.
                "--cap-add",
                "SYS_PTRACE",
                # required for nmap
                "--cap-add",
                "NET_RAW",
                "--rm",
                "-ti",
                "--detach-keys",
                "ctrl-q,ctrl-q",
                "--name",
                self.name,
                "-e",
                "GH_USER",
                "-e",
                "GH_PASS",
                "-e",
                "DISPLAY",
            ]
        )
        arguments.append("--network={}".format(self.args.network))

        if self.client.has_uidmap():
            self._append_id_mappings(arguments)

        arguments.extend(
            [
                "-v",
                "{}:/usr/bin/xdg-open".format(self.xdg_open.client_path),
                "-v",
                "{}/slipway:/run/slipway".format(self.args.runtime_dir),
            ]
        )

        if self.args.mount_docker:
            arguments.append("-v")
            arguments.append("/run/docker.sock:/run/docker.sock")
            self._append_docker_gid(arguments)

        for env in self.args.environment or []:
            arguments.append("-e")
            arguments.append(env)

        for device in self.args.device or []:
            arguments.append("--device")
            arguments.append(device)

        for bind in self.binds.list():
            arguments.append("-v")
            argument = bind.host_path + ":" + bind.container_path
            if "ro" in bind.type:
                argument += ":ro"
            arguments.append(argument)

        for volume in self.volumes.list():
            arguments.append("--mount")
            arguments.append(
                "type=volume,source={},target={}".format(volume.name, volume.path)
            )

        arguments.append(self.image.name)
        return arguments

    def exists(self):
        return self.name in self.client.list_all_containers()

    def run(self):
        os.execvp(self.args.runtime, self._run_arguments())
