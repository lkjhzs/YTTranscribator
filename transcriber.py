import re

import whisper

try:
    from .context_corrector import ContextTextCorrector
except ImportError:
    from context_corrector import ContextTextCorrector


class SpeechTranscriber:
    def __init__(self, model_size="small"):
        """Load Whisper model and optional AI context corrector."""
        print("Загрузка модели Whisper...")
        self.model = whisper.load_model(model_size)
        self.context_corrector = ContextTextCorrector()
        print("Модель загружено!")

    def transcribe(self, audio_path):
        """Convert audio to text."""
        try:
            print(f"Начинаем транскрипцию файла: {audio_path}")

            result = self.model.transcribe(
                audio_path,
                language=None,
                task="transcribe",
                verbose=True,
            )

            full_text = result["text"].strip()

            # Step 1: deterministic user dictionary corrections.
            full_text = self.apply_user_corrections(full_text)
            # Step 2: optional LLM-based contextual correction.
            full_text = self.context_corrector.correct_text(full_text)

            print(f"Транскрипция завершена. Язык: {result['language']}")
            print(f"Длина текста: {len(full_text)} символов")
            return full_text

        except Exception as e:
            raise Exception(f"Ошибка при транскрипции: {e}")

    def apply_user_corrections(self, text):
        """Apply fixed term replacements."""
        corrections = {
            "звід": "звіт",
            "подивати": "подавати",
            "третьій": "третій",
            "фоб": "ФОП",
            "FOP": "ФОП",
            "мати муть": "матимуть",
            "шлюп": "шлюб",
            "у Горщина": "Угорщина",
            "у Горщини": "Угорщини",
            "Горщини": "Угорщини",
        }

        fixed_text = text
        for wrong, correct in corrections.items():
            pattern = r"\b" + re.escape(wrong) + r"\b"
            fixed_text = re.sub(pattern, correct, fixed_text, flags=re.IGNORECASE)

        return fixed_text.strip()
