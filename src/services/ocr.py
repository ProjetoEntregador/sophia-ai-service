import json
import re
import base64
from groq import Groq
from ..prompts import get_ocr_prompt

class OCRService:
    def __init__(
            self,
            api_key,
            model="meta-llama/llama-4-scout-17b-16e-instruct"
        ):
        self.client = Groq(api_key=api_key)
        self.model = model

    @staticmethod
    def encode_image(image_file) -> str:
        image_bytes = image_file.read()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        return base64_image
    
    def _strip_fences(self, text: str) -> str:
        if not isinstance(text, str):
            return text
        cleaned = text.strip()
        if cleaned.startswith("```") and cleaned.endswith("```"):
            cleaned = "\n".join(cleaned.splitlines()[1:-1]).strip()
        return cleaned.strip("`").strip()

    def _try_load_json(self, text: str):
        try:
            return json.loads(text)
        except Exception:
            return None

    def _try_load_unescaped_json(self, text: str):
        try:
            unescaped = bytes(text, "utf-8").decode("unicode_escape")
            return json.loads(unescaped)
        except Exception:
            return None

    def _extract_json_candidate(self, text: str):
        match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
        return match.group(1).strip() if match else None

    def _coerce_to_parsed(self, raw):
        if isinstance(raw, dict):
            return raw

        if not isinstance(raw, str):
            try:
                return json.loads(str(raw))
            except Exception:
                return None

        raw_text = raw
        cleaned_text = self._strip_fences(raw_text)

        parsed = self._try_load_json(cleaned_text)
        if parsed is not None:
            return parsed

        cand = self._extract_json_candidate(cleaned_text)
        if cand:
            parsed = self._try_load_json(cand) or self._try_load_unescaped_json(cand)
            if parsed is not None:
                return parsed

        once_parsed = self._try_load_json(cleaned_text)
        if isinstance(once_parsed, str):
            parsed_obj = self._try_load_json(once_parsed) or self._try_load_unescaped_json(once_parsed)
            if parsed_obj is not None:
                return parsed_obj
        elif isinstance(once_parsed, (dict, list)):
            return once_parsed

        return None

    def parse_model_output(self, raw) -> dict:
        parsed = self._coerce_to_parsed(raw)
        if parsed is None:
            return {"error": "parse_failed", "raw": raw}

        if isinstance(parsed, dict) and "medications" in parsed:
            return parsed
        if isinstance(parsed, list):
            return {"medications": parsed}
        return parsed

    def read_text(self, file) -> str:
        base64_image = self.encode_image(file)
        prompt = get_ocr_prompt()

        system_msg = {
            "role": "system",
            "content": [
                {"type": "text", "text":
                    "You are a strict JSON generator for medication extraction. "
                    "Return ONLY a single JSON object with a top-level key 'medications' (list). "
                    "Do NOT repeat medication entries. If two entries have the same medication_name, dosage and form, keep only one. "
                    "Do not include any extra text, commentary or code fences."
                }
            ],
        }

        user_msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                    },
                },
            ],
        }

        chat_completion = self.client.chat.completions.create(
            messages=[system_msg, user_msg],
            model=self.model,
            temperature=0
        )
        return chat_completion.choices[0].message.content
