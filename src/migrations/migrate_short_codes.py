"""Run with the application stopped, before deploying the unique code field."""

import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.short_links import public_base_url


def migrate(collection, base_url):
    base_url = public_base_url(base_url)
    records = []
    seen = set()
    for record in collection.find({}, {"short_url": 1, "code": 1}):
        path = urlsplit(record["short_url"]).path
        code = record.get("code") or path.removeprefix("/")
        if (not code or not code.isascii() or not code.isalnum()
                or code in seen or path != "/" + code):
            raise ValueError(f"Invalid or duplicate code for record {record['_id']}; no records changed.")
        seen.add(code)
        records.append((record["_id"], code))
    for record_id, code in records:
        collection.update_one({"_id": record_id}, {"$set": {
            "code": code, "short_url": f"{base_url}/{code}"}})
    collection.create_index("code", unique=True)
    return len(records)


if __name__ == "__main__":
    from pymongo import MongoClient
    from utils.app_config import AppConfig

    with MongoClient(host=AppConfig.db_host, port=AppConfig.db_port) as client:
        count = migrate(client[AppConfig.db_name]["url_model"], AppConfig.public_base_url)
        print(f"Migrated {count} short links and created the unique code index.")
