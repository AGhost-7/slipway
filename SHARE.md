# Share Protocol

The share protocol is a bi-directional, multiplexing protocol done over http.
It is an end-to-end encrypted protocol designed to allow sharing a terminal
session as well as local ports with others in a secure manner.

## Session Initiation
Similar to websockets, the connection is initiated with an `UPGRADE` http
request. This allows running the bridge server to sit behind a reverse proxy
such as nginx. Using the protocol over https is also possible.

```
sharing client <-> bridge server <-> connecting client
```

To initiate a sharing session, the sharing client first connects to the bridge
server. The sharing client passes a 64 byte token, encoded in base 16. The
accept header MUST be set to `application/vnd.slipway.share`.

Example request:
```
POST /session/<token> HTTP/1.1
Accept: application/vnd.slipway.share
Connection: Upgrade
Upgrade: tcp
```

If there is already a session with the same token, the server will reject the
request with a 409 (Conflict) status. If the connection is successful, the
server will return a `UPGRADED` response. The content type MUST be set to
`application/vnd.slipway.share`.

Example response:
```
HTTP/1.1 101 UPGDRADED
Content-Type: application/vnd.slipway.share
Connection: Upgrade
Upgrade: tcp

<frames>
```

The connecting client initiates the session by connecting to the server using
an `UPGRADE` request. The content type MUST be set to
`application/vnd.slipway.share`. The client MUST send the corresponding token.

Example request:
```
PATCH /session/<token> HTTP/1.1
Content-Type: application/vnd.slipway.share
Connection: Upgrade
Upgrade: tcp
```

If the session does not exit, a 404 (Not Found) MUST returned. If the
connection is successfully established, a 101 (Upgraded) response it sent:
```
HTTP/1.1 101 UPGDRADED
Content-Type: application/vnd.slipway.share
Connection: Upgrade
Upgrade: tcp

<frames>
```

During the session initiation, the server MAY return a 302 (Found). The client
MUST follow this redirect.

## Encryption Frame
The encryption frames use a binary format. The header is of a set size, but the
body is varied. A frame can be ignored if it fails to decrypt.

```
nonce = 12 bytes
size = 4 bytes
body = varied
```

To encrypt, we use AES GCM with a 96 bit nonce. GCM has been selected due to
its broad support and reasonable performance.

The bridge server MUST NOT know how to decrypt the frames. It only knows how to
pass them from one client to another using the token.

## Data Frame
Once decrypted, the data frame is now available. The client can then decide
to ignore the frame if it is trying to access something which wasn't exposed.

Stdio frame (type 0b00000001):
```
type = 1 byte
io = 1 byte
body = varied
```

Tcp frame (type 0b00000002):
```
type = 1 byte
port = 2 byte
tcp session = 2 byte
body = varied
```

Since the size of the fully decrypted frame is known, simple arithmetic can
be used to determine the size of the body.

```
Stdio body size = decrypted size - 2 bytes
Tcp body size = decrypted size - 5 bytes
```
