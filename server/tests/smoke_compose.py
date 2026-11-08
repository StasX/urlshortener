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
        check(guest.get("/api/links").status_code == 401, "Guest statistics must be protected")
        check(guest.get("/dashboard").status_code == 200, "Dashboard SPA shell must support direct navigation")
        response = guest.post("/api/links", json={"url": "javascript:alert(1)"})
        check(response.status_code == 400, "Unsafe destination must be rejected")
        before = datetime.now(timezone.utc).replace(tzinfo=None)
        # BSON dates truncate microseconds to milliseconds. Compare both bounds
        # at that same precision so fast requests do not fail intermittently.
        before = before.replace(microsecond=(before.microsecond // 1000) * 1000)
        response = guest.post("/api/links", json={"url": "https://example.com/guest"})
        after = datetime.now(timezone.utc).replace(tzinfo=None)
        after = after.replace(microsecond=(after.microsecond // 1000) * 1000)
        check(response.status_code == 200, "Guest creation failed")
        path = urlsplit(response.json["url"]).path
        link = UrlModel.objects.get(code=path[1:])
        check(link.user is None, "Guest link must not have an owner")
        check(before + timedelta(hours=24) <= link.expires_at <=
              after + timedelta(hours=24),
              f"Guest expiry must be 24 hours after creation: got {link.expires_at}, "
              f"expected between {before + timedelta(hours=24)} and {after + timedelta(hours=24)}")
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
        response = member.post("/api/auth/register", json=registration)
        check(response.status_code == 400 and "Passwords must match." in response.json["error"],
              "Password mismatch must show validation feedback")
        registration["repeatPassword"] = registration["password"]
        check(member.post("/api/auth/register", json=registration).status_code == 201, "Registration failed")
        owner = UserModel.objects.get(email=registration["email"])
        token_cookie = member.get_cookie("access_token_cookie", path="/api/")
        check(token_cookie.http_only, "JWT must use an HttpOnly cookie")
        check("access_token" not in member.get("/api/auth/me").json, "JWT must not be returned to JavaScript")
        csrf_headers = {"X-CSRF-TOKEN": member.get_cookie("csrf_access_token").value}
        denied = member.post("/api/links", json={"url": "https://example.com/blocked"})
        check(denied.status_code == 401, "Authenticated writes without CSRF must be rejected")
        response = member.post("/api/links", json={"url": "https://example.com/member"}, headers=csrf_headers)
        check(response.status_code == 200, "Member link creation failed")
        permanent = UrlModel.objects.get(code=urlsplit(response.json["url"]).path[1:])
        check(permanent.expires_at is None and permanent.user.id == owner.id,
              "Member links must be permanent and owned")
        stats = member.get("/api/links").json
        check(len(stats) == 1 and stats[0]["id"] == str(permanent.id),
              "Dashboard must only include owned links")
        check(member.get("/dashboard").status_code == 200, "Member dashboard failed")
        check(guest.delete("/api/links/" + str(permanent.id)).status_code == 401,
              "Guest deletion must be blocked")
        check(member.delete("/api/links/" + str(link.id), headers=csrf_headers).status_code == 404,
              "Member must not manage guest links")
        check(member.delete("/api/links/" + str(permanent.id), headers=csrf_headers).status_code == 204,
              "Member deletion failed")
        check(member.post("/api/auth/logout", headers=csrf_headers).status_code == 200, "Logout failed")
        replay = app.test_client()
        replay.set_cookie("access_token_cookie", token_cookie.value, path="/api/")
        check(replay.get("/api/links").status_code == 401, "Logged-out token must be revoked across clients")
        check(member.post("/api/auth/login", json={"email": registration["email"],
                                         "password": registration["password"]}).status_code == 200,
              "Login failed")

        limiter.enabled = True
        limiter.reset()
        responses = [guest.post("/api/auth/login", json={"email": "missing@example.com", "password": "wrong"}) for _ in range(5)]
        check(responses[-1].status_code == 429 and "error" in responses[-1].json,
              "API rate limit must return JSON for the shared frontend error component")
        check(guest.get("/health").status_code == 200, "Health must remain exempt from rate limits")
        print("Compose integration passed: Vue shell, JWT cookies, CSRF, revocation, guest expiry, ownership, and rate limits")
    finally:
        connection.drop_database(database_name)
        disconnect()


if __name__ == "__main__":
    main()
