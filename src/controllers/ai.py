from flask import Blueprint, jsonify

bp = Blueprint("ai", __name__, url_prefix="/ai")

@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200
