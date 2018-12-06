import paramiko
import threading
from os import path, environ

host_key_path = path.join(environ['HOME'], '.local/share/slipway/host_key')
host_key = paramiko.RSAKey(filename=host_key_path)


class SshServer (paramiko.ServerInterface):

    def __init__(self, user_name):
        self.user_name = user_name
        self.event = threading.Event()

    def _auth(self, user_name):
        if self.authenticated:
            return paramiko.AUTH_FAILED
        if self.user_name == user_name:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_none(self, user_name):
        return self._auth(user_name)

    def check_auth_publickey(self, user_name, key):
        return self._auth(user_name)

    def check_auth_password(self, user_name, password):
        return self._auth(user_name)

    def get_allowed_auths(self, username):
        return "password,publickey"

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(
        self, channel, term, width, height, pixelwidth, pixelheight, modes
    ):
        return True

    def enable_auth_gssapi(self):
        return False
