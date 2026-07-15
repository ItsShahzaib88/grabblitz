"""
Platform Detection Utility
Identifies media platform from URL and returns metadata.
"""
import re
from typing import Optional

# --- Platform Registry ---
# Each entry: (pattern, platform_id, display_name, color, icon_class, supported_types)
PLATFORMS = [
    {
        "id": "youtube",
        "name": "YouTube",
        "color": "#FF0000",
        "patterns": [
            r"(?:youtube\.com|youtu\.be)",
        ],
        "types": ["video", "audio", "thumbnail", "shorts", "playlist"],
        "icon": "youtube",
    },
    {
        "id": "youtube_music",
        "name": "YouTube Music",
        "color": "#FF0000",
        "patterns": [r"music\.youtube\.com"],
        "types": ["audio", "video"],
        "icon": "youtube-music",
    },
    {
        "id": "tiktok",
        "name": "TikTok",
        "color": "#010101",
        "patterns": [r"tiktok\.com", r"vm\.tiktok\.com"],
        "types": ["video", "audio", "thumbnail"],
        "icon": "tiktok",
    },
    {
        "id": "instagram",
        "name": "Instagram",
        "color": "#E1306C",
        "patterns": [r"instagram\.com", r"instagr\.am"],
        "types": ["video", "image", "reels", "stories", "thumbnail"],
        "icon": "instagram",
    },
    {
        "id": "facebook",
        "name": "Facebook",
        "color": "#1877F2",
        "patterns": [r"facebook\.com", r"fb\.watch", r"fb\.com"],
        "types": ["video", "audio", "thumbnail"],
        "icon": "facebook",
    },
    {
        "id": "twitter",
        "name": "X (Twitter)",
        "color": "#000000",
        "patterns": [r"twitter\.com", r"x\.com"],
        "types": ["video", "image", "audio", "thumbnail"],
        "icon": "twitter",
    },
    {
        "id": "threads",
        "name": "Threads",
        "color": "#000000",
        "patterns": [r"threads\.net"],
        "types": ["video", "image"],
        "icon": "threads",
    },
    {
        "id": "pinterest",
        "name": "Pinterest",
        "color": "#E60023",
        "patterns": [r"pinterest\.com", r"pin\.it"],
        "types": ["video", "image", "thumbnail"],
        "icon": "pinterest",
    },
    {
        "id": "snapchat",
        "name": "Snapchat",
        "color": "#FFFC00",
        "patterns": [r"snapchat\.com"],
        "types": ["video", "image"],
        "icon": "snapchat",
    },
    {
        "id": "soundcloud",
        "name": "SoundCloud",
        "color": "#FF3300",
        "patterns": [r"soundcloud\.com"],
        "types": ["audio", "thumbnail"],
        "icon": "soundcloud",
    },
    {
        "id": "spotify",
        "name": "Spotify",
        "color": "#1DB954",
        "patterns": [r"open\.spotify\.com", r"spotify\.com"],
        "types": ["audio"],
        "icon": "spotify",
        "note": "Limited support – track previews only",
    },
    {
        "id": "dailymotion",
        "name": "Dailymotion",
        "color": "#0066DC",
        "patterns": [r"dailymotion\.com", r"dai\.ly"],
        "types": ["video", "audio", "thumbnail"],
        "icon": "dailymotion",
    },
    {
        "id": "snackvideo",
        "name": "Snack Video",
        "color": "#FF6600",
        "patterns": [r"snackvideo\.com"],
        "types": ["video", "audio"],
        "icon": "snackvideo",
    },
    {
        "id": "vimeo",
        "name": "Vimeo",
        "color": "#1AB7EA",
        "patterns": [r"vimeo\.com"],
        "types": ["video", "audio", "thumbnail"],
        "icon": "vimeo",
    },
    {
        "id": "likee",
        "name": "Likee",
        "color": "#FF4B00",
        "patterns": [r"likee\.video", r"likee\.com"],
        "types": ["video"],
        "icon": "likee",
    },
    {
        "id": "bilibili",
        "name": "Bilibili",
        "color": "#00A1D6",
        "patterns": [r"bilibili\.com", r"b23\.tv"],
        "types": ["video", "audio", "thumbnail"],
        "icon": "bilibili",
    },
    {
        "id": "reddit",
        "name": "Reddit",
        "color": "#FF4500",
        "patterns": [r"reddit\.com", r"redd\.it"],
        "types": ["video", "image"],
        "icon": "reddit",
    },
    {
        "id": "tumblr",
        "name": "Tumblr",
        "color": "#35465C",
        "patterns": [r"tumblr\.com"],
        "types": ["video", "image", "audio"],
        "icon": "tumblr",
    },
    {
        "id": "flickr",
        "name": "Flickr",
        "color": "#0063DC",
        "patterns": [r"flickr\.com"],
        "types": ["image", "video"],
        "icon": "flickr",
    },
    {
        "id": "imgur",
        "name": "Imgur",
        "color": "#1BB76E",
        "patterns": [r"imgur\.com"],
        "types": ["image", "video", "gif"],
        "icon": "imgur",
    },
    {
        "id": "linkedin",
        "name": "LinkedIn",
        "color": "#0A66C2",
        "patterns": [r"linkedin\.com"],
        "types": ["video"],
        "icon": "linkedin",
    },
    {
        "id": "twitch",
        "name": "Twitch",
        "color": "#9146FF",
        "patterns": [r"twitch\.tv", r"clips\.twitch\.tv"],
        "types": ["video", "audio", "thumbnail"],
        "icon": "twitch",
    },
    {
        "id": "streamable",
        "name": "Streamable",
        "color": "#0099CC",
        "patterns": [r"streamable\.com"],
        "types": ["video"],
        "icon": "streamable",
    },
    {
        "id": "loom",
        "name": "Loom",
        "color": "#7B42F6",
        "patterns": [r"loom\.com"],
        "types": ["video"],
        "icon": "loom",
    },
    {
        "id": "vk",
        "name": "VK",
        "color": "#0077FF",
        "patterns": [r"vk\.com", r"vkontakte\.ru"],
        "types": ["video", "audio", "image"],
        "icon": "vk",
    },
    {
        "id": "rumble",
        "name": "Rumble",
        "color": "#85C742",
        "patterns": [r"rumble\.com"],
        "types": ["video", "thumbnail"],
        "icon": "rumble",
    },
    {
        "id": "telegram",
        "name": "Telegram",
        "color": "#26A5E4",
        "patterns": [r"t\.me", r"telegram\.me"],
        "types": ["video", "image", "audio"],
        "icon": "telegram",
    },
    {
        "id": "generic",
        "name": "Generic Site",
        "color": "#6366F1",
        "patterns": [r".*"],
        "types": ["video", "audio"],
        "icon": "globe",
    },
]


def detect_platform(url: str) -> Optional[dict]:
    """
    Detect the platform from a given URL.
    Returns the platform dict or a generic fallback.
    """
    url_lower = url.lower()
    for platform in PLATFORMS:
        for pattern in platform["patterns"]:
            if re.search(pattern, url_lower):
                return platform
    return PLATFORMS[-1]  # Generic fallback


def get_all_platforms() -> list:
    """Return all platforms except the generic fallback."""
    return [p for p in PLATFORMS if p["id"] != "generic"]


def is_supported_url(url: str) -> bool:
    """Basic check that a URL has a valid scheme and host."""
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url, re.IGNORECASE))
