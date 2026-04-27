# YouTube Video Summarizer (Web)

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open: http://127.0.0.1:5000

## Features

- YouTube URL analysis
- Local audio/video file analysis (`.mp3`, `.wav`, `.m4a`, `.mp4`)
- Full transcript display
- Optional AI contextual transcript correction (LLM)
- Summary generation
- Summary download as `.txt`


```powershell
$env:OPENAI_API_KEY="your_api_key"
$env:AI_CORRECTION_MODEL="gpt-4o-mini"   # optional
$env:ENABLE_AI_CORRECTION="1"            # 0 to disable
```
