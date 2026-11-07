from hashlib import scrypt, sha512
from hmac import compare_digest
from os import environ, urandom
import re


class Security:
    @staticmethod
    def hash(plain_text):
        if not isinstance(plain_text, str) or not plain_text:
            raise ValueError("Password must not be empty.")
        salt = urandom(16)
        digest = scrypt(plain_text.encode("utf-8"), salt=salt,
                        n=32768, r=8, p=1, dklen=64, maxmem=64 * 1024 * 1024)
        return f"scrypt$32768$8$1${salt.hex()}${digest.hex()}"

    @staticmethod
    def needs_rehash(stored_hash):
        return isinstance(stored_hash, str) and re.fullmatch(r"[0-9a-f]{128}", stored_hash) is not None

    @staticmethod
    def verify(stored_hash, plain_text):
        if not isinstance(stored_hash, str) or not isinstance(plain_text, str) or not plain_text:
            return False
        if Security.needs_rehash(stored_hash):
            # Retain the old salt until all legacy accounts have migrated.
            salt = environ.get("PASSWORDS_SALT")
            if salt is None:
                return False
            digest = sha512(plain_text.encode("utf-8") + salt.encode("utf-8")).hexdigest()
            return compare_digest(stored_hash, digest)
        try:
            method, n, r, p, salt_hex, digest_hex = stored_hash.split("$")
            # Accept only our format; stored parameters cannot trigger excessive work.
            if (method, n, r, p) != ("scrypt", "32768", "8", "1"):
                return False
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(digest_hex)
            if len(salt) != 16 or len(expected) != 64:
                return False
            actual = scrypt(plain_text.encode("utf-8"), salt=salt,
                            n=32768, r=8, p=1, dklen=64, maxmem=64 * 1024 * 1024)
            return compare_digest(expected, actual)
        except (ValueError, TypeError):
            return False
