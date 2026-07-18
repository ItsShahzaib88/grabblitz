"""
Core downloader module.
Wraps yt-dlp to extract media metadata.
"""
import yt_dlp
import traceback
import os
import tempfile
import re
import imageio_ffmpeg
from typing import Optional, Callable


def _sanitize_filename(name: str) -> str:
    """Remove characters that are unsafe for filenames."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name[:80].strip()


def get_format_ext(formats: list, format_id: str) -> str:
    """Look up the extension for a given format_id from the formats list."""
    for f in formats:
        if f.get("format_id") == format_id:
            return f.get("ext", "mp4")
    return "mp4"


def _format_size(filesize: Optional[int]) -> Optional[str]:
    """Convert bytes to human-readable string."""
    if filesize is None:
        return None
    if filesize < 1024:
        return f"{filesize} B"
    elif filesize < 1024 * 1024:
        return f"{filesize / 1024:.1f} KB"
    elif filesize < 1024 * 1024 * 1024:
        return f"{filesize / (1024 * 1024):.1f} MB"
    else:
        return f"{filesize / (1024 * 1024 * 1024):.2f} GB"


def _sanitize_filename(name: str) -> str:
    """Remove characters that are unsafe for filenames."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name[:80].strip()


def _process_format(f: dict) -> Optional[dict]:
    """Convert a raw yt-dlp format dict into our clean API format."""
    url = f.get("url")
    if not url:
        return None

    # Skip manifest-based streaming formats — yt-dlp handles these via download
    if f.get("protocol") in ("m3u8", "m3u8_native", "dash", "rtsp", "rtmp"):
        return None

    vcodec = f.get("vcodec", "none")
    acodec = f.get("acodec", "none")

    has_video = vcodec and vcodec != "none"
    has_audio = acodec and acodec != "none"

    if not has_video and not has_audio:
        return None

    resolution = f.get("resolution") or ""
    if not resolution:
        width = f.get("width")
        height = f.get("height")
        if width and height:
            resolution = f"{width}x{height}"
        elif has_video:
            resolution = "unknown"
        else:
            resolution = "audio only"

    filesize = f.get("filesize") or f.get("filesize_approx")

    return {
        "format_id": f.get("format_id", ""),
        "ext": f.get("ext", "").lower(),
        "resolution": resolution,
        "quality_label": f.get("format_note", resolution),
        "fps": f.get("fps"),
        "filesize": filesize,
        "filesize_hr": _format_size(filesize),
        "url": url,
        "has_video": has_video,
        "has_audio": has_audio,
        "vcodec": vcodec,
        "acodec": acodec,
        "tbr": f.get("tbr"),
        "abr": f.get("abr"),
        "vbr": f.get("vbr"),
    }


