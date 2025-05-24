# src/utils/url_parser.py
import re

def identify_platform(url: str) -> str:
    url = url.lower()
    if re.search(r"(youtube\.com|youtu\.be)", url):
        return "youtube"
    elif "instagram.com" in url:
        return "instagram"
    elif re.search(r"(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)", url):
        return "tiktok"
    else:
        return "other"