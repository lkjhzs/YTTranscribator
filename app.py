from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from io import BytesIO
from pathlib import Path
import tempfile
import os

from modules.downloader import YouTubeDownloader
from modules.transcriber import SpeechTranscriber
from modules.summarizer import TextSummarizer

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024  # 1GB

# Initialize heavy services lazily so the website opens immediately.
downloader = None
transcriber = None
summarizer = None


def get_services():
    global downloader, transcriber, summarizer
    if downloader is None:
        downloader = YouTubeDownloader()
    if transcriber is None:
        transcriber = SpeechTranscriber()
    if summarizer is None:
        summarizer = TextSummarizer()
    return downloader, transcriber, summarizer


def is_youtube_url(value: str) -> bool:
    lowered = value.lower()
    return "youtube.com" in lowered or "youtu.be" in lowered


def validate_extension(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    downloader_service, transcriber_service, summarizer_service = get_services()
    source_value = (request.form.get("source") or "").strip()
    uploaded = request.files.get("audio_file")

    if not source_value and (not uploaded or not uploaded.filename):
        return render_template(
            "index.html",
            error="Введіть YouTube-посилання або завантажте локальний файл.",
            source=source_value,
        )

    temp_file_path = None

    try:
        if source_value and is_youtube_url(source_value):
            audio_path = downloader_service.download_audio(source_value)
        elif uploaded and uploaded.filename:
            if not validate_extension(uploaded.filename):
                return render_template(
                    "index.html",
                    error="Підтримуються формати: .mp3, .wav, .m4a, .mp4",
                    source=source_value,
                )

            safe_name = secure_filename(uploaded.filename)
            suffix = Path(safe_name).suffix or ".mp4"

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir="output") as tmp:
                uploaded.save(tmp)
                temp_file_path = tmp.name

            audio_path = temp_file_path
        else:
            audio_path = source_value

        if not os.path.exists(audio_path):
            raise RuntimeError(f"Файл не знайдено: {audio_path}")

        full_text = transcriber_service.transcribe(audio_path)
        summary = summarizer_service.create_summary(full_text)

        return render_template(
            "index.html",
            source=source_value,
            full_text=full_text,
            summary=summary,
        )

    except Exception as exc:
        return render_template(
            "index.html",
            error=f"Виникла помилка: {exc}",
            source=source_value,
        )
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass


@app.route("/download-summary", methods=["POST"])
def download_summary():
    summary = (request.form.get("summary") or "").strip()
    if not summary:
        return render_template("index.html", error="Немає конспекту для збереження.")

    buffer = BytesIO(summary.encode("utf-8"))
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="summary.txt",
        mimetype="text/plain; charset=utf-8",
    )


if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    # Disable reloader so file changes in ./output do not restart the server mid-request.
    app.run(debug=True, use_reloader=False, threaded=True)
