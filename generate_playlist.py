import requests
import re
import sys
from collections import OrderedDict
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
OUTPUT_FILE = "playlist.m3u"

# Your 8 exact categories (order preserved)
CATEGORIES = [
    "Tamil Local",
    "Tamil Movies",
    "Tamil News",
    "Tamil Music",
    "Tamil Kids",
    "English Movies",
    "English News",
    "Sports"
]

# Do NOT check Tamil Local URLs
SKIP_URL_CHECK = {"Tamil Local"}

# Sources from your list – add more if needed
SOURCES = [
    "https://raw.githubusercontent.com/Vmfm/tamilvmtv/live/channels.m3u",
    "https://raw.githubusercontent.com/Vmfm/tamilvmtv/live/jio.m3u",
    "https://raw.githubusercontent.com/Tamilwebcast/Tamilwebcast.github.io/main/TWCIPTV.m3u",
    "https://raw.githubusercontent.com/Indiblog/india-iptv/output/india_iptv.m3u",
    "https://raw.githubusercontent.com/Indiblog/india-iptv/output/india_general.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/jtv.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/pishow.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/yupptvfast.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/tangotv.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/ashokadigital.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/neotv.m3u",
]

# Tamil & English keyword detection (case‑insensitive)
LANG_KEYWORDS = {
    "tamil": ["tamil", "sun ", "vijay", "kalaignar", "jaya ", "raj ", "captain", 
              "polimer", "mega ", "pudhiya", "thanthi", "vasanth", "isaiaruvi",
              "k tv", "ktv", "adithya", "chutti", "chithiram", "makkal", "sirippoli",
              "vendhar", "peppers", "angel", "murugan", "madha", "velicham", "seithigal"],
    "english": ["english", "hbo", "cnn", "bbc", "disney", "discovery", "nat geo",
                "sony pix", "star movies", "mn+", "hits", "romedy", "comedy central",
                "axn", "colors infinity", "zee café", "&flix", "&privé", "star world",
                "fox", "fyi", "tlc", "animal planet", "history tv18", "news", "bloomberg"]
}

# Sports keywords (any language but we'll only keep Tamil/English audio)
SPORTS_KEYWORDS = ["sports", "star sports", "sony ten", "eurosport", "dsport",
                   "olympics", "cricket", "football", "tennis", "f1", "nba", "wwe"]

# Channels to force into categories (overrides automatic detection)
MANUAL_MAP = {
    "Sun TV": "Tamil Local",
    "Sun Music": "Tamil Music",
    "KTV": "Tamil Movies",
    "Sun News": "Tamil News",
    "Chutti TV": "Tamil Kids",
    "Star Movies": "English Movies",
    "CNN": "English News",
    "Star Sports 1": "Sports",
    # add more as needed
}

# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------
def clean_channel_name(raw):
    """Remove common tags and extra whitespace."""
    raw = re.sub(r'\s*\[.*?\]\s*', '', raw)   # [Geo-blocked] etc.
    raw = re.sub(r'\s*\(.*?\)\s*', '', raw)
    raw = re.sub(r'\s*\b(HD|SD|HEVC|4K|UHD)\b\s*', '', raw, flags=re.IGNORECASE)
    return ' '.join(raw.split()).strip()

def detect_language(name):
    """Return 'tamil', 'english', or None."""
    name_lower = name.lower()
    for keyword in LANG_KEYWORDS["tamil"]:
        if keyword in name_lower:
            return "tamil"
    for keyword in LANG_KEYWORDS["english"]:
        if keyword in name_lower:
            return "english"
    return None

def is_sports(name):
    """Check if channel is sports related."""
    return any(kw in name.lower() for kw in SPORTS_KEYWORDS)