def extract_info(url: str) -> dict:
    """
    Extract all metadata and download formats from a URL.
    Returns a structured dict with title, thumbnail, formats, etc.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist",
        "ignoreerrors": False,
    }
    cookie_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cookies.txt")
    if os.path.exists(cookie_path):
        ydl_opts["cookiefile"] = cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            raw = ydl.extract_info(url, download=False)

            if not raw:
                raise ValueError("Could not extract info from this URL.")

            # Handle playlists
            is_playlist = "entries" in raw
            if is_playlist:
                playlist_title = raw.get("title", "Playlist")
                entries = list(raw.get("entries") or [])
                entries = [e for e in entries if e]
                if len(entries) == 1:
                    raw = entries[0]
                    is_playlist = False
                else:
                    playlist_items = []
                    for entry in entries[:50]:
                        playlist_items.append({
                            "id": entry.get("id", ""),
                            "title": entry.get("title", "Unknown"),
                            "url": entry.get("webpage_url", ""),
                            "thumbnail": entry.get("thumbnail", ""),
                            "duration": entry.get("duration"),
                        })
                    return {
                        "success": True,
                        "is_playlist": True,
                        "title": playlist_title,
                        "thumbnail": entries[0].get("thumbnail", "") if entries else "",
                        "playlist_count": len(entries),
                        "items": playlist_items,
                        "videos": [],
                        "audios": [],
                        "images": [],
                        "uploader": raw.get("uploader", raw.get("channel", "")),
                    }

            # --- Process single video/audio ---
            title = raw.get("title", "Unknown Title")
            description = raw.get("description", "")[:500] if raw.get("description") else ""
            uploader = raw.get("uploader") or raw.get("channel") or raw.get("creator") or ""
            uploader_url = raw.get("uploader_url") or raw.get("channel_url") or ""
            duration = raw.get("duration")
            view_count = raw.get("view_count")
            like_count = raw.get("like_count")
            upload_date = raw.get("upload_date", "")
            webpage_url = raw.get("webpage_url", url)

            # Thumbnail — prefer highest resolution
            thumbnail = ""
            thumbnails = raw.get("thumbnails") or []
            if thumbnails:
                try:
                    thumbnails_sorted = sorted(
                        thumbnails,
                        key=lambda t: (t.get("width") or 0) * (t.get("height") or 0),
                        reverse=True,
                    )
                    thumbnail = thumbnails_sorted[0].get("url", "")
                except Exception:
                    thumbnail = thumbnails[-1].get("url", "") if thumbnails else ""
            if not thumbnail:
                thumbnail = raw.get("thumbnail", "")

            # All available thumbnails for download
            thumbnail_list = []
            for t in thumbnails:
                t_url = t.get("url", "")
                if t_url:
                    thumbnail_list.append({
                        "url": t_url,
                        "width": t.get("width"),
                        "height": t.get("height"),
                        "resolution": f"{t.get('width', '?')}x{t.get('height', '?')}",
                    })

            # Process download formats
            raw_formats = raw.get("formats") or []
            videos = []
            audios = []

            for f in raw_formats:
                processed = _process_format(f)
                if not processed:
                    continue
                
                if processed["has_video"]:
                    videos.append(processed)
                else:
                    audios.append(processed)

            def sort_key(f):
                res = f.get("resolution", "")
                try:
                    parts = res.lower().replace("x", "p").split("p")
                    return int(parts[-2]) if len(parts) >= 2 else int(parts[0])
                except Exception:
                    return 0

            videos.sort(key=sort_key, reverse=True)
            audios.sort(key=lambda f: f.get("abr") or 0, reverse=True)

            # Remove duplicate resolutions (keep best quality per resolution)
            seen_resolutions = set()
            unique_videos = []
            for v in videos:
                res = v.get("resolution", "")
                if res not in seen_resolutions:
                    seen_resolutions.add(res)
                    unique_videos.append(v)

            return {
                "success": True,
                "is_playlist": False,
                "title": title,
                "description": description,
                "thumbnail": thumbnail,
                "thumbnails": thumbnail_list[:10],
                "duration": duration,
                "uploader": uploader,
                "uploader_url": uploader_url,
                "view_count": view_count,
                "like_count": like_count,
                "upload_date": upload_date,
                "webpage_url": webpage_url,
                "videos": unique_videos,
                "audios": audios,
                "images": [],
            }

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if "Unsupported URL" in error_msg:
            raise ValueError("This URL is not supported. Please try a different link.")
        elif "Private video" in error_msg:
            raise ValueError("This content is private and cannot be downloaded.")
        elif "age" in error_msg.lower():
            raise ValueError("This content is age-restricted and cannot be downloaded.")
        else:
            raise ValueError(f"Could not process this URL: {error_msg[:200]}")
    except Exception as e:
        traceback.print_exc()
        raise ValueError(f"An unexpected error occurred: {str(e)[:200]}")


def download_to_file(source_url: str, format_id: str, title: str = "download", ext: str = "mp4", has_audio: bool = False, progress_hook: Optional[Callable] = None) -> tuple[str, str]:
    """
    Download media using yt-dlp directly to a temp file on disk.
    Returns (filepath, ext).
    
    This is the RELIABLE approach — yt-dlp handles all auth headers,
    cookies, format merging, and retries automatically.
    """
    tmpdir = tempfile.mkdtemp(prefix="saveflow_")
    safe_title = _sanitize_filename(title) or "download"
    output_template = os.path.join(tmpdir, f"{safe_title}.%(ext)s")

    is_audio = ext.lower() in ["mp3", "m4a", "ogg", "opus", "flac", "wav"]
    actual_format = format_id if (is_audio or has_audio) else f"{format_id}+bestaudio/best"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": output_template,
        "format": actual_format,
        "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
        # No timeout — let it download as long as it needs
        "retries": 5,
        "fragment_retries": 5,
        "ignoreerrors": False,
        # Merge separate video+audio streams if ffmpeg is available
        "merge_output_format": "mp4" if not is_audio else None,
        # Embed metadata
        "writethumbnail": False,
    }
    
    cookie_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cookies.txt")
    if os.path.exists(cookie_path):
        ydl_opts["cookiefile"] = cookie_path
    
    if progress_hook:
        ydl_opts["progress_hooks"] = [progress_hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source_url, download=True)
            # Find the downloaded file in tmpdir
            for fname in os.listdir(tmpdir):
                fpath = os.path.join(tmpdir, fname)
                if os.path.isfile(fpath):
                    ext = os.path.splitext(fname)[1].lstrip(".")
                    return fpath, ext
            raise ValueError("Download completed but output file not found.")
    except Exception as e:
        # Cleanup tmp dir on failure
        import shutil
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass
        raise ValueError(f"Download failed: {str(e)[:300]}")
