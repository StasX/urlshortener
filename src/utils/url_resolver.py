"""Resolve one redirect without permitting requests to internal networks."""

import http.client
import ipaddress
import socket
import ssl
from urllib.parse import urljoin, urlsplit


class InvalidPublicURL(ValueError):
    pass


def validate_public_url(url):
    if not isinstance(url, str) or not url or len(url) > 4096:
        raise InvalidPublicURL("Provide a valid public HTTP or HTTPS URL.")
    if any(ord(char) <= 32 or ord(char) == 127 for char in url):
        raise InvalidPublicURL("URL contains invalid characters.")
    try:
        parts = urlsplit(url)
        if (parts.scheme not in ("http", "https") or not parts.hostname
                or parts.username is not None or parts.password is not None):
            raise ValueError
        port = parts.port or (443 if parts.scheme == "https" else 80)
        if port not in (80, 443):
            raise ValueError
        host = parts.hostname.encode("idna").decode("ascii")
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        if not addresses:
            raise ValueError
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if not ip.is_global or (isinstance(ip, ipaddress.IPv6Address)
                                    and (ip.ipv4_mapped or ip.sixtofour or ip.teredo)):
                raise ValueError
    except (ValueError, UnicodeError, OSError) as exc:
        raise InvalidPublicURL("URL must point to a public HTTP or HTTPS destination on port 80 or 443.") from exc
    return parts, host, port, addresses[0][4][0]


class _PinnedConnection(http.client.HTTPConnection):
    """Connect to the checked IP while retaining the hostname for TLS and Host."""

    def __init__(self, host, port, address, secure):
        super().__init__(host, port, timeout=5)
        self.address = address
        self.secure = secure

    def connect(self):
        self.sock = socket.create_connection((self.address, self.port), self.timeout)
        if self.secure:
            self.sock = ssl.create_default_context().wrap_socket(
                self.sock, server_hostname=self.host)


def resolve_public_url(url):
    parts, host, port, address = validate_public_url(url)
    connection = _PinnedConnection(host, port, address, parts.scheme == "https")
    try:
        path = parts.path or "/"
        if parts.query:
            path += "?" + parts.query
        connection.request("GET", path)
        response = connection.getresponse()
        if response.status in (301, 302, 303, 307, 308):
            location = response.getheader("Location")
            if location:
                target = urljoin(url, location)
                validate_public_url(target)
                return target
        return url
    finally:
        # Only headers are needed; never download the response body or follow redirects.
        connection.close()
