"""Validate stored redirect destinations without fetching them."""

import ipaddress
import re
from urllib.parse import urlsplit


def validate_destination_url(url):
    if not isinstance(url, str) or not url or len(url) > 4096:
        raise ValueError("Provide a valid HTTP or HTTPS URL.")
    if any(ord(char) <= 32 or ord(char) == 127 or char in '<>"\\' for char in url):
        raise ValueError("URL contains invalid characters.")
    try:
        parts = urlsplit(url)
        if (parts.scheme not in ("http", "https") or not parts.hostname
                or parts.username is not None or parts.password is not None):
            raise ValueError
        if parts.port is not None and not 1 <= parts.port <= 65535:
            raise ValueError
        host = parts.hostname.encode("idna").decode("ascii")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            labels = host.rstrip(".").split(".")
            if len(host) > 253 or any(
                not re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?", label)
                for label in labels
            ):
                raise ValueError
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Provide a valid HTTP or HTTPS URL without credentials.") from exc
    return url
