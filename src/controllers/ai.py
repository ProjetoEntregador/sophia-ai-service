from flask import Blueprint, current_app, request, jsonify, send_file
import io

bp = Blueprint("ai", __name__, url_prefix="/ai")

@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@bp.route("/orchestrate/transcribe-and-say", methods=["POST"])
def transcribe_and_say():
    if "file" not in request.files:
        return jsonify({"error": "file required"}), 400
    audio = request.files["file"].read()
    text = current_app.stt.transcribe(audio)

    audio_bytes = current_app.tts.synthesize(f"Você disse: {text}")
    if not audio_bytes:
        return jsonify({"error": "tts failed"}), 500
    buf = io.BytesIO(audio_bytes)
    buf.seek(0)
    return send_file(buf, mimetype="audio/wav")