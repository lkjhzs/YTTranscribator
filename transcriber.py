import os
import re
import shutil
import subprocess
import tempfile

import whisper
import torch

try:
    from .context_corrector import ContextTextCorrector
except ImportError:
    from context_corrector import ContextTextCorrector


class SpeechTranscriber:
    def __init__(self, model_size=None, accuracy_mode="fast"):
        """Load Whisper model and optional AI context corrector."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        model_size = model_size or os.getenv("WHISPER_MODEL_SIZE") or self.default_model_size()
        print(f"Завантаження моделі Whisper ({model_size})...")
        self.model = self.load_model(model_size).to(self.device)
        self.context_corrector = ContextTextCorrector()
        self.ffmpeg_path = self._find_ffmpeg()
        self.accuracy_mode = accuracy_mode
        print("Модель завантажено!")

    def default_model_size(self):
        return "medium" if self.device == "cuda" else "small"

    def load_model(self, model_size):
        try:
            return whisper.load_model(model_size)
        except Exception:
            if model_size == "small":
                raise
            print(f"Не вдалося завантажити Whisper {model_size}, пробую small...")
            return whisper.load_model("small")

    def transcribe(self, audio_path):
        """Convert audio to text."""
        prepared_audio_path = None

        try:
            print(f"Починаємо транскрипцію файлу: {audio_path}")
            prepared_audio_path = self.prepare_audio(audio_path)

            result = self.model.transcribe(
                prepared_audio_path,
                language=None,
                task="transcribe",
                verbose=False,
                fp16=self.device == "cuda",
                **self.decoding_options(),
                condition_on_previous_text=False,
                compression_ratio_threshold=2.4,
                logprob_threshold=-1.0,
                no_speech_threshold=0.6,
                initial_prompt=self.initial_prompt(),
            )

            full_text = result["text"].strip()

            # Step 1: deterministic user dictionary corrections.
            full_text = self.apply_user_corrections(full_text)
            # Step 2: optional LLM-based contextual correction.
            full_text = self.context_corrector.correct_text(full_text)

            print(f"Транскрипція завершена. Мова: {result['language']}")
            print(f"Довжина тексту: {len(full_text)} символів")
            return full_text

        except Exception as exc:
            raise Exception(f"Помилка при транскрипції: {exc}")
        finally:
            if prepared_audio_path and prepared_audio_path != audio_path:
                try:
                    os.remove(prepared_audio_path)
                except OSError:
                    pass

    def prepare_audio(self, audio_path):
        """Create a normalized mono WAV copy for more stable recognition."""
        if not self.ffmpeg_path:
            return audio_path

        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir="output")
        normalized_path = handle.name
        handle.close()

        command = [
            self.ffmpeg_path,
            "-y",
            "-i",
            audio_path,
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
        ]

        if os.getenv("ENABLE_AUDIO_FILTERS", "0") == "1":
            command.extend(["-af", "highpass=f=80,lowpass=f=8000,loudnorm=I=-18:TP=-1.5:LRA=11"])

        command.append(normalized_path)

        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return normalized_path
        except Exception as exc:
            print(f"Не вдалося нормалізувати аудіо, використовую оригінал: {exc}")
            try:
                os.remove(normalized_path)
            except OSError:
                pass
            return audio_path

    def _find_ffmpeg(self):
        bundled_ffmpeg = r"C:\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe"
        if os.path.exists(bundled_ffmpeg):
            return bundled_ffmpeg
        return shutil.which("ffmpeg")

    def decoding_options(self):
        if self.accuracy_mode == "accurate":
            return {
                "beam_size": int(os.getenv("WHISPER_BEAM_SIZE", "3")),
                "temperature": (0.0, 0.2),
            }

        if self.accuracy_mode == "balanced":
            return {
                "temperature": (0.0, 0.2),
            }

        return {
            "temperature": 0.0,
        }

    @staticmethod
    def settings_for_quality(quality):
        quality = (quality or "balanced").lower()

        if quality == "fast":
            return {
                "model_size": "base",
                "accuracy_mode": "fast",
            }

        if quality == "accurate":
            return {
                "model_size": "medium",
                "accuracy_mode": "accurate",
            }

        return {
            "model_size": "small",
            "accuracy_mode": "balanced",
        }

    def initial_prompt(self):
        return (
            "Це транскрипція українського або російського YouTube-відео. "
            "Зберігай імена, назви, терміни та абревіатури точно: ФОП, ЄС, НАТО, США, "
            "Україна, Росія, Угорщина, податки, звіт, третя група, квартал. "
            "Не перекладай текст, лише розпізнавай мовлення."
        )

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
            "україни": "України",
            "холоднокромний": "холоднокровний",
        }

        fixed_text = text
        for wrong, correct in corrections.items():
            pattern = r"\b" + re.escape(wrong) + r"\b"
            fixed_text = re.sub(pattern, correct, fixed_text, flags=re.IGNORECASE)

        return fixed_text.strip()
