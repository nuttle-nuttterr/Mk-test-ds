import requests, re, time
from collections import OrderedDict

OUTPUT_FILE = "playlist.m3u"
CATEGORIES = [
    "Tamil Local",      # <-- your "local channels" category
    "Tamil Movies",
    "Tamil News",
    "Tamil Music",
    "Tamil Kids",
    "English Movies",
    "English News",
    "Sports"
]
SKIP_URL_CHECK = {"Tamil Local"}   # do not test these links

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

LANG_KW = {
    "tamil": ["tamil", "sun ", "vijay", "kalaignar", "jaya ", "raj ", "captain",
              "polimer", "mega ", "pudhiya", "thanthi", "vasanth", "isaiaruvi",
              "k tv", "ktv", "adithya", "chutti", "chithiram", "makkal", "sirippoli",
              "vendhar", "peppers", "angel", "murugan", "madha", "velicham", "seithigal"],
    "english": ["english", "hbo", "cnn", "bbc", "disney", "discovery", "nat geo",
                "sony pix", "star movies", "mn+", "hits", "romedy", "comedy central",
                "axn", "colors infinity", "zee café", "&flix", "&privé", "star world",
                "fox", "fyi", "tlc", "animal planet", "history tv18", "news", "bloomberg"]
}
SPORTS_KW = ["sports", "star sports", "sony ten", "eurosport", "dsport",
             "olympics", "cricket", "football", "tennis", "f1", "nba", "wwe"]

MANUAL_MAP = {
    "Sun TV": "Tamil Local", "Sun Music": "Tamil Music", "KTV": "Tamil Movies",
    "Sun News": "Tamil News", "Chutti TV": "Tamil Kids", "Star Movies": "English Movies",
    "CNN": "English News", "Star Sports 1": "Sports"
}

def clean_name(raw):
    raw = re.sub(r'\s*\[.*?\]\s*', '', raw)
    raw = re.sub(r'\s*\(.*?\)\s*', '', raw)
    raw = re.sub(r'\s*\b(HD|SD|HEVC|4K|UHD)\b\s*', '', raw, flags=re.I)
    return ' '.join(raw.split()).strip()

def detect_lang(name):
    n = name.lower()
    for kw in LANG_KW["tamil"]:
        if kw in n: return "tamil"
    for kw in LANG_KW["english"]:
        if kw in n: return "english"
    return None

def is_sports(name):
    return any(kw in name.lower() for kw in SPORTS_KW)

def detect_cat(name):
    for key, cat in MANUAL_MAP.items():
        if key.lower() in name.lower(): return cat
    n = name.lower()
    lang = detect_lang(name)

    # Kids in any language → Tamil Kids
    if any(w in n for w in ["kids", "chutti", "chithiram", "cartoon", "disney",
                            "nick", "pogo", "motu patlu", "chhota bheem",
                            "scooby", "mr bean", "vir the robot"]):
        return "Tamil Kids"

    if is_sports(name) and lang in ("tamil", "english"):
        return "Sports"

    if lang == "tamil":
        if any(w in n for w in ["movie", "cinema", "ktv", "megahit", "thirai"]): return "Tamil Movies"
        if any(w in n for w in ["news", "seithigal", "pudhiya", "polimer news",
                                "sun news", "thanthi tv", "news18"]): return "Tamil News"
        if any(w in n for w in ["music", "isai", "isaiaruvi", "sun music", "mega music"]): return "Tamil Music"
        # Everything else Tamil → Tamil Local
        return "Tamil Local"

    if lang == "english":
        if any(w in n for w in ["news", "cnn", "bbc", "ndtv", "times now", "republic",
                                "wion", "sky news"]): return "English News"
        if any(w in n for w in ["movie", "hbo", "star movies", "sony pix", "mn+",
                                "hits", "romedy", "comedy central", "&flix", "zee café"]): return "English Movies"
        return "English Movies"

    return None

