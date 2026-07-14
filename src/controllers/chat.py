from flask import Blueprint, current_app, request, jsonify

bp = Blueprint('chat', __name__, url_prefix='/chat')

@bp.route('/completions', methods=['POST'])
def completions():
    data = request.get_json(silent=True) or {}
    messages = data.get('messages')

    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "messages is required"}), 400

    payload = {
        "systemPrompt": data.get("systemPrompt") or "",
        "messages": messages,
        "tools": data.get("tools") or [],
    }

    try:
        response = current_app.chat.chat(payload)
    except Exception as e:
        current_app.logger.exception("Chat failed")
        return jsonify({"error": "chat failed", "detail": str(e)}), 500

    return jsonify(response), 200
