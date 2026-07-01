import requests, re, time, os
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import m3u8
except ImportError:
    m3u8 = None

OUTPUT_FILE = "playlist.m3u"
BACKUP_FILE = "playlist_backup.m3u"

# ---------- Sources ----------
# Primary: iptv-org’s pre‑tested language playlists
PRIMARY_SOURCES = [
    "https://iptv-org.github.io/iptv/languages/tam.m3u",
    "https://iptv-org.github.io/iptv/languages/eng.m3u"
]

# Secondary: your original repos (for extra local/regional channels)
SECONDARY_SOURCES = [
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
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/neotv.m3u"
]

CATEGORIES = [
    "Tamil Entertainment", "Tamil News", "Tamil Movies", "Tamil Music",
    "Tamil Kids", "Tamil Sports", "Tamil Devotional", "Tamil Infotainment",
    "Tamil Shopping", "Tamil Local", "English Movies", "English News"
]

# ---------- Language filtering ----------
TAMIL_KW = [
    "tamil", "sun ", "vijay", "kalaignar", "jaya ", "raj ", "captain",
    "polimer", "mega ", "pudhiya", "thanthi", "vasanth", "isaiaruvi",
    "k tv", "ktv", "adithya", "chutti", "chithiram", "makkal", "sirippoli",
    "vendhar", "peppers", "angel", "murugan", "madha", "velicham", "seithigal",
    "podhigai", "puthiya", "thalaimurai", "sathiyam", "madhimugam",
    "aruloli", "jeevan", "nambikkai", "shubhsandesh", "aastha"
]
ENGLISH_KW = [
    "english", "hbo", "cnn", "bbc", "disney", "discovery", "nat geo",
    "sony pix", "star movies", "mn+", "hits", "romedy", "comedy central",
    "axn", "colors infinity", "zee café", "&flix", "&privé", "star world",
    "fox", "fyi", "tlc", "animal planet", "history tv18", "bloomberg",
    "movies now", "sky news", "ndtv", "wion", "times now"
]
BLOCKED = [
    "telugu", "hindi", "marathi", "malayalam", "kannada", "bengali", "punjabi",
    "gujarati", "oriya", "assamese", "bhojpuri", "urdu", "sanskrit",
    "etv", "gemini", "maa tv", "tv9", "zee marathi", "star pravah",
    "asianet", "kiran", "flowers", "mazhavil", "kairali", "amrita",
    "sangeet", "b4u", "aaj tak", "sony sab", "sony pal",
    "star plus", "zee tv", "star utsav", "star gold", "sony max",
    "dangal", "big magic", "dd national", "dd india", "sony max 2",
    "colors kannada", "colors bangla", "colors gujarati", "colors marathi"
]

