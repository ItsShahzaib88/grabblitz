"""
API Routes for SaveFlow
Defines all REST endpoints.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import sys
import os
import uuid
import shlex
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from api.downloader import extract_info, get_format_ext, download_to_file
from utils.platform_detect import detect_platform, get_all_platforms
from utils.rate_limiter import rate_limiter
from utils.sanitizer import sanitize_url

router = APIRouter()


# --- Request / Response Models ---

class InfoRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    format_id: str
    title: str = "download"
    ext: str = "mp4"
    has_audio: bool = False

# --- Global Task Store ---
download_tasks = {}

def update_download_progress(task_id: str, d: dict):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded = d.get('downloaded_bytes', 0)
        speed = d.get('speed', 0)
        
        download_tasks[task_id]["loaded"] = downloaded
        if total > 0:
            download_tasks[task_id]["total"] = total
        if speed is not None:
            download_tasks[task_id]["speed"] = speed

def run_background_download(task_id: str, url: str, format_id: str, title: str, ext: str, has_audio: bool):
    try:
        download_tasks[task_id]["status"] = "downloading"
        
        def progress_hook(d):
            update_download_progress(task_id, d)
            
        fpath, final_ext = download_to_file(url, format_id, title, ext, has_audio, progress_hook)
        
        download_tasks[task_id]["status"] = "completed"
        download_tasks[task_id]["filepath"] = fpath
        download_tasks[task_id]["ext"] = final_ext
    except Exception as e:
        download_tasks[task_id]["status"] = "error"
        download_tasks[task_id]["error_msg"] = str(e)


# --- Helper: Get Client IP ---

def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# --- Endpoints ---

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "SaveFlow API"}


@router.get("/platforms")
async def get_platforms():
    platforms = get_all_platforms()
    safe_platforms = [
        {
            "id": p["id"],
            "name": p["name"],
            "color": p["color"],
            "types": p["types"],
            "icon": p["icon"],
            "note": p.get("note", ""),
        }
        for p in platforms
    ]
    return {"success": True, "platforms": safe_platforms}


@router.post("/info")
async def get_media_info(request: Request, body: InfoRequest):
    """Extract media metadata. Rate-limited to 10 req/min per IP."""
    client_ip = get_client_ip(request)

    if not rate_limiter.is_allowed(client_ip):
        retry_after = rate_limiter.get_retry_after(client_ip)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Too many requests. Please wait {retry_after} seconds.",
                "retry_after": retry_after,
            },
        )

    is_valid, result = sanitize_url(body.url)
    if not is_valid:
        raise HTTPException(status_code=400, detail={"error": "invalid_url", "message": result})

    clean_url = result
    platform = detect_platform(clean_url)

    try:
        info = await run_in_threadpool(extract_info, clean_url)
        info["platform"] = {
            "id": platform["id"],
            "name": platform["name"],
            "color": platform["color"],
            "icon": platform["icon"],
        }
        return JSONResponse(content=info)
    except ValueError as e:
        raise HTTPException(status_code=422, detail={"error": "extraction_failed", "message": str(e)})
    except Exception:
        raise HTTPException(status_code=500, detail={"error": "server_error", "message": "Internal server error."})


@router.post("/download")
async def start_download(request: Request, body: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Start a download on the server and return a task_id for polling progress.
    """
    is_valid, result = sanitize_url(body.url)
    if not is_valid:
        raise HTTPException(status_code=400, detail={"error": "invalid_url", "message": result})

    task_id = str(uuid.uuid4())
    download_tasks[task_id] = {
        "status": "starting",
        "loaded": 0,
        "total": 0,
        "speed": 0,
        "filepath": None,
        "error_msg": None,
        "ext": body.ext or "mp4",
        "title": body.title or "download"
    }
    
    background_tasks.add_task(
        run_background_download,
        task_id=task_id,
        url=result,
        format_id=body.format_id,
        title=body.title or "download",
        ext=body.ext or "mp4",
        has_audio=body.has_audio
    )
    
    return {"success": True, "task_id": task_id}


@router.get("/progress/{task_id}")
async def get_progress(task_id: str):
    """Poll for download progress on the server."""
    if task_id not in download_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return download_tasks[task_id]


@router.get("/serve/{task_id}")
async def serve_file(task_id: str, background_tasks: BackgroundTasks):
    """Serve the downloaded file and delete it from the server."""
    if task_id not in download_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task = download_tasks[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="File not ready")
        
    filepath = task["filepath"]
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File missing")
        
    safe_title = task["title"].replace('"', "'").replace('\n', '').replace('\r', '')
    filename = f"{safe_title}.{task['ext']}"
    
    def cleanup():
        try:
            os.remove(filepath)
            os.rmdir(os.path.dirname(filepath))
        except:
            pass
        if task_id in download_tasks:
            del download_tasks[task_id]
            
    background_tasks.add_task(cleanup)
    
    return FileResponse(
        path=filepath, 
        filename=filename, 
        media_type="application/octet-stream"
    )
