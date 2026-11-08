"""Run inside the server container with MongoDB available; use an isolated database."""

from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit
from uuid import uuid4

from mongoengine import connect, disconnect

from app import app, limiter
from models.url_model import UrlModel
from models.user_model import UserModel
from utils.app_config import AppConfig


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    database_name = "urlshortener_ci_" + uuid4().hex
    disconnect()
    connection = connect(db=database_name, host=AppConfig.db_host, port=AppConfig.db_port)
    app.config["TESTING"] = True
    limiter.enabled = False
    try:
        guest = app.test_client()
        for path in ("/", "/login", "/register", "/health"):
            check(guest.get(path).status_code == 200, f"Page failed: {path}")
        check(guest.get("/urls-stat").status_code == 401, "Guest statistics must be protected")
        check(guest.get("/dashboard").status_code == 302, "Guest dashboard must redirect to login")
        response = guest.post("/short", data={"url": "javascript:alert(1)"})
        check(response.status_code == 400, "Unsafe destination must be rejected")
        before = datetime.now(timezone.utc).replace(tzinfo=None)
        response = guest.post("/short", data={"url": "https://example.com/guest"})
        check(response.status_code == 200, "Guest creation failed")
        path = urlsplit(response.json["url"]).path
        link = UrlModel.objects.get(code=path[1:])
        check(link.user is None, "Guest link must not have an owner")
        check(before + timedelta(hours=24) <= link.expires_at <=
              datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24),
              "Guest expiry must be 24 hours after creation")
        response = guest.get(path)
        check(response.status_code == 302 and response.location == "https://example.com/guest",
              "Guest link must redirect to its destination")
        check(UrlModel.objects.get(id=link.id).enters == 1, "Redirect must count a visit")
        indexes = UrlModel._get_collection().index_information()
        check(any(index.get("expireAfterSeconds") == 0 and index["key"] == [("expires_at", 1)]
                  for index in indexes.values()), "Expiry TTL index must exist")
        UrlModel.objects(id=link.id).update(set__expires_at=before - timedelta(seconds=1))
        response = guest.get(path)
        check(response.status_code == 404 and b"error-card" in response.data,
              "Expired links must display the styled 404 page")

        member = app.test_client()
        registration = {
            "firstName": "Test", "lastName": "Member", "email": "member@example.com",
            "password": "ci-test-password", "repeatPassword": "different",
        }
        response = member.post("/register", data=registration)
        check(response.status_code == 400 and b"Passwords must match." in response.data,
              "Password mismatch must show validation feedback")
        registration["repeatPassword"] = registration["password"]
        check(member.post("/register", data=registration).status_code == 302, "Registration failed")
        owner = UserModel.objects.get(email=registration["email"])
        response = member.post("/short", data={"url": "https://example.com/member"})
        check(response.status_code == 200, "Member link creation failed")
        permanent = UrlModel.objects.get(code=urlsplit(response.json["url"]).path[1:])
        check(permanent.expires_at is None and permanent.user.id == owner.id,
              "Member links must be permanent and owned")
        stats = member.get("/urls-stat").json
        check(len(stats) == 1 and stats[0]["id"] == str(permanent.id),
              "Dashboard must only include owned links")
        check(member.get("/dashboard").status_code == 200, "Member dashboard failed")
        check(guest.delete("/urls/" + str(permanent.id)).status_code == 401,
              "Guest deletion must be blocked")
        check(member.delete("/urls/" + str(link.id)).status_code == 404,
              "Member must not manage guest links")
        check(member.delete("/urls/" + str(permanent.id)).status_code == 204,
              "Member deletion failed")
        check(member.delete("/logout").status_code == 200, "Logout failed")
        check(member.post("/login", data={"username": registration["email"],
                                         "password": registration["password"]}).status_code == 302,
              "Login failed")

        limiter.enabled = True
        limiter.reset()
        responses = [guest.get("/login") for _ in range(5)]
        check(responses[-1].status_code == 429 and b"error-card" in responses[-1].data,
              "Rate limit must return the styled 429 page")
        check(guest.get("/health").status_code == 200, "Health must remain exempt from rate limits")
        print("Compose integration passed: pages, authentication, guest expiry, TTL index, ownership, and rate limits")
    finally:
        connection.drop_database(database_name)
        disconnect()


if __name__ == "__main__":
    main()
