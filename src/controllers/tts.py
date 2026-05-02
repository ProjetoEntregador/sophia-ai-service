from flask import Blueprint, current_app, request, jsonify, send_file
import io

bp = Blueprint('tts', __name__, url_prefix='/tts')

@bp.route('/synthesize', methods=['POST'])
def synthesize():
    data = request.get_json(silent=True) or {}
    text = data.get('text', '').strip()
    if not text:
        return jsonify({"error": "text is required"}), 400
    audio_bytes = current_app.tts.synthesize(text)
    if not audio_bytes:
        return jsonify({"error": "no audio produced"}), 500
    buf = io.BytesIO(audio_bytes)
    buf.seek(0)
    return send_file(buf, mimetype='audio/ogg', as_attachment=False)