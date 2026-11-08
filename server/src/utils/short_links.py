from urllib.parse import urlsplit


def public_base_url(value):
    """Validate the configured public origin, independent of request headers."""
    try:
        parts = urlsplit(value)
        if (parts.scheme not in ("http", "https") or not parts.hostname
                or parts.username is not None or parts.password is not None
                or parts.path not in ("", "/") or parts.query or parts.fragment
                or any(ord(char) <= 32 or char in '<>"\\' for char in value)):
            raise ValueError
        if parts.port is not None and not 1 <= parts.port <= 65535:
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise ValueError("PUBLIC_BASE_URL must be an HTTP or HTTPS origin, such as https://short.example.com") from exc
    return value.rstrip("/")
