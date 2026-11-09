import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jwt_helpers import make_app, authenticate
from utils.realtime import configure_realtime, notify_links_changed, socketio


class RealtimeTests(unittest.TestCase):
    def setUp(self):
        self.app, self.client, self.user = make_app(self)
        configure_realtime(self.app)

    def connect(self):
        # SocketIOTestClient hardcodes /socket.io. Build its request at the
        # deployed path so Flask sends only cookies valid for /api/.
        build_request = self.client._request_from_builder_args

        def at_api_path(*args, **kwargs):
            kwargs["kwargs"]["path"] = "/api/socket.io"
            return build_request(*args, **kwargs)

        with patch.object(self.client, "_request_from_builder_args", side_effect=at_api_path):
            client = socketio.test_client(self.app, flask_test_client=self.client)
        self.addCleanup(lambda: client.disconnect() if client.is_connected() else None)
        return client

    def test_anonymous_connection_is_rejected(self):
        self.assertFalse(self.connect().is_connected())

    def test_revoked_connection_is_rejected(self):
        authenticate(self.app, self.client, self.user.id)
        self.revoked.return_value.first.return_value = object()
        self.assertFalse(self.connect().is_connected())

    def test_notifications_are_scoped_to_owner_and_have_no_link_data(self):
        authenticate(self.app, self.client, self.user.id)
        client = self.connect()
        self.assertTrue(client.is_connected())
        with self.app.app_context():
            notify_links_changed("another-user")
            notify_links_changed(None)
        self.assertEqual(client.get_received(), [])
        with self.app.app_context():
            notify_links_changed(self.user.id)
        events = client.get_received()
        self.assertEqual([event["name"] for event in events], ["links_changed"])
        self.assertEqual(events[0]["args"], [])

    def test_creation_and_deletion_notify_open_dashboard(self):
        authenticate(self.app, self.client, self.user.id)
        client = self.connect()
        with patch("views.home_view.UrlModel"):
            self.assertEqual(self.client.post("/api/links", json={"url": "https://example.com"}).status_code, 200)
        with patch("views.dashboard_view.UrlModel.objects") as urls:
            urls.return_value.delete.return_value = 1
            self.assertEqual(self.client.delete("/api/links/507f1f77bcf86cd799439011").status_code, 204)
        self.assertEqual([event["name"] for event in client.get_received()], ["links_changed", "links_changed"])

    def test_visit_notifies_link_owner(self):
        authenticate(self.app, self.client, self.user.id)
        client = self.connect()
        with patch("views.home_view.UrlModel.objects") as urls:
            link = urls.return_value.filter.return_value.modify.return_value
            link.full_url = "https://example.com"
            link.to_mongo.return_value = {"user": self.user.id}
            self.assertEqual(self.client.get("/abc123").status_code, 302)
        self.assertEqual([event["name"] for event in client.get_received()], ["links_changed"])
