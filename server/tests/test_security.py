import hashlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from utils.security import Security


class PasswordSecurityTests(unittest.TestCase):
    def test_scrypt_round_trip_and_wrong_password(self):
        stored = Security.hash("a strong password 🔐")
        self.assertTrue(stored.startswith("scrypt$32768$8$1$"))
        self.assertTrue(Security.verify(stored, "a strong password 🔐"))
        self.assertFalse(Security.verify(stored, "wrong password"))
        self.assertFalse(Security.needs_rehash(stored))

    def test_random_salt_for_each_password(self):
        self.assertNotEqual(Security.hash("password"), Security.hash("password"))

    @patch.dict(os.environ, {"PASSWORDS_SALT": "legacy-salt"})
    def test_legacy_verification_and_migration(self):
        legacy = hashlib.sha512(b"passwordlegacy-salt").hexdigest()
        self.assertTrue(Security.needs_rehash(legacy))
        self.assertFalse(Security.verify(legacy, "wrong"))
        self.assertTrue(Security.verify(legacy, "password"))
        migrated = Security.hash("password")
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(Security.verify(migrated, "password"))
            self.assertFalse(Security.verify(legacy, "password"))

    def test_malformed_hashes_fail_closed(self):
        for stored in (None, "", "garbage", "scrypt$999999999$8$1$aa$bb",
                       "scrypt$32768$8$1$nothex$bad", "scrypt$32768$8$1$aa$bb"):
            with self.subTest(stored=stored):
                self.assertFalse(Security.verify(stored, "password"))

    def test_empty_password_rejected(self):
        for password in (None, ""):
            with self.subTest(password=password), self.assertRaises(ValueError):
                Security.hash(password)


if __name__ == "__main__":
    unittest.main()
