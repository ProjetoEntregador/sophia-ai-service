from groq import Groq
from io import BytesIO
from pydub import AudioSegment

class TextToSpeech:
    def __init__(
            self,
            speed=1.5,
            voice="hannah",
            api_key=None,
            response_format="wav",
            model="canopylabs/orpheus-v1-english",
            output_format="ogg",
        ):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.speed = speed
        self.voice = voice
        self.output_format = output_format
        self.response_format = response_format

    def synthesize(self, text) -> bytes:
        response = self.client.audio.speech.create(
            input=text,
            model=self.model,
            speed=self.speed,
            voice=self.voice,
            response_format=self.response_format
        )
        response.write_to_file("output.wav")
        wav_buffer = BytesIO(response.read())
        audio = AudioSegment.from_file(wav_buffer, format="wav")
        ogg_buffer = BytesIO()
        audio.export(ogg_buffer, format=self.output_format, codec="libopus")
        ogg_buffer.seek(0)
        return ogg_buffer.getvalue()