# ---------- Categorisation ----------
MASTER_LIST = {
    "sun tv": "Tamil Entertainment", "star vijay": "Tamil Entertainment",
    "zee tamil": "Tamil Entertainment", "colors tamil": "Tamil Entertainment",
    "kalaignar tv": "Tamil Entertainment", "raj tv": "Tamil Entertainment",
    "polimer tv": "Tamil Entertainment", "mega tv": "Tamil Entertainment",
    "vasanth tv": "Tamil Entertainment", "puthuyugam tv": "Tamil Entertainment",
    "captain tv": "Tamil Entertainment", "adithya tv": "Tamil Entertainment",
    "vendhar tv": "Tamil Entertainment", "jaya tv": "Tamil Entertainment",
    "d tamil": "Tamil Entertainment", "sirippoli": "Tamil Entertainment",
    "sun news": "Tamil News", "raj news": "Tamil News",
    "thanthi tv": "Tamil News", "news18 tamil": "Tamil News",
    "polimer news": "Tamil News", "news7 tamil": "Tamil News",
    "news j": "Tamil News", "kalaignar seithigal": "Tamil News",
    "win news": "Tamil News", "sathiyam tv": "Tamil News",
    "madhimugam tv": "Tamil News", "pudhiya thalaimurai": "Tamil News",
    "ktv": "Tamil Movies", "zee thirai": "Tamil Movies",
    "sun life": "Tamil Movies", "raj digital plus": "Tamil Movies",
    "jaya movie": "Tamil Movies", "vijay super": "Tamil Movies",
    "j movies": "Tamil Movies", "thirai tv": "Tamil Movies",
    "sun music": "Tamil Music", "raj musix": "Tamil Music",
    "isaiaruvi": "Tamil Music", "g music": "Tamil Music",
    "jcv musix": "Tamil Music", "chutti tv": "Tamil Kids",
    "chithiram tv": "Tamil Kids", "cartoon network tamil": "Tamil Kids",
    "pogo tamil": "Tamil Kids", "nick tamil": "Tamil Kids",
    "sony yay tamil": "Tamil Kids", "star sports tamil": "Tamil Sports",
    "angel tv": "Tamil Devotional", "murugan tv": "Tamil Devotional",
    "discovery tamil": "Tamil Infotainment", "sony bbc earth": "Tamil Infotainment",
    "cnn": "English News", "bbc news": "English News",
    "bloomberg": "English News", "ndtv 24x7": "English News",
    "wion": "English News", "times now": "English News",
    "sky news": "English News",
    "hbo": "English Movies", "star movies": "English Movies",
    "sony pix": "English Movies", "mn+": "English Movies",
    "&flix": "English Movies", "romedy now": "English Movies",
    "comedy central": "English Movies"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}

def clean_name(raw):
    raw = re.sub(r'\s*\[.*?\]\s*', '', raw)
    raw = re.sub(r'\s*\(.*?\)\s*', '', raw)
    raw = re.sub(r'\s*\b(HD|SD|HEVC|4K|UHD|HDR|Dolby)\b\s*', '', raw, flags=re.I)
    return ' '.join(raw.split()).strip()

def detect_language(name):
    n = name.lower()
    for word in BLOCKED:
        if word in n:
            return None
    for kw in TAMIL_KW:
        if kw in n:
            return "tamil"
    for kw in ENGLISH_KW:
        if kw in n:
            return "english"
    return None

def get_category(name, group_title=""):
    clean = clean_name(name).lower()
    for master_name, category in MASTER_LIST.items():
        if master_name in clean or clean in master_name:
            return category
    if any(kw in clean for kw in TAMIL_KW):
        return "Tamil Local"
    if any(kw in clean for kw in ENGLISH_KW):
        return "English News" if "news" in clean else "English Movies"
    return None

def parse_m3u(content):
    lines = content.splitlines()
    attrs = {}
    name = None
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF"):
            attrs = {}
            for match in re.finditer(r'(\S+)="(.*?)"', line):
                attrs[match.group(1)] = match.group(2)
            if ',' in line:
                name = line.rsplit(',', 1)[-1].strip()
            else:
                name = None
        elif line and not line.startswith("#") and name:
            yield attrs, name, line
            name = None

def fetch_channels_from_urls(urls, default_lang):
    channels = []
    for url in urls:
        print(f"  Fetching {url} ... ", end="")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            print("OK")
        except Exception as e:
            print(f"FAIL ({e})")
            continue
        for attrs, raw_name, stream_url in parse_m3u(resp.text):
            stream_url = stream_url.strip()
            if not stream_url.startswith("http"):
                continue
            lang = detect_language(raw_name)
            if lang is None:
                continue
            cat = get_category(raw_name, attrs.get("group-title", ""))
            if cat is None:
                cat = "Tamil Local" if lang == "tamil" else "English Movies"
            channels.append((cat, attrs, raw_name, stream_url))
    return channels

