import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from utils.url_validation import validate_destination_url


class DestinationURLTests(unittest.TestCase):
    def test_rejects_unsafe_and_malformed_destinations(self):
        for url in (None, "", "javascript:alert(1)", "data:text/html,test",
                    "//example.com", "https://", "https://user:pass@example.com",
                    'https://example.com/<img src=x onerror=alert(1)>',
                    "https://example.com/\nheader", "https://example.com\\@evil.com",
                    "https://example.com:99999", "https://bad_host.com"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_destination_url(url)

    def test_preserves_valid_urls(self):
        for url in ("https://example.com/path?q=a&b=2#section",
                    "http://example.com:8080/", "https://[2001:db8::1]/",
                    "https://example.com/%3Cimg%3E", "https://example.com/it's"):
            with self.subTest(url=url):
                self.assertEqual(validate_destination_url(url), url)


if __name__ == "__main__":
    unittest.main()
