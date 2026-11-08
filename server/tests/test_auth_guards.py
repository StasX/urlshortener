import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
HAS_DEPENDENCIES = all(importlib.util.find_spec(name) for name in ("flask", "mongoengine", "requests"))


@unittest.skipUnless(HAS_DEPENDENCIES, "Flask, MongoEngine and requests are required")
class AuthenticationGuardTests(unittest.TestCase):
    def setUp(self):
        from flask import Flask
        from views.home_view import home_blueprint
        from views.dashboard_view import dashboard_blueprint

        self.app = Flask(__name__, template_folder="../src/templates")
        self.app.config.update(TESTING=True, SECRET_KEY="test-only-key")
        self.app.add_url_rule("/login", endpoint="auth_view.login", view_func=lambda: "Login")
        self.app.register_blueprint(home_blueprint)
        self.app.register_blueprint(dashboard_blueprint)
        self.client = self.app.test_client()

    def test_anonymous_requests_do_not_query_database(self):
        with patch("views.home_view.UserModel.objects") as users, patch("views.dashboard_view.UrlModel.objects") as urls:
            page = self.client.get("/dashboard")
            self.assertEqual(page.status_code, 302)
            self.assertEqual(page.headers["Location"], "/login")
            for response in (self.client.post("/short"), self.client.get("/urls-stat")):
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json, {"error": "Authentication required."})
            users.assert_not_called()
            urls.assert_not_called()

    def test_incomplete_session_is_treated_as_anonymous(self):
        for user in (None, {}, {"first_name": "Test"}, {"id": ""}, "invalid"):
            with self.subTest(user=user):
                with self.client.session_transaction() as session:
                    session["current_user"] = user
                self.assertEqual(self.client.get("/dashboard").status_code, 302)
                self.assertEqual(self.client.get("/urls-stat").status_code, 401)
                self.assertEqual(self.client.post("/short").status_code, 401)

    def test_authenticated_statistics_remain_scoped_to_user(self):
        with self.client.session_transaction() as session:
            session["current_user"] = {"id": "user-id"}
        with patch("views.dashboard_view.UrlModel.objects", return_value=[]) as urls:
            response = self.client.get("/urls-stat")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, [])
            urls.assert_called_once_with(user="user-id")

    def test_authenticated_short_request_reaches_validation(self):
        with self.client.session_transaction() as session:
            session["current_user"] = {"id": "user-id"}
        response = self.client.post("/short", data={"url": "javascript:alert(1)"})
        self.assertEqual(response.status_code, 400)

    def test_anonymous_deletion_does_not_query_database(self):
        with patch("views.dashboard_view.UrlModel.objects") as urls:
            response = self.client.delete("/urls/507f1f77bcf86cd799439011")
            self.assertEqual(response.status_code, 401)
            urls.assert_not_called()

    def test_deletion_is_scoped_to_signed_in_user(self):
        with self.client.session_transaction() as session:
            session["current_user"] = {"id": "user-id"}
        with patch("views.dashboard_view.UrlModel.objects") as urls:
            urls.return_value.delete.return_value = 1
            response = self.client.delete("/urls/507f1f77bcf86cd799439011")
            self.assertEqual(response.status_code, 204)
            self.assertEqual(response.data, b"")
            urls.assert_called_once_with(id="507f1f77bcf86cd799439011", user="user-id")

    def test_missing_or_unowned_link_returns_404(self):
        with self.client.session_transaction() as session:
            session["current_user"] = {"id": "user-id"}
        with patch("views.dashboard_view.UrlModel.objects") as urls:
            urls.return_value.delete.return_value = 0
            response = self.client.delete("/urls/507f1f77bcf86cd799439011")
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json, {"error": "Link not found."})

    def test_invalid_link_id_does_not_query_database(self):
        with self.client.session_transaction() as session:
            session["current_user"] = {"id": "user-id"}
        with patch("views.dashboard_view.UrlModel.objects") as urls:
            self.assertEqual(self.client.delete("/urls/invalid").status_code, 404)
            urls.assert_not_called()


if __name__ == "__main__":
    unittest.main()
