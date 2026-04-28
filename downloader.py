import os
import re
import html
import urllib.request

import yt_dlp


class YouTubeDownloader:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        bundled_ffmpeg_dir = r"C:\ffmpeg-8.0.1-essentials_build\bin"
        self.ffmpeg_location = bundled_ffmpeg_dir if os.path.exists(bundled_ffmpeg_dir) else None

    def download_audio(self, url):
        """Download the best available audio stream and convert it to WAV."""
        ydl_opts = self._base_ytdlp_options()
        ydl_opts.update({
            "format": "bestaudio/best",
            "outtmpl": os.path.join(self.output_dir, "audio_%(id)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "0",
                }
            ],
        })

        if self.ffmpeg_location:
            ydl_opts["ffmpeg_location"] = self.ffmpeg_location

        try:
            print(f"Починаємо завантаження: {url}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                audio_path = self._resolve_downloaded_audio_path(ydl, info)

            file_size = os.path.getsize(audio_path)
            print(f"Аудіо завантажено: {audio_path}")
            print(f"Розмір: {file_size} байт")

            if file_size < 1024:
                raise Exception(f"Файл занадто маленький: {file_size} байт")

            return audio_path

        except Exception as exc:
            clean_error = self._clean_ytdlp_error(exc)
            print(f"Помилка в download_audio: {clean_error}")
            raise Exception(f"Помилка при завантаженні: {clean_error}")

    def get_subtitles_text(self, url):
        """Return YouTube subtitles/auto-captions text when available."""
        ydl_opts = self._base_ytdlp_options()
        ydl_opts.update({
            "quiet": True,
            "skip_download": True,
        })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as exc:
            clean_error = self._clean_ytdlp_error(exc)
            print(f"Не вдалося отримати інформацію про YouTube-відео: {clean_error}")
            return ""

        try:
            track = self._select_caption_track(info)
            if not track:
                return ""

            with urllib.request.urlopen(track["url"], timeout=20) as response:
                subtitle_data = response.read().decode("utf-8", errors="ignore")

            text = self._vtt_to_text(subtitle_data)
            if text:
                print("Знайдено субтитри YouTube, Whisper не потрібен.")
            return text

        except Exception as exc:
            print(f"Не вдалося отримати субтитри YouTube: {self._clean_ytdlp_error(exc)}")
            return ""

    def _select_caption_track(self, info):
        captions = {}
        captions.update(info.get("subtitles") or {})
        captions.update(info.get("automatic_captions") or {})

        if not captions:
            return None

        language_priority = ("uk", "uk-UA", "ru", "ru-RU", "en", "en-US", "en-GB")
        ordered_languages = []

        for preferred in language_priority:
            ordered_languages.extend(
                language for language in captions if language == preferred or language.startswith(f"{preferred}-")
            )

        ordered_languages.extend(language for language in captions if language not in ordered_languages)

        for language in ordered_languages:
            tracks = captions.get(language) or []
            for track in tracks:
                if track.get("ext") == "vtt" and track.get("url"):
                    return track

        return None

    def _vtt_to_text(self, subtitle_data):
        lines = []
        previous = ""

        for raw_line in subtitle_data.splitlines():
            line = raw_line.strip()

            if (
                not line
                or line == "WEBVTT"
                or line.startswith("Kind:")
                or line.startswith("Language:")
                or "-->" in line
                or re.fullmatch(r"\d+", line)
            ):
                continue

            line = html.unescape(line)
            line = re.sub(r"<[^>]+>", "", line)
            line = re.sub(r"(^|\s)(>{1,2}\s*)+", " ", line)
            line = re.sub(r"\s+", " ", line).strip()

            if line and line != previous:
                lines.append(line)
                previous = line

        return " ".join(lines).strip()

    def _clean_ytdlp_error(self, error):
        message = str(error)
        message = re.sub(r"\x1b\[[0-9;]*m", "", message)
        message = re.sub(r"\s+", " ", message).strip()
        message = re.sub(r"^ERROR:\s*", "", message, flags=re.IGNORECASE)

        if self._is_unavailable_video_error(message):
            return (
                "yt-dlp не зміг отримати це YouTube-відео. Якщо воно відкривається у браузері, "
                "найчастіше допомагає оновити yt-dlp або передати cookies браузера."
            )

        return message

    def _base_ytdlp_options(self):
        options = {
            "quiet": False,
            "no_warnings": False,
            "no_color": True,
            "geo_bypass": True,
            "socket_timeout": 30,
            "retries": 3,
            "fragment_retries": 3,
            "extractor_args": {
                "youtube": {
                    "player_client": ["web", "android", "ios"],
                }
            },
        }

        cookies_file = os.getenv("YTDLP_COOKIES_FILE", "").strip()
        if cookies_file:
            options["cookiefile"] = cookies_file

        cookies_browser = os.getenv("YTDLP_COOKIES_FROM_BROWSER", "").strip()
        if cookies_browser:
            options["cookiesfrombrowser"] = (cookies_browser,)

        return options

    def _is_unavailable_video_error(self, message):
        lowered = message.lower()
        unavailable_markers = (
            "video is not available",
            "private video",
            "video unavailable",
            "this video is unavailable",
            "has been removed",
        )
        return any(marker in lowered for marker in unavailable_markers)

    def _resolve_downloaded_audio_path(self, ydl, info):
        base_path = ydl.prepare_filename(info)
        root, _ = os.path.splitext(base_path)
        wav_path = root + ".wav"

        if os.path.exists(wav_path):
            return wav_path

        if os.path.exists(base_path):
            return base_path

        video_id = info.get("id")
        if video_id:
            for filename in os.listdir(self.output_dir):
                if filename.startswith(f"audio_{video_id}."):
                    return os.path.join(self.output_dir, filename)

        raise Exception("Не вдалося знайти завантажене аудіо")
