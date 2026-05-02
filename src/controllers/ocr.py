from flask import Blueprint, current_app, request, jsonify

bp = Blueprint('ocr', __name__, url_prefix='/ocr')

@bp.route('/read', methods=['POST'])
def read():
    if 'file' not in request.files:
        return jsonify({"error": "image file is required"}), 400
    file = request.files['file']

    try:
        raw = current_app.ocr.read_text(file)
        parsed = current_app.ocr.parse_model_output(raw)
    except Exception as e:
        current_app.logger.exception("OCR failed")
        return jsonify({"error": "ocr failed", "detail": str(e)}), 500

    return jsonify(parsed), 200