def check_url(url, timeout=3):
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        return r.status_code == 200
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
            if not url.startswith("http"):
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)

            name = clean_name(raw_name)
            if not name:
                continue

            category = detect_cat(name)
            if category is None:
                continue

            if category not in SKIP_URL_CHECK:
                if not check_url(url):
                    print(f"  ✗ Dead: {name} ({category})")
                    continue

            new_attrs = dict(attrs)
            new_attrs["group-title"] = category
            channels[category][url] = (new_attrs, raw_name)
            print(f"  ✓ {raw_name} → {category}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for cat in CATEGORIES:
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
        print(f"  {cat}: {len(channels[cat])}")

    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 📺 Tamil & English IPTV\n\n")
        f.write(f"**Updated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n")
        f.write(f"**Total:** {total}\n\n")
        f.write("| Category | Channels |\n| --- | --- |\n")
        for cat in CATEGORIES:
            f.write(f"| {cat} | {len(channels[cat])} |\n")
        f.write("\n## Usage\n`https://raw.githubusercontent.com/nuttle-nuttterr/Mk-test-ds/main/playlist.m3u`\n")

if __name__ == "__main__":
    main()
MANUAL_MAP = {
    "Sun TV": "Tamil Local", "Sun Music": "Tamil Music", "KTV": "Tamil Movies",
    "Sun News": "Tamil News", "Chutti TV": "Tamil Kids", "Star Movies": "English Movies",
    "CNN": "English News", "Star Sports 1": "Sports"
}

def clean_name(raw):
    raw = re.sub(r'\s*\[.*?\]\s*', '', raw)
    raw = re.sub(r'\s*\(.*?\)\s*', '', raw)
    raw = re.sub(r'\s*\b(HD|SD|HEVC|4K|UHD)\b\s*', '', raw, flags=re.I)
    return ' '.join(raw.split()).strip()

def detect_lang(name):
    n = name.lower()
    for kw in LANG_KW["tamil"]:
        if kw in n: return "tamil"
    for kw in LANG_KW["english"]:
        if kw in n: return "english"
    return None

def is_sports(name):
    return any(kw in name.lower() for kw in SPORTS_KW)

def detect_cat(name):
    for key, cat in MANUAL_MAP.items():
        if key.lower() in name.lower(): return cat
    n = name.lower()
    lang = detect_lang(name)

    if any(w in n for w in ["kids", "chutti", "chithiram", "cartoon", "disney",
                            "nick", "pogo", "motu patlu", "chhota bheem",
                            "scooby", "mr bean", "vir the robot"]):
        return "Tamil Kids"

    if is_sports(name) and lang in ("tamil", "english"):
        return "Sports"

    if lang == "tamil":
        if any(w in n for w in ["movie", "cinema", "ktv", "megahit", "thirai"]): return "Tamil Movies"
        if any(w in n for w in ["news", "seithigal", "pudhiya", "polimer news",
                                "sun news", "thanthi tv", "news18"]): return "Tamil News"
        if any(w in n for w in ["music", "isai", "isaiaruvi", "sun music", "mega music"]): return "Tamil Music"
        return "Tamil Local"

    if lang == "english":
        if any(w in n for w in ["news", "cnn", "bbc", "ndtv", "times now", "republic",
                                "wion", "sky news"]): return "English News"
        if any(w in n for w in ["movie", "hbo", "star movies", "sony pix", "mn+",
                                "hits", "romedy", "comedy central", "&flix", "zee café"]): return "English Movies"
        return "English Movies"

    return None

def check_url(url, timeout=3):
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        return r.status_code == 200
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
            if not url.startswith("http"):
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)

            name = clean_name(raw_name)
            if not name:
                continue

            category = detect_cat(name)
            if category is None:
                continue

            if category not in SKIP_URL_CHECK:
                if not check_url(url):
                    print(f"  ✗ Dead: {name} ({category})")
                    continue

            new_attrs = dict(attrs)
            new_attrs["group-title"] = category
            channels[category][url] = (new_attrs, raw_name)
            print(f"  ✓ {raw_name} → {category}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for cat in CATEGORIES:
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
        print(f"  {cat}: {len(channels[cat])}")

    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 📺 Tamil & English IPTV\n\n")
        f.write(f"**Updated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n")
        f.write(f"**Total:** {total}\n\n")
        f.write("| Category | Channels |\n| --- | --- |\n")
        for cat in CATEGORIES:
            f.write(f"| {cat} | {len(channels[cat])} |\n")
        f.write("\n## Usage\n`https://raw.githubusercontent.com/nuttle-nuttterr/Mk-test-ds/main/playlist.m3u`\n")

if __name__ == "__main__":
    main()
