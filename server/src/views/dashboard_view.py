from bson import ObjectId
from flask import Blueprint, Response, g, jsonify

from models.url_model import UrlModel
from utils.jwt_auth import login_required
from utils.realtime import notify_links_changed


dashboard_blueprint = Blueprint("dashboard_view", __name__, url_prefix="/api/links")


@dashboard_blueprint.get("")
@login_required()
def stat():
    return jsonify([{
        "id": str(link.id), "shortUrl": link.short_url,
        "fullUrl": link.full_url, "visits": link.enters,
    } for link in UrlModel.objects(user=g.current_user.id)])


@dashboard_blueprint.delete("/<url_id>")
@login_required()
def delete_url(url_id):
    if not ObjectId.is_valid(url_id):
        return jsonify(error="Link not found."), 404
    if not UrlModel.objects(id=url_id, user=g.current_user.id).delete():
        return jsonify(error="Link not found."), 404
    notify_links_changed(g.current_user.id)
    return Response(status=204)
