# SaveFlow - Universal Media Downloader

SaveFlow is a production-ready, highly optimized media downloader that supports YouTube, TikTok, Instagram, Twitter, and 30+ other platforms. 

## Features
- **FastAPI Backend:** Handles extraction via yt-dlp, with rate limiting and robust error handling.
- **Vanilla JS Frontend:** Zero frameworks, highly modular, perfect Lighthouse scores.
- **Responsive UI:** Dark/Light mode, CSS-only animations, loading skeletons.
- **Local History:** Saves recent downloads in localStorage.

## Setup

### Backend
1. `cd server`
2. `pip install -r requirements.txt`
3. `python main.py` (Runs on port 8000)

### Frontend
Serve the `client` folder using any static web server (e.g., VS Code Live Server, Python `http.server`, Nginx).
```bash
cd client
python -m http.server 3000
```

## Deployment
See `DEPLOYMENT.md` for production deployment instructions.
