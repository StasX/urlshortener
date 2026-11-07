import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from migrations.migrate_short_codes import migrate
from utils.short_links import public_base_url


class LinkConfigurationTests(unittest.TestCase):
    def test_public_origin(self):
        self.assertEqual(public_base_url("https://short.example/"), "https://short.example")
        self.assertEqual(public_base_url("http://localhost:5000"), "http://localhost:5000")
        for value in ("javascript:alert(1)", "https://", "https://user:pass@example.com",
                      "https://example.com/path", "https://example.com?x=1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                public_base_url(value)

    def test_migration_preserves_codes_and_sets_unique_index(self):
        collection = MagicMock()
        collection.find.return_value = [{"_id": 1, "short_url": "http://old.example/abc123"}]
        self.assertEqual(migrate(collection, "https://short.example"), 1)
        collection.update_one.assert_called_once_with({"_id": 1}, {"$set": {
            "code": "abc123", "short_url": "https://short.example/abc123"}})
        collection.create_index.assert_called_once_with("code", unique=True)

    def test_duplicate_legacy_codes_abort_before_writing(self):
        collection = MagicMock()
        collection.find.return_value = [
            {"_id": 1, "short_url": "http://old.example/abc123"},
            {"_id": 2, "short_url": "https://other.example/abc123"},
        ]
        with self.assertRaises(ValueError):
            migrate(collection, "https://short.example")
        collection.update_one.assert_not_called()
        collection.create_index.assert_not_called()


HAS_DEPENDENCIES = all(importlib.util.find_spec(name) for name in ("flask", "mongoengine"))


@unittest.skipUnless(HAS_DEPENDENCIES, "Flask and MongoEngine are required")
class LinkRouteTests(unittest.TestCase):
    def setUp(self):
        from flask import Flask
        from views.home_view import home_blueprint
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True, SECRET_KEY="test-key",
                               PUBLIC_BASE_URL="https://short.example")
        self.app.register_blueprint(home_blueprint)
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["current_user"] = {"id": "user-id"}

    def test_creation_ignores_host_and_retries_duplicate_insert(self):
        from mongoengine import NotUniqueError
        with patch("views.home_view.UserModel.objects"), patch("views.home_view.UrlModel") as model, patch("views.home_view.choice", side_effect=list("abc123def456")):
            model.return_value.save.side_effect = [NotUniqueError(), None]
            response = self.client.post("/short", data={"url": "https://destination.example"},
                                        headers={"Host": "untrusted.example"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, {"url": "https://short.example/def456"})
            self.assertEqual(model.call_args.kwargs["code"], "def456")
            self.assertEqual(model.call_count, 2)

    def test_redirect_uses_code_and_atomic_increment(self):
        with patch("views.home_view.UrlModel.objects") as urls:
            urls.return_value.modify.return_value.full_url = "https://destination.example"
            for host in ("http://old.example", "https://new.example"):
                response = self.client.get("/abc123", base_url=host)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.headers["Location"], "https://destination.example")
                urls.assert_called_with(code="abc123")
                urls.return_value.modify.assert_called_with(inc__enters=1, new=True)

    def test_unknown_code_returns_404(self):
        with patch("views.home_view.UrlModel.objects") as urls, patch("views.home_view.render_template", return_value="Missing"):
            urls.return_value.modify.return_value = None
            self.assertEqual(self.client.get("/missing").status_code, 404)

    def test_exhausted_collisions_return_503(self):
        from mongoengine import NotUniqueError
        with patch("views.home_view.UserModel.objects"), patch("views.home_view.UrlModel") as model:
            model.return_value.save.side_effect = NotUniqueError()
            response = self.client.post("/short", data={"url": "https://destination.example"})
            self.assertEqual(response.status_code, 503)
            self.assertEqual(model.return_value.save.call_count, 10)

    def test_code_has_unique_database_constraint(self):
        from models.url_model import UrlModel
        self.assertTrue(UrlModel._fields["code"].unique)
        self.assertTrue(UrlModel._fields["code"].required)


if __name__ == "__main__":
    unittest.main()