def detect_category(name):
    """Assign one of the 8 categories based on name."""
    # First check manual map
    for key, cat in MANUAL_MAP.items():
        if key.lower() in name.lower():
            return cat

    name_lower = name.lower()
    lang = detect_language(name)

    # Sports check before language (Tamil/English sports go to Sports)
    if is_sports(name) and lang in ("tamil", "english"):
        return "Sports"

    # Tamil categories
    if lang == "tamil":
        if any(w in name_lower for w in ["movie", "cinema", "ktv", "megahit", "thirai"]):
            return "Tamil Movies"
        if any(w in name_lower for w in ["news", "seithigal", "pudhiya", "polimer news",
                                          "sun news", "thanthi tv", "news18"]):
            return "Tamil News"
        if any(w in name_lower for w in ["music", "isai", "isaiaruvi", "sun music", "mega music"]):
            return "Tamil Music"
        if any(w in name_lower for w in ["kids", "chutti", "chithiram", "cartoon", "disney",
                                          "nick", "pogo"]):
            return "Tamil Kids"
        return "Tamil Local"   # fallback

    # English categories
    if lang == "english":
        if any(w in name_lower for w in ["news", "cnn", "bbc", "ndtv", "times now", "republic",
                                          "wion", "sky news"]):
            return "English News"
        if any(w in name_lower for w in ["movie", "hbo", "star movies", "sony pix", "mn+",
                                          "hits", "romedy", "comedy central", "&flix", "zee café"]):
            return "English Movies"
        # Kids in English – still goes to Tamil Kids (you said Tamil Kids all languages)
        if any(w in name_lower for w in ["kids", "disney", "nick", "pogo", "cartoon"]):
            return "Tamil Kids"
        return "English Movies"  # fallback

    # If lang is None but it's a known kids channel in any language
    if any(w in name_lower for w in ["kids", "disney", "nick", "pogo", "cartoon"]):
        return "Tamil Kids"

    return None   # can't assign → discard

def check_url(url, timeout=3):
    """Return True if URL is reachable (HEAD request)."""
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        return r.status_code == 200
    except:
        return False

def parse_m3u(content):
    """Generator that yields (channel_name, url) from M3U text."""
    lines = content.splitlines()
    name = None
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF"):
            # Extract name after the last comma
            parts = line.split(",")
            if len(parts) > 1:
                name = parts[-1].strip()
            else:
                name = None
        elif line and not line.startswith("#") and name:
            yield name, line
            name = None

# -------------------------------------------------------------------
# Main logic
# -------------------------------------------------------------------
def main():
    # Dictionary to hold unique URLs per category
    channels = {cat: OrderedDict() for cat in CATEGORIES}
    seen_urls = set()

    # Fetch all sources
    for source in SOURCES:
        print(f"Fetching {source} ...", end=" ")
        try:
            resp = requests.get(source, timeout=15)
            resp.raise_for_status()
            content = resp.text
            print("OK")
        except Exception as e:
            print(f"FAILED ({e})")
            continue

        # Parse channels
        for raw_name, url in parse_m3u(content):
            name = clean_channel_name(raw_name)
            if not name:
                continue

            # Normalise URL
            url = url.strip()
            if not url.startswith("http"):
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)

            category = detect_category(name)
            if category is None:
                continue   # not Tamil/English or unclassifiable

            # Broken link checking (skip for Tamil Local)
            if category not in SKIP_URL_CHECK:
                if not check_url(url):
                    print(f"  ✗ Dead: {name} ({category})")
                    continue

            channels[category][url] = name
            print(f"  ✓ {name} → {category}")

    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for cat in CATEGORIES:
            f.write(f"\n# --- {cat} ---\n")
            for url, name in channels[cat].items():
                f.write(f'#EXTINF:-1 group-title="{cat}",{name}\n')
                f.write(f"{url}\n")

    # Statistics
    total = sum(len(v) for v in channels.values())
    print("\n✅ Playlist generated:")
    for cat in CATEGORIES:
        count = len(channels[cat])
        print(f"  {cat}: {count}")
    print(f"  Total unique: {total}")

    # Update README.md (optional)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 📺 Tamil & English IPTV\n\n")
        f.write(f"**Last updated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n")
        f.write(f"**Total channels:** {total}\n\n")
        f.write("| Category | Channels |\n| --- | --- |\n")
        for cat in CATEGORIES:
            f.write(f"| {cat} | {len(channels[cat])} |\n")
        f.write("\n## Usage\n")
        f.write("Add this URL to your IPTV player:\n")
        f.write("`https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/playlist.m3u`\n")

if __name__ == "__main__":
    main()
