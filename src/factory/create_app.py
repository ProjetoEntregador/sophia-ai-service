import os
from flask import Flask

from src.controllers.ai import bp as ai_bp
from src.controllers.tts import bp as tts_bp
from src.controllers.stt import bp as stt_bp
from src.controllers.ocr import bp as ocr_bp
from src.services.tts import TextToSpeech
from src.services.stt import SpeechToText
from src.services.ocr import OCRService

def create_app():
    app = Flask(__name__)
    app.tts = TextToSpeech(api_key=os.environ.get("TTS_API_KEY"))
    app.stt = SpeechToText(api_key=os.environ.get("STT_API_KEY"))
    app.ocr = OCRService(api_key=os.environ.get("OCR_API_KEY"))

    app.register_blueprint(tts_bp)
    app.register_blueprint(stt_bp)
    app.register_blueprint(ocr_bp)
    app.register_blueprint(ai_bp)
    return app
