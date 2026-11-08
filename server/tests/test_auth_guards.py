import importlib.util
import sys
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
HAS_DEPENDENCIES = all(importlib.util.find_spec(name) for name in ("flask", "mongoengine", "flask_jwt_extended"))


@unittest.skipUnless(HAS_DEPENDENCIES, "Application dependencies are required")
class AuthenticationGuardTests(unittest.TestCase):
    def setUp(self):
        from jwt_helpers import make_app
        self.app, self.client, self.user = make_app(self, csrf=True)

    def sign_in(self, **options):
        from jwt_helpers import authenticate
        return authenticate(self.app, self.client, self.user.id, **options)

    def test_anonymous_management_is_rejected_without_database_queries(self):
        with patch("views.dashboard_view.UrlModel.objects") as urls:
            for response in (self.client.get("/api/links"), self.client.delete("/api/links/507f1f77bcf86cd799439011")):
                self.assertEqual(response.status_code, 401)
                self.assertIn("error", response.json)
            urls.assert_not_called()
            self.users.assert_not_called()

    def test_legacy_session_does_not_authenticate(self):
        with self.client.session_transaction() as session:
            session["current_user"] = {"id": str(self.user.id)}
        self.assertEqual(self.client.get("/api/links").status_code, 401)

    def test_guest_me_does_not_query_database(self):
        self.assertEqual(self.client.get("/api/auth/me").json, {"user": None})
        self.users.assert_not_called()

    def test_expired_token_is_rejected(self):
        self.sign_in(expires_delta=timedelta(seconds=-1))
        self.assertEqual(self.client.get("/api/links").status_code, 401)
        self.users.assert_not_called()

    def test_invalid_token_is_not_treated_as_guest(self):
        self.client.set_cookie("access_token_cookie", "forged-token", path="/api/")
        response = self.client.post("/api/links", json={"url": "https://example.com"})
        self.assertEqual(response.status_code, 401)
        self.users.assert_not_called()

    def test_revoked_token_is_rejected(self):
        self.sign_in()
        self.revoked.return_value.first.return_value = object()
        self.assertEqual(self.client.get("/api/links").status_code, 401)
        self.users.assert_not_called()

    def test_deleted_account_is_rejected(self):
        self.sign_in()
        self.users.return_value.first.return_value = None
        self.assertEqual(self.client.get("/api/links").status_code, 401)

    def test_csrf_is_required_for_authenticated_writes(self):
        self.sign_in()
        with patch("views.dashboard_view.UrlModel.objects") as urls:
            response = self.client.delete("/api/links/507f1f77bcf86cd799439011")
            self.assertEqual(response.status_code, 401)
            urls.assert_not_called()

    def test_cross_origin_login_is_rejected(self):
        response = self.client.post("/api/auth/login", json={"email": "test@example.com", "password": "password"},
                                    headers={"Origin": "https://evil.example"})
        self.assertEqual(response.status_code, 403)
        self.users.assert_not_called()

    def test_statistics_are_scoped_to_token_owner(self):
        self.sign_in()
        with patch("views.dashboard_view.UrlModel.objects", return_value=[]) as urls:
            self.assertEqual(self.client.get("/api/links").json, [])
            urls.assert_called_once_with(user=self.user.id)

    def test_deletion_is_scoped_to_token_owner(self):
        headers = self.sign_in()
        with patch("views.dashboard_view.UrlModel.objects") as urls:
            urls.return_value.delete.return_value = 1
            response = self.client.delete("/api/links/507f1f77bcf86cd799439011", headers=headers)
            self.assertEqual(response.status_code, 204)
            urls.assert_called_once_with(id="507f1f77bcf86cd799439011", user=self.user.id)

    def test_missing_or_unowned_link_returns_404(self):
        headers = self.sign_in()
        with patch("views.dashboard_view.UrlModel.objects") as urls:
            urls.return_value.delete.return_value = 0
            response = self.client.delete("/api/links/507f1f77bcf86cd799439011", headers=headers)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json, {"error": "Link not found."})

    def test_invalid_link_id_does_not_query_database(self):
        headers = self.sign_in()
        with patch("views.dashboard_view.UrlModel.objects") as urls:
            self.assertEqual(self.client.delete("/api/links/invalid", headers=headers).status_code, 404)
            urls.assert_not_called()

    def test_non_object_auth_payload_is_rejected(self):
        for endpoint in ("login", "register"):
            response = self.client.post("/api/auth/" + endpoint, json=[])
            self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
