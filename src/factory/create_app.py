import os
from flask import Flask

from src.controllers.ai import bp as ai_bp
from src.controllers.stt import bp as stt_bp
from src.controllers.ocr import bp as ocr_bp
from src.controllers.chat import bp as chat_bp
from src.ai import AIClientFactory
from src.services.stt import SpeechToText
from src.services.ocr import OCRService
from src.services.chat import ChatService

def create_app():
    app = Flask(__name__)

    ai = AIClientFactory()
    app.stt = SpeechToText(client=ai.groq_client(os.environ.get("STT_API_KEY")))
    app.ocr = OCRService(client=ai.groq_client(os.environ.get("OCR_API_KEY")))
    app.chat = ChatService(ai.build_chat_providers())

    app.register_blueprint(stt_bp)
    app.register_blueprint(ocr_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(ai_bp)
    return app
