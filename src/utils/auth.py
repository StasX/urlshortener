from functools import wraps

from flask import jsonify, redirect, session, url_for


def login_required(*, api=False):
    """Require a signed-in session before a view reads user data."""
    def decorate(view):
        @wraps(view)
        def guarded(*args, **kwargs):
            user = session.get("current_user")
            if not isinstance(user, dict) or not user.get("id"):
                if api:
                    return jsonify({"error": "Authentication required."}), 401
                return redirect(url_for("auth_view.login"))
            return view(*args, **kwargs)
        return guarded
    return decorate
