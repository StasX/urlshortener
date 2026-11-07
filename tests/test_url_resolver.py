import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from utils.url_resolver import InvalidPublicURL, _PinnedConnection, resolve_public_url, validate_public_url


def answer(ip):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 80))]


class URLResolverTests(unittest.TestCase):
    def test_invalid_inputs_do_not_connect(self):
        for url in (None, "", "file:///etc/passwd", "ftp://example.com",
                    "http://user:pass@example.com", "http://example.com:8080",
                    "http://example.com\r\nX-Test: yes"):
            with self.subTest(url=url), self.assertRaises(InvalidPublicURL):
                validate_public_url(url)

    def test_nonpublic_dns_results_are_rejected(self):
        for ip in ("127.0.0.1", "10.0.0.1", "172.16.0.1", "192.168.1.1",
                   "169.254.169.254", "0.0.0.0", "::1", "fc00::1",
                   "::ffff:127.0.0.1"):
            with self.subTest(ip=ip), patch("utils.url_resolver.socket.getaddrinfo", return_value=answer(ip)):
                with self.assertRaises(InvalidPublicURL):
                    validate_public_url("http://example.com")

    @patch("utils.url_resolver.socket.getaddrinfo")
    def test_mixed_public_private_dns_is_rejected(self, lookup):
        lookup.return_value = answer("8.8.8.8") + answer("127.0.0.1")
        with self.assertRaises(InvalidPublicURL):
            validate_public_url("https://example.com")

    @patch("utils.url_resolver._PinnedConnection")
    @patch("utils.url_resolver.socket.getaddrinfo", return_value=answer("8.8.8.8"))
    def test_relative_redirect_and_no_body_download(self, lookup, connection_class):
        connection = connection_class.return_value
        response = connection.getresponse.return_value
        response.status = 302
        response.getheader.return_value = "/destination"
        self.assertEqual(resolve_public_url("https://example.com/start"),
                         "https://example.com/destination")
        connection_class.assert_called_once_with("example.com", 443, "8.8.8.8", True)
        connection.request.assert_called_once_with("GET", "/start")
        response.read.assert_not_called()
        connection.close.assert_called_once()

    @patch("utils.url_resolver._PinnedConnection")
    @patch("utils.url_resolver.socket.getaddrinfo")
    def test_internal_redirect_rejected_without_following(self, lookup, connection_class):
        lookup.side_effect = [answer("8.8.8.8"), answer("127.0.0.1")]
        response = connection_class.return_value.getresponse.return_value
        response.status = 302
        response.getheader.return_value = "http://localhost/admin"
        with self.assertRaises(InvalidPublicURL):
            resolve_public_url("https://example.com")
        connection_class.assert_called_once()
        connection_class.return_value.close.assert_called_once()

    @patch("utils.url_resolver.socket.create_connection")
    @patch("utils.url_resolver.ssl.create_default_context")
    def test_connection_pins_ip_and_verifies_original_tls_hostname(self, context, connect):
        connection = _PinnedConnection("example.com", 443, "8.8.8.8", True)
        connection.connect()
        connect.assert_called_once_with(("8.8.8.8", 443), 5)
        context.return_value.wrap_socket.assert_called_once_with(
            connect.return_value, server_hostname="example.com")
        connection.close()

    @patch("utils.url_resolver._PinnedConnection")
    @patch("utils.url_resolver.socket.getaddrinfo", return_value=answer("8.8.8.8"))
    def test_timeout_closes_connection(self, lookup, connection_class):
        connection_class.return_value.getresponse.side_effect = TimeoutError
        with self.assertRaises(TimeoutError):
            resolve_public_url("https://example.com")
        connection_class.return_value.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
