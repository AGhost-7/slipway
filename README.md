# Slipway
An easier way to use containers for development on Linux. It automatically
maps credentials, sets up things such as the clipboard, and corrects permission
issues which arise from developing with containers natively.

## Getting Started
Install slipway:
```sh
python3 -m pip install slipway
```

Run an example image:
```
slipway start aghost7/nodejs-dev:bionic-carbon
```

## GnuPG (GPG) Support
On your host, you will need to have gpg configured with the daemon running.
Slipway will detect that gpg is running and will automatically create a bind
mount (volume) to map the socket file into the container.

Enable gpg signing git commits:
```sh
git config --global commit.gpgSign true
```

If you want to always sign tags:
```sh
git config --global tag.forceSignAnnotated true
```

Since we want gnupg to be used from the terminal interface, we need to change
the configuration under `~/.gnupg/gpg.conf`:

```
use-agent
pinentry-mode loopback
```

## Developing
Install pipenv:
```
python3 -m pip install --user --upgrade pipenv
```

Install dependencies and load virtualenv:
```
pipenv install --dev
pipenv shell
```

Run tests:
```
pytest
```
