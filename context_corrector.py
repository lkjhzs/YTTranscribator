import os


class ContextTextCorrector:
    def __init__(self):
        self.enabled = os.getenv("ENABLE_AI_CORRECTION", "1") == "1"
        self.model = os.getenv("AI_CORRECTION_MODEL", "gpt-4o-mini")
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self._client = None
        self._available = False

        if not self.enabled:
            print("AI correction is disabled by ENABLE_AI_CORRECTION=0")
            return

        if not self.api_key:
            print("OPENAI_API_KEY is not set. AI correction is skipped.")
            return

        try:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key)
            self._available = True
            print(f"AI correction enabled (model: {self.model})")
        except Exception as exc:
            print(f"AI correction client init failed: {exc}")

    def correct_text(self, text):
        if not text or len(text.strip()) < 20:
            return text

        if not self._available or not self._client:
            return text

        try:
            prompt = (
                "You are a transcription proofreader.\n"
                "Fix recognition mistakes using context.\n"
                "Do not summarize and do not change meaning.\n"
                "Keep the same language as input.\n"
                "Return only corrected text."
            )

            response = self._client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.1,
            )

            corrected = (response.output_text or "").strip()
            if corrected:
                print("AI correction applied successfully.")
                return corrected

            return text
        except Exception as exc:
            print(f"AI correction failed, using original transcript: {exc}")
            return text
