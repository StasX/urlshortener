"""Authenticated, owner-scoped dashboard invalidations (no link data on sockets)."""
from flask import current_app, g
from flask_socketio import SocketIO, join_room
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError

from utils.jwt_auth import login_required

socketio = SocketIO(async_mode="threading")


def configure_realtime(app):
    origins = [app.config["PUBLIC_BASE_URL"]]
    if app.config.get("SPA_DEV_ORIGIN"):
        origins.append(app.config["SPA_DEV_ORIGIN"])
    socketio.init_app(app, path="api/socket.io", cors_allowed_origins=origins)


@socketio.on("connect")
def connect(auth=None):
    @login_required()
    def authenticated():
        join_room(f"user:{g.current_user.id}")
        return True

    try:
        return authenticated() is True
    except (JWTExtendedException, PyJWTError):
        # JWT verification failures must reject the Socket.IO handshake.
        return False


def notify_links_changed(user_id):
    if user_id is not None and "socketio" in current_app.extensions:
        socketio.emit("links_changed", to=f"user:{user_id}")
