import subprocess
import json


class PodmanClient(object):
    def list_volume_names(self):
        result = subprocess.run(
            ['podman', 'volumes', 'ls', '--format', '{{.Name}}'],
            capture_output=True
        )
        return str(result.stdout, 'utf8').strip().split('\n')

    def create_volume(self, name):
        subprocess.run(
            ['podman', 'volume', 'create', name],
            capture_output=True
        )

    def pull_image(self, name):
        subprocess.run(['podman', 'pull', name])

    def inspect_image(self, name):
        result = subprocess.run(
            ['podman', 'image', 'inspect', '--format', '{{json .}}', name],
            capture_output=True
        )
        return json.loads(str(result.stdout, 'utf8').strip())

    def remove_volume(self, name):
        result = subprocess.run(
            ['podman', 'volumes', 'remove', name])
        assert(result.returncode == 0)

    def image_exists(self, name):
        result = subprocess.run(
            ['podman', 'image', 'inspect', name],
            capture_output=True)
        return result.returncode == 0
