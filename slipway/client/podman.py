import subprocess
import json
from typing import Optional


class PodmanClient(object):
    @property
    def runtime(self):
        return "podman"

    def list_volume_names(self):
        result = subprocess.run(
            ["podman", "volume", "ls", "--format", "{{.Name}}"], capture_output=True
        )
        return str(result.stdout, "utf8").strip().split("\n")

    def create_volume(self, name):
        subprocess.run(["podman", "volume", "create", name], capture_output=True)

    def pull_image(self, name):
        subprocess.run(["podman", "pull", name])

    def inspect_image(self, name):
        result = subprocess.run(
            ["podman", "image", "inspect", "--format", "{{json .}}", name],
            capture_output=True,
        )
        images = json.loads(str(result.stdout, "utf8").strip())
        if isinstance(images, list):
            return images[0]

        return images

    def remove_volume(self, name):
        result = subprocess.run(["podman", "volume", "remove", name])
        assert result.returncode == 0

    def image_exists(self, name):
        result = subprocess.run(
            ["podman", "image", "inspect", name], capture_output=True
        )
        return result.returncode == 0

    def has_uidmap(self):
        return True

    def is_rootless(self):
        result = subprocess.run(["podman", "info", "-f", "json"], capture_output=True)

        info = json.loads(str(result.stdout, "utf-8"))
        return info["host"]["security"]["rootless"]

    def list_all_containers(self):
        result = subprocess.run(
            ["podman", "ps", "-a", "--format", "{{.Names}}"], capture_output=True
        )
        return str(result.stdout, "utf-8").strip().split("\n")

    def image_file(self, name: str, file_path: str) -> Optional[str]:
        result = subprocess.run(
            ["podman", "run", "--rm", "--entrypoint", "/bin/cat", name, file_path],
            capture_output=True,
        )

        return str(result.stdout, "utf-8")