def check_hls_stream(url, timeout=8):
    if m3u8 is None:
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
            r.close()
            return r.status_code < 400
        except:
            return False
    try:
        playlist = m3u8.load(url, headers=HEADERS, timeout=timeout)
        if not playlist.segments:
            return False
        first_segment = playlist.segments[0].absolute_uri
        r = requests.get(first_segment, headers=HEADERS, timeout=timeout, stream=True)
        chunk = r.iter_content(chunk_size=1024).__next__()
        r.close()
        return True
    except:
        return False

def check_generic_stream(url, timeout=8):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
        chunk = r.iter_content(chunk_size=1024).__next__()
        r.close()
        return True
    except:
        return False

def is_stream_playable(url, timeout=8):
    if '.m3u8' in url:
        return check_hls_stream(url, timeout)
    else:
        return check_generic_stream(url, timeout)

def main():
    old_playlist = None
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            old_playlist = f.read()

    print("📡 Fetching primary (iptv-org) playlists...")
    primary_channels = fetch_channels_from_urls(PRIMARY_SOURCES, "tamil")
    print(f"   ✅ {len(primary_channels)} channels from primary sources")

    print("📡 Fetching secondary (community) playlists...")
    secondary_channels = fetch_channels_from_urls(SECONDARY_SOURCES, "tamil")
    print(f"   ✅ {len(secondary_channels)} channels from secondary sources")

    all_candidates = primary_channels + secondary_channels

    # Deduplicate by URL (keep first occurrence – primary takes precedence)
    output = {cat: OrderedDict() for cat in CATEGORIES}
    seen = set()
    unique_candidates = []
    for cat, attrs, raw_name, url in all_candidates:
        if url in seen:
            continue
        seen.add(url)
        unique_candidates.append((cat, attrs, raw_name, url))

    print(f"\n🔍 Deep-checking {len(unique_candidates)} unique streams (this may take 10-15 minutes)...")
    live = 0
    dead = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_map = {
            executor.submit(is_stream_playable, url, 8): (cat, attrs, raw_name, url)
            for (cat, attrs, raw_name, url) in unique_candidates
        }
        for future in as_completed(future_map):
            cat, attrs, raw_name, url = future_map[future]
            try:
                if future.result():
                    new_attrs = dict(attrs)
                    new_attrs["group-title"] = cat
                    output[cat][url] = (new_attrs, raw_name)
                    live += 1
                    print(f"  ✓ {raw_name}")
                else:
                    dead += 1
                    print(f"  ✗ {raw_name}")
            except Exception as e:
                dead += 1
                print(f"  ✗ {raw_name} (error)")

    total = sum(len(v) for v in output.values())
    if total == 0:
        print("⚠️ No playable streams found. Restoring previous playlist.")
        if old_playlist:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(old_playlist)
        else:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n# No channels available\n")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for cat in CATEGORIES:
            if not output[cat]:
                continue
            f.write(f"\n# --- {cat} ---\n")
            for url, (attrs, ch_name) in output[cat].items():
                extinf = '#EXTINF:-1'
                for k, v in attrs.items():
                    extinf += f' {k}="{v}"'
                extinf += f',{ch_name}'
                f.write(extinf + '\n')
                f.write(url + '\n')

    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        f.write(open(OUTPUT_FILE).read())

    print(f"\n✅ Final playlist: {total} truly playable channels")
    for cat in CATEGORIES:
        if output[cat]:
            print(f"  {cat}: {len(output[cat])}")

    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 📺 Tamil & English IPTV (fully validated)\n\n")
        f.write(f"**Updated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n")
        f.write(f"**Playable channels:** {total}\n\n")
        f.write("| Category | Channels |\n| --- | --- |\n")
        for cat in CATEGORIES:
            f.write(f"| {cat} | {len(output[cat])} |\n")
        f.write("\n## Usage\n`https://raw.githubusercontent.com/nuttle-nuttterr/Mk-test-ds/main/playlist.m3u`\n")

if __name__ == "__main__":
    main()
