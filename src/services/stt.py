from groq import Groq
from io import BytesIO

class SpeechToText:
    def __init__(
            self,
            api_key,
            temperature=0,
            model="whisper-large-v3",
            response_format="verbose_json"
        ):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.response_format = response_format

    def transcribe(self, audio_input) -> str:
        if hasattr(audio_input, "read") and hasattr(audio_input, "filename"):
            data = audio_input.read()
            filename = getattr(audio_input, "filename", "audio.ogg")

        elif isinstance(audio_input, (bytes, bytearray)):
            data = bytes(audio_input)
            filename = "audio.ogg"

        elif hasattr(audio_input, "read"):
            data = audio_input.read()
            filename = getattr(audio_input, "name", "audio.ogg")
        else:
            raise ValueError("audio_input must be FileStorage, bytes or file-like")

        buf = BytesIO(data)
        buf.name = filename
        buf.seek(0)

        file_param = (filename, buf)

        response = self.client.audio.transcriptions.create(
            file=file_param,
            model=self.model,
            temperature=self.temperature,
            response_format=self.response_format,
            language="pt"
        )

        return getattr(response, "text", response if isinstance(response, str) else str(response))
