from flask import Blueprint, current_app, request, jsonify

bp = Blueprint('stt', __name__, url_prefix='/stt')

@bp.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({"error": "file is required"}), 400
    f = request.files['file']
    try:
        text = current_app.stt.transcribe(f)
    except Exception as e:
        current_app.logger.exception("STT failed")
        return jsonify({"error": "transcribe failed", "detail": str(e)}), 500
    return jsonify({"text": text}), 200