# SaveFlow Deployment Guide

## Production Requirements

- Python 3.9+
- Node.js (Optional, for building/minifying if added later)
- Reverse Proxy (Nginx/Caddy)
- SSL Certificate

## 1. Backend Deployment (FastAPI)

We recommend using `gunicorn` with `uvicorn` workers for production.

```bash
cd server
pip install -r requirements.txt
pip install gunicorn

# Start Gunicorn server
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
```

## 2. Frontend Deployment

The frontend is completely static (HTML, CSS, Vanilla JS) with zero build steps.
Simply serve the `client/` folder using Nginx, Apache, or a CDN.

## 3. Nginx Configuration

```nginx
server {
    listen 80;
    server_name saveflow.com;

    # Serve static frontend
    location / {
        root /path/to/universal-downloader/client;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```
