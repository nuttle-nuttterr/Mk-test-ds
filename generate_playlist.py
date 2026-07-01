import requests, re, time
from collections import OrderedDict
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

OUTPUT_FILE = "playlist.m3u"

CATEGORIES = [
    "Tamil Entertainment", "Tamil News", "Tamil Movies", "Tamil Music",
    "Tamil Kids", "Tamil Sports", "Tamil Devotional", "Tamil Infotainment",
    "Tamil Shopping", "Tamil Local", "English Movies", "English News"
]

# Sources (you can add more)
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
    "https://raw.githubusercontent.com/amazeyourself/m3u/main/neotv.m3u"
]

# Master channel list (same as before, abbreviated for space)
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
    "discovery tamil": "Tamil Infotainment", "sony bbc earth": "Tamil Infotainment"
}

BLOCKED = [
    "telugu", "hindi", "marathi", "malayalam", "kannada", "bengali", "punjabi",
    "gujarati", "oriya", "assamese", "bhojpuri", "urdu", "sanskrit",
    "etv telugu", "gemini", "maa tv", "tv9", "zee marathi", "star pravah",
    "asianet", "kiran", "flowers", "mazhavil", "kairali", "amrita",
    "sangeet", "b4u", "aaj tak", "ndtv india", "sony sab", "sony pal",
    "star plus", "zee tv", "star utsav", "star gold", "sony max",
    "dangal", "big magic", "dd national", "dd india"
]

ENGLISH_KW = ["english", "hbo", "cnn", "bbc", "disney", "discovery", "nat geo",
              "sony pix", "star movies", "mn+", "hits", "romedy", "comedy central",
              "axn", "colors infinity", "zee café", "&flix", "&privé", "star world",
              "fox", "fyi", "tlc", "bloomberg", "movies now"]

LOCAL_DOMAINS = [
    "galaxyott.live", "sscloud", "applelive.in", "maxtn.in", "olidigital.in",
    "rojatv.cloud", "thendralcloud.in", "singamcloud.in", "onecloudlive.in",
    "ipcloud.live", "notvstream.in", "livebox.co.in", "ashokadigital.net",
    "phoenixcreations.online", "7starcloud.com", "brightmeltech.in",
    "rcserver.in", "apserver.in", "bmlive.net", "mindspell.in",
    "yettelevision.com", "103.140.254", "103.87.105", "d6-pro.com"
]

def clean_name(raw):
    raw = re.sub(r'\s*\[.*?\]\s*', '', raw)
    raw = re.sub(r'\s*\(.*?\)\s*', '', raw)
    raw = re.sub(r'\s*\b(HD|SD|HEVC|4K|UHD|HDR|Dolby)\b\s*', '', raw, flags=re.I)
    return ' '.join(raw.split()).strip()

def has_blocked_words(text):
    if not text: return False
    lower = text.lower()
    for word in BLOCKED:
        if word in lower: return True
    return False

def is_english(name):
    n = name.lower()
    for kw in ENGLISH_KW:
        if kw in n: return True
    return False

def is_local_domain(url):
    try:
        domain = urlparse(url).hostname or ""
        for ld in LOCAL_DOMAINS:
            if ld in domain: return True
        return False
    except:
        return False

def detect_cat(name, url, group_title=""):
    if has_blocked_words(name) or has_blocked_words(group_title):
        return None
    clean = clean_name(name).lower()
    for master_name, category in MASTER_LIST.items():
        if master_name in clean or clean in master_name:
            return category
    if is_english(name):
        if any(w in clean for w in ["news", "cnn", "bbc", "bloomberg", "ndtv", "wion"]):
            return "English News"
        if any(w in clean for w in ["movie", "hbo", "star movies", "sony pix", "mn+", "hits", "romedy"]):
            return "English Movies"
        return None
    if is_local_domain(url):
        return "Tamil Local"
    tamil_indicators = ["tv", "tamil", "sun", "vijay", "raj", "jaya", "kalaignar",
                        "polimer", "mega", "vasanth", "vendhar", "captain", "adithya",
                        "puthu", "makkal", "sirippoli", "isai", "seithigal", "thanthi",
                        "chutti", "thirai", "musix", "aruvi", "sathiyam"]
    if any(ind in clean for ind in tamil_indicators):
        return "Tamil Local"
    return None

def check_url(url, timeout=5):
    """Return True if URL responds (tries HEAD then partial GET)."""
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        if r.status_code < 400:
            return True
    except:
        pass
    # Fallback: try a very short GET (just the first chunk)
    try:
        r = requests.get(url, timeout=timeout, stream=True, allow_redirects=True)
        r.close()
        return r.status_code < 400
    except:
        return False

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

def main():
    channels = {cat: OrderedDict() for cat in CATEGORIES}
    seen_urls = set()
    pending = []   # (category, attrs, raw_name, url)

    # Collect channels
    for src in SOURCES:
        print(f"Fetching {src} ... ", end="")
        try:
            resp = requests.get(src, timeout=15)
            resp.raise_for_status()
            print("OK")
        except Exception as e:
            print(f"FAIL ({e})")
            continue

        for attrs, raw_name, url in parse_m3u(resp.text):
            url = url.strip()
            if not url.startswith("http"): continue
            if url in seen_urls: continue
            seen_urls.add(url)

            src_group = attrs.get("group-title", "")
            category = detect_cat(raw_name, url, src_group)
            if category is None: continue

            pending.append((category, attrs, raw_name, url))

    # Test all URLs concurrently
    print(f"\nChecking {len(pending)} URLs...")
    live = 0
    dead = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_map = {executor.submit(check_url, url): (cat, attrs, name, url)
                      for (cat, attrs, name, url) in pending}
        for future in as_completed(future_map):
            cat, attrs, name, url = future_map[future]
            try:
                if future.result():
                    new_attrs = dict(attrs)
                    new_attrs["group-title"] = cat
                    channels[cat][url] = (new_attrs, name)
                    live += 1
                else:
                    dead += 1
            except:
                dead += 1

    print(f"Live: {live}, Dead: {dead}")

    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for cat in CATEGORIES:
            if not channels[cat]: continue
            f.write(f"\n# --- {cat} ---\n")
            for url, (attrs, ch_name) in channels[cat].items():
                extinf = '#EXTINF:-1'
                for k, v in attrs.items():
                    extinf += f' {k}="{v}"'
                extinf += f',{ch_name}'
                f.write(extinf + '\n')
                f.write(url + '\n')

    total = sum(len(v) for v in channels.values())
    print(f"\n✅ Done. Total: {total}")
    for cat in CATEGORIES:
        if channels[cat]:
            print(f"  {cat}: {len(channels[cat])}")

    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 📺 Tamil & English IPTV\n\n")
        f.write(f"**Updated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n")
        f.write(f"**Total:** {total} live channels\n\n")
        f.write("| Category | Live Channels |\n| --- | --- |\n")
        for cat in CATEGORIES:
            f.write(f"| {cat} | {len(channels[cat])} |\n")
        f.write("\n## Usage\n`https://raw.githubusercontent.com/nuttle-nuttterr/Mk-test-ds/main/playlist.m3u`\n")

if __name__ == "__main__":
    main()
