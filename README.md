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
