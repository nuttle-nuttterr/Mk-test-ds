import requests, re, time
from collections import OrderedDict
from urllib.parse import urlparse

OUTPUT_FILE = "playlist.m3u"

CATEGORIES = [
    "Tamil Entertainment",
    "Tamil Local",
    "Tamil Movies",
    "Tamil News",
    "Tamil Music",
    "Tamil Kids",
    "English Movies",
    "English News",
    "Sports"
]

SKIP_URL_CHECK = {"Tamil Local", "Tamil Entertainment"}

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

BLOCKED = [
    "telugu", "hindi", "marathi", "malayalam", "kannada", "bengali", "punjabi",
    "gujarati", "oriya", "assamese", "bhojpuri", "urdu", "sanskrit",
    "etv telugu", "gemini", "maa tv", "tv9 telugu", "tv9 marathi",
    "zee marathi", "zee talkies", "colors marathi", "star pravah",
    "asianet", "kiran", "flowers", "mazhavil", "kairali",
    "amrita", "dd malayalam", "dd telugu", "dd hindi", "dd bengali",
    "sangeet", "b4u", "aaj tak", "india today", "ndtv india",
    "sony sab", "sony pal", "star plus", "colors", "zee tv",
    "star utsav", "star gold", "sony max", "zee cinema", "&pictures",
    "sony wah", "star bharat", "dangal", "big magic", "dd national",
    "dd india", "lok sabha", "rajya sabha"
]

LANG_KW = {
    "tamil": ["tamil", "sun ", "vijay", "kalaignar", "jaya ", "raj ", "captain",
              "polimer", "mega ", "pudhiya", "thanthi", "vasanth", "isaiaruvi",
              "k tv", "ktv", "adithya", "chutti", "chithiram", "makkal", "sirippoli",
              "vendhar", "peppers", "angel", "murugan", "madha", "velicham", "seithigal",
              "podhigai", "puthiya", "thalaimurai", "sathiyam", "madhimugam"],
    "english": ["english", "hbo", "cnn", "bbc", "disney", "discovery", "nat geo",
                "sony pix", "star movies", "mn+", "hits", "romedy", "comedy central",
                "axn", "colors infinity", "zee café", "&flix", "&privé", "star world",
                "fox", "fyi", "tlc", "animal planet", "history tv18", "news", "bloomberg"]
}

SPORTS_KW = ["sports", "star sports", "sony ten", "eurosport", "dsport",
             "olympics", "cricket", "football", "tennis", "f1", "nba", "wwe"]

MAJOR_TAMIL_ENT = [
    "sun tv", "star vijay", "vijay tv", "vijay super", "zee tamil",
    "colors tamil", "kalaignar tv", "jaya tv", "raj tv", "polimer tv",
    "puthuyugam tv", "dd podhigai", "vasanth tv", "d tamil", "eet tv"
]

LOCAL_DOMAINS = [
    "galaxyott.live", "sscloud7.in", "sscloud7.com", "applelive.in",
    "maxtn.in", "olidigital.in", "rojatv.cloud", "thendralcloud.in",
    "singamcloud.in", "onecloudlive.in", "ipcloud.live", "notvstream.in",
    "livebox.co.in", "ashokadigital.net", "phoenixcreations.online",
    "7starcloud.com", "brightmeltech.in", "rcserver.in", "apserver.in",
    "bmlive.net", "mindspell.in", "yettelevision.com", "103.140.254.2",
    "103.87.105.51"
]

def clean_name(raw):
    raw = re.sub(r'\s*\[.*?\]\s*', '', raw)
    raw = re.sub(r'\s*\(.*?\)\s*', '', raw)
    raw = re.sub(r'\s*\b(HD|SD|HEVC|4K|UHD)\b\s*', '', raw, flags=re.I)
    return ' '.join(raw.split()).strip()

def has_blocked_words(text):
    if not text:
        return False
    lower = text.lower()
    for word in BLOCKED:
        if word in lower:
            return True
    return False

def detect_lang(name):
    n = name.lower()
    for kw in LANG_KW["tamil"]:
        if kw in n:
            return "tamil"
    for kw in LANG_KW["english"]:
        if kw in n:
            return "english"
    return None

def is_sports(name):
    return any(kw in name.lower() for kw in SPORTS_KW)

def is_local_domain(url):
    try:
        domain = urlparse(url).hostname
        return domain in LOCAL_DOMAINS
    except:
        return False

def detect_cat(name, url, group_title=""):
    if has_blocked_words(name) or has_blocked_words(group_title):
        return None

    n = name.lower()
    lang = detect_lang(name)

    if any(w in n for w in ["kids", "chutti", "chithiram", "cartoon", "disney",
                            "nick", "pogo", "motu patlu", "chhota bheem",
                            "scooby", "mr bean", "vir the robot"]):
        return "Tamil Kids"

    if is_sports(name) and lang in ("tamil", "english"):
        return "Sports"

    if lang == "tamil":
        if any(w in n for w in ["movie", "cinema", "ktv", "megahit", "thirai"]):
            return "Tamil Movies"
        if any(w in n for w in ["news", "seithigal", "pudhiya", "polimer news",
                                "sun news", "thanthi tv", "news18", "win news",
                                "news7", "news j"]):
            return "Tamil News"
        if any(w in n for w in ["music", "isai", "isaiaruvi", "sun music",
                                "mega music", "raj musix", "g music", "jcv musix"]):
            return "Tamil Music"

        if any(major in n for major in MAJOR_TAMIL_ENT):
            return "Tamil Entertainment"

        if is_local_domain(url):
            return "Tamil Local"

        return "Tamil Entertainment"

    if lang == "english":
        if any(w in n for w in ["news", "cnn", "bbc", "ndtv", "times now", "republic",
                                "wion", "sky news", "bloomberg"]):
            return "English News"
        if any(w in n for w in ["movie", "hbo", "star movies", "sony pix", "mn+",
                                "hits", "romedy", "comedy central", "&flix", "zee café"]):
            return "English Movies"
        return None

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

            src_group = attrs.get("group-title", "")
            category = detect_cat(raw_name, url, src_group)
            if category is None:
                continue

            if category not in SKIP_URL_CHECK:
                if not check_url(url):
                    print(f"  ✗ Dead: {raw_name} ({category})")
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
    main()    "gujarati", "oriya", "assamese", "bhojpuri", "urdu", "sanskrit",
    "etv telugu", "gemini", "maa tv", "tv9 telugu", "tv9 marathi",
    "zee marathi", "zee talkies", "colors marathi", "star pravah",
    "asianet", "surya tv", "kiran", "flowers", "mazhavil", "kairali",
    "amrita", "dd malayalam", "dd telugu", "dd hindi", "dd bengali",
    "sangeet", "b4u", "aaj tak", "india today", "ndtv india",
    "sony sab", "sony pal", "star plus", "colors", "zee tv",
    "star utsav", "star gold", "sony max", "zee cinema", "&pictures",
    "sony wah", "star bharat", "dangal", "big magic", "dd national",
    "dd india", "lok sabha", "rajya sabha"
}

LANG_KW = {
    "tamil": ["tamil", "sun ", "vijay", "kalaignar", "jaya ", "raj ", "captain",
              "polimer", "mega ", "pudhiya", "thanthi", "vasanth", "isaiaruvi",
              "k tv", "ktv", "adithya", "chutti", "chithiram", "makkal", "sirippoli",
              "vendhar", "peppers", "angel", "murugan", "madha", "velicham", "seithigal",
              "podhigai", "puthiya", "thalaimurai", "sathiyam", "madhimugam"],
    "english": ["english", "hbo", "cnn", "bbc", "disney", "discovery", "nat geo",
                "sony pix", "star movies", "mn+", "hits", "romedy", "comedy central",
                "axn", "colors infinity", "zee café", "&flix", "&privé", "star world",
                "fox", "fyi", "tlc", "animal planet", "history tv18", "news", "bloomberg"]
}

SPORTS_KW = ["sports", "star sports", "sony ten", "eurosport", "dsport",
             "olympics", "cricket", "football", "tennis", "f1", "nba", "wwe"]

MAJOR_TAMIL_ENT = {
    "sun tv", "star vijay", "vijay tv", "vijay super", "zee tamil",
    "colors tamil", "kalaignar tv", "jaya tv", "raj tv", "polimer tv",
    "puthuyugam tv", "dd podhigai", "vasanth tv", "d tamil", "eet tv"
}

LOCAL_DOMAINS = {
    "galaxyott.live", "sscloud7.in", "sscloud7.com", "applelive.in",
    "maxtn.in", "olidigital.in", "rojatv.cloud", "thendralcloud.in",
    "singamcloud.in", "onecloudlive.in", "ipcloud.live", "notvstream.in",
    "livebox.co.in", "ashokadigital.net", "phoenixcreations.online",
    "7starcloud.com", "brightmeltech.in", "rcserver.in", "apserver.in",
    "bmlive.net", "mindspell.in", "yettelevision.com", "103.140.254.2",
    "103.87.105.51"
}

def clean_name(raw):
    raw = re.sub(r'\s*\[.*?\]\s*', '', raw)
    raw = re.sub(r'\s*\(.*?\)\s*', '', raw)
    raw = re.sub(r'\s*\b(HD|SD|HEVC|4K|UHD)\b\s*', '', raw, flags=re.I)
    return ' '.join(raw.split()).strip()

def has_blocked_words(text):
    if not text:
        return False
    lower = text.lower()
    for word in BLOCKED:
        if word in lower:
            return True
    return False

def detect_lang(name):
    n = name.lower()
    for kw in LANG_KW["tamil"]:
        if kw in n:
            return "tamil"
    for kw in LANG_KW["english"]:
        if kw in n:
            return "english"
    return None

def is_sports(name):
    return any(kw in name.lower() for kw in SPORTS_KW)

def is_local_domain(url):
    try:
        domain = urlparse(url).hostname
        return domain in LOCAL_DOMAINS
    except:
        return False

def detect_cat(name, url, group_title=""):
    if has_blocked_words(name) or has_blocked_words(group_title):
        return None

    n = name.lower()
    lang = detect_lang(name)

    if any(w in n for w in ["kids", "chutti", "chithiram", "cartoon", "disney",
                            "nick", "pogo", "motu patlu", "chhota bheem",
                            "scooby", "mr bean", "vir the robot"]):
        return "Tamil Kids"

    if is_sports(name) and lang in ("tamil", "english"):
        return "Sports"

    if lang == "tamil":
        if any(w in n for w in ["movie", "cinema", "ktv", "megahit", "thirai"]):
            return "Tamil Movies"
        if any(w in n for w in ["news", "seithigal", "pudhiya", "polimer news",
                                "sun news", "thanthi tv", "news18", "win news",
                                "news7", "news j"]):
            return "Tamil News"
        if any(w in n for w in ["music", "isai", "isaiaruvi", "sun music",
                                "mega music", "raj musix", "g music", "jcv musix"]):
            return "Tamil Music"

        if any(major in n for major in MAJOR_TAMIL_ENT):
            return "Tamil Entertainment"

        if is_local_domain(url):
            return "Tamil Local"

        return "Tamil Entertainment"

    if lang == "english":
        if any(w in n for w in ["news", "cnn", "bbc", "ndtv", "times now", "republic",
                                "wion", "sky news", "bloomberg"]):
            return "English News"
        if any(w in n for w in ["movie", "hbo", "star movies", "sony pix", "mn+",
                                "hits", "romedy", "comedy central", "&flix", "zee café"]):
            return "English Movies"
        return None

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

            src_group = attrs.get("group-title", "")
            category = detect_cat(raw_name, url, src_group)
            if category is None:
                continue

            if category not in SKIP_URL_CHECK:
                if not check_url(url):
                    print(f"  ✗ Dead: {raw_name} ({category})")
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
    main()    "telugu", "hindi", "marathi", "malayalam", "kannada", "bengali", "punjabi",
    "gujarati", "oriya", "assamese", "bhojpuri", "urdu", "sanskrit",
    "etv telugu", "gemini", "maa tv", "tv9 telugu", "tv9 marathi",
    "zee marathi", "zee talkies", "colors marathi", "star pravah",
    "asianet", "surya tv", "kiran", "flowers", "mazhavil", "kairali",
    "amrita", "dd malayalam", "dd telugu", "dd hindi", "dd bengali",
    "sangeet", "b4u", "aaj tak", "india today", "ndtv india",
    "sony sab", "sony pal", "star plus", "colors", "zee tv",
    "star utsav", "star gold", "sony max", "zee cinema", "&pictures",
    "sony wah", "star bharat", "dangal", "big magic", "dd national",
    "dd india", "lok sabha", "rajya sabha"
}

LANG_KW = {
    "tamil": ["tamil", "sun ", "vijay", "kalaignar", "jaya ", "raj ", "captain",
              "polimer", "mega ", "pudhiya", "thanthi", "vasanth", "isaiaruvi",
              "k tv", "ktv", "adithya", "chutti", "chithiram", "makkal", "sirippoli",
              "vendhar", "peppers", "angel", "murugan", "madha", "velicham", "seithigal",
              "podhigai", "puthiya", "thalaimurai", "sathiyam", "madhimugam"],
    "english": ["english", "hbo", "cnn", "bbc", "disney", "discovery", "nat geo",
                "sony pix", "star movies", "mn+", "hits", "romedy", "comedy central",
                "axn", "colors infinity", "zee café", "&flix", "&privé", "star world",
                "fox", "fyi", "tlc", "animal planet", "history tv18", "news", "bloomberg"]
}

SPORTS_KW = ["sports", "star sports", "sony ten", "eurosport", "dsport",
             "olympics", "cricket", "football", "tennis", "f1", "nba", "wwe"]

MAJOR_TAMIL_ENT = {
    "sun tv", "star vijay", "vijay tv", "vijay super", "zee tamil",
    "colors tamil", "kalaignar tv", "jaya tv", "raj tv", "polimer tv",
    "puthuyugam tv", "dd podhigai", "vasanth tv", "d tamil", "eet tv"
}

LOCAL_DOMAINS = {
    "galaxyott.live", "sscloud7.in", "sscloud7.com", "applelive.in",
    "maxtn.in", "olidigital.in", "rojatv.cloud", "thendralcloud.in",
    "singamcloud.in", "onecloudlive.in", "ipcloud.live", "notvstream.in",
    "livebox.co.in", "ashokadigital.net", "phoenixcreations.online",
    "7starcloud.com", "brightmeltech.in", "rcserver.in", "apserver.in",
    "bmlive.net", "mindspell.in", "yettelevision.com", "103.140.254.2",
    "103.87.105.51"
}

def clean_name(raw):
    raw = re.sub(r'\s*\[.*?\]\s*', '', raw)
    raw = re.sub(r'\s*\(.*?\)\s*', '', raw)
    raw = re.sub(r'\s*\b(HD|SD|HEVC|4K|UHD)\b\s*', '', raw, flags=re.I)
    return ' '.join(raw.split()).strip()

def has_blocked_words(text):
    if not text:
        return False
    lower = text.lower()
    for word in BLOCKED:
        if word in lower:
            return True
    return False

def detect_lang(name):
    n = name.lower()
    for kw in LANG_KW["tamil"]:
        if kw in n:
            return "tamil"
    for kw in LANG_KW["english"]:
        if kw in n:
            return "english"
    return None

def is_sports(name):
    return any(kw in name.lower() for kw in SPORTS_KW)

def is_local_domain(url):
    try:
        domain = urlparse(url).hostname
        return domain in LOCAL_DOMAINS
    except:
        return False

def detect_cat(name, url, group_title=""):
    if has_blocked_words(name) or has_blocked_words(group_title):
        return None

    n = name.lower()
    lang = detect_lang(name)

    # Kids (any language)
    if any(w in n for w in ["kids", "chutti", "chithiram", "cartoon", "disney",
                            "nick", "pogo", "motu patlu", "chhota bheem",
                            "scooby", "mr bean", "vir the robot"]):
        return "Tamil Kids"

    # Sports
    if is_sports(name) and lang in ("tamil", "english"):
        return "Sports"

    if lang == "tamil":
        if any(w in n for w in ["movie", "cinema", "ktv", "megahit", "thirai"]):
            return "Tamil Movies"
        if any(w in n for w in ["news", "seithigal", "pudhiya", "polimer news",
                                "sun news", "thanthi tv", "news18", "win news",
                                "news7", "news j"]):
            return "Tamil News"
        if any(w in n for w in ["music", "isai", "isaiaruvi", "sun music",
                                "mega music", "raj musix", "g music", "jcv musix"]):
            return "Tamil Music"

        if any(major in n for major in MAJOR_TAMIL_ENT):
            return "Tamil Entertainment"

        if is_local_domain(url):
            return "Tamil Local"

        return "Tamil Entertainment"

    if lang == "english":
        if any(w in n for w in ["news", "cnn", "bbc", "ndtv", "times now", "republic",
                                "wion", "sky news", "bloomberg"]):
            return "English News"
        if any(w in n for w in ["movie", "hbo", "star movies", "sony pix", "mn+",
                                "hits", "romedy", "comedy central", "&flix", "zee café"]):
            return "English Movies"
        return None

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

            src_group = attrs.get("group-title", "")
            category = detect_cat(raw_name, url, src_group)
            if category is None:
                continue

            if category not in SKIP_URL_CHECK:
                if not check_url(url):
                    print(f"  ✗ Dead: {raw_name} ({category})")
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
    main()    "gujarati", "oriya", "assamese", "bhojpuri", "urdu", "sanskrit",
    "etv telugu", "gemini", "maa tv", "tv9 telugu", "tv9 marathi",
    "zee marathi", "zee talkies", "colors marathi", "star pravah",
    "asianet", "surya tv", "kiran", "flowers", "mazhavil", "kairali",
    "amrita", "dd malayalam", "dd telugu", "dd hindi", "dd bengali",
    "sangeet", "b4u", "aaj tak", "india today", "ndtv india",
    "sony sab", "sony pal", "star plus", "colors", "zee tv",
    "star utsav", "star gold", "sony max", "zee cinema", "&pictures",
    "sony wah", "star bharat", "dangal", "big magic", "dd national",
    "dd india", "lok sabha", "rajya sabha"
}

LANG_KW = {
    "tamil": ["tamil", "sun ", "vijay", "kalaignar", "jaya ", "raj ", "captain",
              "polimer", "mega ", "pudhiya", "thanthi", "vasanth", "isaiaruvi",
              "k tv", "ktv", "adithya", "chutti", "chithiram", "makkal", "sirippoli",
              "vendhar", "peppers", "angel", "murugan", "madha", "velicham", "seithigal",
              "podhigai", "puthiya", "thalaimurai", "sathiyam", "madhimugam"],
    "english": ["english", "hbo", "cnn", "bbc", "disney", "discovery", "nat geo",
                "sony pix", "star movies", "mn+", "hits", "romedy", "comedy central",
                "axn", "colors infinity", "zee café", "&flix", "&privé", "star world",
                "fox", "fyi", "tlc", "animal planet", "history tv18", "news", "bloomberg"]
}

SPORTS_KW = ["sports", "star sports", "sony ten", "eurosport", "dsport",
             "olympics", "cricket", "football", "tennis", "f1", "nba", "wwe"]

MAJOR_TAMIL_ENT = {
    "sun tv", "star vijay", "vijay tv", "vijay super", "zee tamil",
    "colors tamil", "kalaignar tv", "jaya tv", "raj tv", "polimer tv",
    "puthuyugam tv", "dd podhigai", "vasanth tv", "d tamil", "eet tv"
}

LOCAL_DOMAINS = {
    "galaxyott.live", "sscloud7.in", "sscloud7.com", "applelive.in",
    "maxtn.in", "olidigital.in", "rojatv.cloud", "thendralcloud.in",
    "singamcloud.in", "onecloudlive.in", "ipcloud.live", "notvstream.in",
    "livebox.co.in", "ashokadigital.net", "phoenixcreations.online",
    "7starcloud.com", "brightmeltech.in", "rcserver.in", "apserver.in",
    "bmlive.net", "mindspell.in", "yettelevision.com", "103.140.254.2",
    "103.87.105.51"
}

def clean_name(raw):
    raw = re.sub(r'\s*\[.*?\]\s*', '', raw)
    raw = re.sub(r'\s*\(.*?\)\s*', '', raw)
    raw = re.sub(r'\s*\b(HD|SD|HEVC|4K|UHD)\b\s*', '', raw, flags=re.I)
    return ' '.join(raw.split()).strip()

def has_blocked_words(text):
    if not text:
        return False
    lower = text.lower()
    for word in BLOCKED:
        if word in lower:
            return True
    return False

def detect_lang(name):
    n = name.lower()
    for kw in LANG_KW["tamil"]:
        if kw in n:
            return "tamil"
    for kw in LANG_KW["english"]:
        if kw in n:
            return "english"
    return None

def is_sports(name):
    return any(kw in name.lower() for kw in SPORTS_KW)

def is_local_domain(url):
    try:
        domain = urlparse(url).hostname
        return domain in LOCAL_DOMAINS
    except:
        return False

def detect_cat(name, url, group_title=""):
    if has_blocked_words(name) or has_blocked_words(group_title):
        return None

    n = name.lower()
    lang = detect_lang(name)

    # Kids (any language)
    if any(w in n for w in ["kids", "chutti", "chithiram", "cartoon", "disney",
                            "nick", "pogo", "motu patlu", "chhota bheem",
                            "scooby", "mr bean", "vir the robot"]):
        return "Tamil Kids"

    # Sports
    if is_sports(name) and lang in ("tamil", "english"):
        return "Sports"

    if lang == "tamil":
        if any(w in n for w in ["movie", "cinema", "ktv", "megahit", "thirai"]):
            return "Tamil Movies"
        if any(w in n for w in ["news", "seithigal", "pudhiya", "polimer news",
                                "sun news", "thanthi tv", "news18", "win news",
                                "news7", "news j"]):
            return "Tamil News"
        if any(w in n for w in ["music", "isai", "isaiaruvi", "sun music",
                                "mega music", "raj musix", "g music", "jcv musix"]):
            return "Tamil Music"

        if any(major in n for major in MAJOR_TAMIL_ENT):
            return "Tamil Entertainment"

        if is_local_domain(url):
            return "Tamil Local"

        return "Tamil Entertainment"

    if lang == "english":
        if any(w in n for w in ["news", "cnn", "bbc", "ndtv", "times now", "republic",
                                "wion", "sky news", "bloomberg"]):
            return "English News"
        if any(w in n for w in ["movie", "hbo", "star movies", "sony pix", "mn+",
                                "hits", "romedy", "comedy central", "&flix", "zee café"]):
            return "English Movies"
        return None

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

            src_group = attrs.get("group-title", "")
            category = detect_cat(raw_name, url, src_group)
            if category is None:
                continue

            if category not in SKIP_URL_CHECK:
                if not check_url(url):
                    print(f"  ✗ Dead: {raw_name} ({category})")
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
    main()    "telugu", "hindi", "marathi", "malayalam", "kannada", "bengali", "punjabi",
    "gujarati", "oriya", "assamese", "bhojpuri", "urdu", "sanskrit",
    "etv telugu", "gemini", "maa tv", "tv9 telugu", "tv9 marathi",
    "zee marathi", "zee talkies", "colors marathi", "star pravah",
    "asianet", "surya tv", "kiran", "flowers", "mazhavil", "kairali",
    "amrita", "dd malayalam", "dd telugu", "dd hindi", "dd bengali",
    "sangeet", "b4u", "aaj tak", "india today", "ndtv india",
    "sony sab", "sony pal", "star plus", "colors", "zee tv",
    "star utsav", "star gold", "sony max", "zee cinema", "&pictures",
    "sony wah", "star bharat", "dangal", "big magic", "dd national",
    "dd india", "lok sabha", "rajya sabha"
}

# ---------- LANGUAGE DETECTION KEYWORDS ----------
LANG_KW = {
    "tamil": ["tamil", "sun ", "vijay", "kalaignar", "jaya ", "raj ", "captain",
              "polimer", "mega ", "pudhiya", "thanthi", "vasanth", "isaiaruvi",
              "k tv", "ktv", "adithya", "chutti", "chithiram", "makkal", "sirippoli",
              "vendhar", "peppers", "angel", "murugan", "madha", "velicham", "seithigal",
              "podhigai", "puthiya", "thalaimurai", "sathiyam", "madhimugam"],
    "english": ["english", "hbo", "cnn", "bbc", "disney", "discovery", "nat geo",
                "sony pix", "star movies", "mn+", "hits", "romedy", "comedy central",
                "axn", "colors infinity", "zee café", "&flix", "&privé", "star world",
                "fox", "fyi", "tlc", "animal planet", "history tv18", "news", "bloomberg"]
}

SPORTS_KW = ["sports", "star sports", "sony ten", "eurosport", "dsport",
             "olympics", "cricket", "football", "tennis", "f1", "nba", "wwe"]

# Major Tamil entertainment channels → Tamil Entertainment (not Local)
MAJOR_TAMIL_ENT = {
    "sun tv", "star vijay", "vijay tv", "vijay super", "zee tamil",
    "colors tamil", "kalaignar tv", "jaya tv", "raj tv", "polimer tv",
    "puthuyugam tv", "dd podhigai", "vasanth tv", "d tamil", "eet tv"
}

# Domains that indicate a small local cable channel → Tamil Local
LOCAL_DOMAINS = {
    "galaxyott.live", "sscloud7.in", "sscloud7.com", "applelive.in",
    "maxtn.in", "olidigital.in", "rojatv.cloud", "thendralcloud.in",
    "singamcloud.in", "onecloudlive.in", "ipcloud.live", "notvstream.in",
    "livebox.co.in", "ashokadigital.net", "phoenixcreations.online",
    "7starcloud.com", "brightmeltech.in", "rcserver.in", "apserver.in",
    "bmlive.net", "mindspell.in", "yettelevision.com", "103.140.254.2",
    "103.87.105.51"
}

def clean_name(raw):
    raw = re.sub(r'\s*\[.*?\]\s*', '', raw)
    raw = re.sub(r'\s*\(.*?\)\s*', '', raw)
    raw = re.sub(r'\s*\b(HD|SD|HEVC|4K|UHD)\b\s*', '', raw, flags=re.I)
    return ' '.join(raw.split()).strip()

def has_blocked_words(text):
    """Return True if any blocked language word appears in the text."""
    if not text:
        return False
    lower = text.lower()
    for word in BLOCKED:
        if word in lower:
            return True
    return False

def detect_lang(name):
    n = name.lower()
    for kw in LANG_KW["tamil"]:
        if kw in n:
            return "tamil"
    for kw in LANG_KW["english"]:
        if kw in n:
            return "english"
    return None

def is_sports(name):
    return any(kw in name.lower() for kw in SPORTS_KW)

def is_local_domain(url):
    """Check if the URL's domain is in our known local cable list."""
    try:
        domain = urlparse(url).hostname
        return domain in LOCAL_DOMAINS
    except:
        return False

def detect_cat(name, url, group_title=""):
    """Return the appropriate category, or None if channel should be skipped."""
    # 1. Hard block on name or group-title
    if has_blocked_words(name) or has_blocked_words(group_title):
        return None

    n = name.lower()
    lang = detect_lang(name)

    # 2. Kids – allowed in any language
    if any(w in n for w in ["kids", "chutti", "chithiram", "cartoon", "disney",
                            "nick", "pogo", "motu patlu", "chhota bheem",
                            "scooby", "mr bean", "vir the robot"]):
        return "Tamil Kids"

    # 3. Sports
    if is_sports(name) and lang in ("tamil", "english"):
        return "Sports"

    # 4. Tamil
    if lang == "tamil":
        # Specific categories first
        if any(w in n for w in ["movie", "cinema", "ktv", "megahit", "thirai"]):
            return "Tamil Movies"
        if any(w in n for w in ["news", "seithigal", "pudhiya", "polimer news",
                                "sun news", "thanthi tv", "news18", "win news",
                                "news7", "news j"]):
            return "Tamil News"
        if any(w in n for w in ["music", "isai", "isaiaruvi", "sun music",
                                "mega music", "raj musix", "g music", "jcv musix"]):
            return "Tamil Music"

        # Major entertainment channels → Tamil Entertainment
        if any(major in n for major in MAJOR_TAMIL_ENT):
            return "Tamil Entertainment"

        # If URL indicates a local cable operator → Tamil Local
        if is_local_domain(url):
            return "Tamil Local"

        # Fallback for any other Tamil channel → Tamil Entertainment
        return "Tamil Entertainment"

    # 5. English
    if lang == "english":
        if any(w in n for w in ["news", "cnn", "bbc", "ndtv", "times now", "republic",
                                "wion", "sky news", "bloomberg"]):
            return "English News"
        if any(w in n for w in ["movie", "hbo", "star movies", "sony pix", "mn+",
                                "hits", "romedy", "comedy central", "&flix", "zee café"]):
            return "English Movies"
        # For English channels that are not movies or news, discard
        return None

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

            src_group = attrs.get("group-title", "")
            category = detect_cat(raw_name, url, src_group)
            if category is None:
                continue

            if category not in SKIP_URL_CHECK:
                if not check_url(url):
                    print(f"  ✗ Dead: {raw_name} ({category})")
                    continue

            new_attrs = dict(attrs)
            new_attrs["group-title"] = category
            channels[category][url] = (new_attrs, raw_name)
            print(f"  ✓ {raw_name} → {category}")

    # Write output
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
    main()    "telugu", "hindi", "marathi", "malayalam", "kannada", "bengali", "punjabi",
    "gujarati", "oriya", "assamese", "bhojpuri", "urdu", "sanskrit",
    "etv telugu", "gemini", "maa tv", "tv9 telugu", "tv9 marathi",
    "zee marathi", "zee talkies", "colors marathi", "star pravah",
    "asianet", "surya tv", "kiran", "flowers", "mazhavil", "kairali",
    "amrita", "dd malayalam", "dd telugu", "dd hindi", "dd bengali",
    "sangeet", "b4u", "aaj tak", "india today", "ndtv india",
    "sony sab", "sony pal", "star plus", "colors", "zee tv",
    "star utsav", "star gold", "sony max", "zee cinema", "&pictures",
    "sony wah", "star bharat", "dangal", "big magic", "dd national",
    "dd india", "lok sabha", "rajya sabha"
}

# ---------- LANGUAGE DETECTION KEYWORDS ----------
LANG_KW = {
    "tamil": ["tamil", "sun ", "vijay", "kalaignar", "jaya ", "raj ", "captain",
              "polimer", "mega ", "pudhiya", "thanthi", "vasanth", "isaiaruvi",
              "k tv", "ktv", "adithya", "chutti", "chithiram", "makkal", "sirippoli",
              "vendhar", "peppers", "angel", "murugan", "madha", "velicham", "seithigal",
              "podhigai", "puthiya", "thalaimurai", "sathiyam", "madhimugam"],
    "english": ["english", "hbo", "cnn", "bbc", "disney", "discovery", "nat geo",
                "sony pix", "star movies", "mn+", "hits", "romedy", "comedy central",
                "axn", "colors infinity", "zee café", "&flix", "&privé", "star world",
                "fox", "fyi", "tlc", "animal planet", "history tv18", "news", "bloomberg"]
}

SPORTS_KW = ["sports", "star sports", "sony ten", "eurosport", "dsport",
             "olympics", "cricket", "football", "tennis", "f1", "nba", "wwe"]

# Major Tamil entertainment channels → Tamil Entertainment (not Local)
MAJOR_TAMIL_ENT = {
    "sun tv", "star vijay", "vijay tv", "vijay super", "zee tamil",
    "colors tamil", "kalaignar tv", "jaya tv", "raj tv", "polimer tv",
    "puthuyugam tv", "dd podhigai", "vasanth tv", "d tamil", "eet tv"
}

# Domains that indicate a small local cable channel → Tamil Local
LOCAL_DOMAINS = {
    "galaxyott.live", "sscloud7.in", "sscloud7.com", "applelive.in",
    "maxtn.in", "olidigital.in", "rojatv.cloud", "thendralcloud.in",
    "singamcloud.in", "onecloudlive.in", "ipcloud.live", "notvstream.in",
    "livebox.co.in", "ashokadigital.net", "phoenixcreations.online",
    "7starcloud.com", "brightmeltech.in", "rcserver.in", "apserver.in",
    "bmlive.net", "mindspell.in", "yettelevision.com", "103.140.254.2",
    "103.87.105.51"
}

def clean_name(raw):
    raw = re.sub(r'\s*\[.*?\]\s*', '', raw)
    raw = re.sub(r'\s*\(.*?\)\s*', '', raw)
    raw = re.sub(r'\s*\b(HD|SD|HEVC|4K|UHD)\b\s*', '', raw, flags=re.I)
    return ' '.join(raw.split()).strip()

def has_blocked_words(text):
    """Return True if any blocked language word appears in the text."""
    if not text:
        return False
    lower = text.lower()
    for word in BLOCKED:
        if word in lower:
            return True
    return False

def detect_lang(name):
    n = name.lower()
    for kw in LANG_KW["tamil"]:
        if kw in n:
            return "tamil"
    for kw in LANG_KW["english"]:
        if kw in n:
            return "english"
    return None

def is_sports(name):
    return any(kw in name.lower() for kw in SPORTS_KW)

def is_local_domain(url):
    """Check if the URL's domain is in our known local cable list."""
    try:
        domain = urlparse(url).hostname
        return domain in LOCAL_DOMAINS
    except:
        return False

def detect_cat(name, url, group_title=""):
    """Return the appropriate category, or None if channel should be skipped."""
    # 1. Hard block on name or group-title
    if has_blocked_words(name) or has_blocked_words(group_title):
        return None

    n = name.lower()
    lang = detect_lang(name)

    # 2. Kids – allowed in any language
    if any(w in n for w in ["kids", "chutti", "chithiram", "cartoon", "disney",
                            "nick", "pogo", "motu patlu", "chhota bheem",
                            "scooby", "mr bean", "vir the robot"]):
        return "Tamil Kids"

    # 3. Sports
    if is_sports(name) and lang in ("tamil", "english"):
        return "Sports"

    # 4. Tamil
    if lang == "tamil":
        # Specific categories first
        if any(w in n for w in ["movie", "cinema", "ktv", "megahit", "thirai"]):
            return "Tamil Movies"
        if any(w in n for w in ["news", "seithigal", "pudhiya", "polimer news",
                                "sun news", "thanthi tv", "news18", "win news",
                                "news7", "news j"]):
            return "Tamil News"
        if any(w in n for w in ["music", "isai", "isaiaruvi", "sun music",
                                "mega music", "raj musix", "g music", "jcv musix"]):
            return "Tamil Music"

        # Major entertainment channels → Tamil Entertainment
        if any(major in n for major in MAJOR_TAMIL_ENT):
            return "Tamil Entertainment"

        # If URL indicates a local cable operator → Tamil Local
        if is_local_domain(url):
            return "Tamil Local"

        # Fallback for any other Tamil channel → Tamil Entertainment
        return "Tamil Entertainment"

    # 5. English
    if lang == "english":
        if any(w in n for w in ["news", "cnn", "bbc", "ndtv", "times now", "republic",
                                "wion", "sky news", "bloomberg"]):
            return "English News"
        if any(w in n for w in ["movie", "hbo", "star movies", "sony pix", "mn+",
                                "hits", "romedy", "comedy central", "&flix", "zee café"]):
            return "English Movies"
        # For English channels that are not movies or news, discard
        return None

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

            src_group = attrs.get("group-title", "")
            category = detect_cat(raw_name, url, src_group)
            if category is None:
                continue

            if category not in SKIP_URL_CHECK:
                if not check_url(url):
                    print(f"  ✗ Dead: {raw_name} ({category})")
                    continue

            new_attrs = dict(attrs)
            new_attrs["group-title"] = category
            channels[category][url] = (new_attrs, raw_name)
            print(f"  ✓ {raw_name} → {category}")

    # Write output
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
    main()    "telugu", "hindi", "marathi", "malayalam", "kannada", "bengali", "punjabi",
    "gujarati", "oriya", "assamese", "bhojpuri", "urdu", "sanskrit",
    "etv telugu", "gemini", "maa tv", "tv9 telugu", "tv9 marathi",
    "zee marathi", "zee talkies", "colors marathi", "star pravah",
    "asianet", "surya tv", "kiran", "flowers", "mazhavil", "kairali",
    "amrita", "dd malayalam", "dd telugu", "dd hindi", "dd bengali",
    "sangeet", "b4u", "aaj tak", "india today", "ndtv india",
    "sony sab", "sony pal", "star plus", "colors", "zee tv",
    "star utsav", "star gold", "sony max", "zee cinema", "&pictures",
    "sony wah", "star bharat", "dangal", "big magic", "dd national",
    "dd india", "lok sabha", "rajya sabha"
}

# ---------- LANGUAGE DETECTION KEYWORDS ----------
LANG_KW = {
    "tamil": ["tamil", "sun ", "vijay", "kalaignar", "jaya ", "raj ", "captain",
              "polimer", "mega ", "pudhiya", "thanthi", "vasanth", "isaiaruvi",
              "k tv", "ktv", "adithya", "chutti", "chithiram", "makkal", "sirippoli",
              "vendhar", "peppers", "angel", "murugan", "madha", "velicham", "seithigal",
              "podhigai", "puthiya", "thalaimurai", "sathiyam", "madhimugam"],
    "english": ["english", "hbo", "cnn", "bbc", "disney", "discovery", "nat geo",
                "sony pix", "star movies", "mn+", "hits", "romedy", "comedy central",
                "axn", "colors infinity", "zee café", "&flix", "&privé", "star world",
                "fox", "fyi", "tlc", "animal planet", "history tv18", "news", "bloomberg"]
}

SPORTS_KW = ["sports", "star sports", "sony ten", "eurosport", "dsport",
             "olympics", "cricket", "football", "tennis", "f1", "nba", "wwe"]

# Major Tamil entertainment channels → Tamil Entertainment (not Local)
MAJOR_TAMIL_ENT = {
    "sun tv", "star vijay", "vijay tv", "vijay super", "zee tamil",
    "colors tamil", "kalaignar tv", "jaya tv", "raj tv", "polimer tv",
    "puthuyugam tv", "dd podhigai", "vasanth tv", "d tamil", "eet tv"
}

# Domains that indicate a small local cable channel → Tamil Local
LOCAL_DOMAINS = {
    "galaxyott.live", "sscloud7.in", "sscloud7.com", "applelive.in",
    "maxtn.in", "olidigital.in", "rojatv.cloud", "thendralcloud.in",
    "singamcloud.in", "onecloudlive.in", "ipcloud.live", "notvstream.in",
    "livebox.co.in", "ashokadigital.net", "phoenixcreations.online",
    "7starcloud.com", "brightmeltech.in", "rcserver.in", "apserver.in",
    "bmlive.net", "mindspell.in", "yettelevision.com", "103.140.254.2",
    "103.87.105.51"
}

def clean_name(raw):
    raw = re.sub(r'\s*\[.*?\]\s*', '', raw)
    raw = re.sub(r'\s*\(.*?\)\s*', '', raw)
    raw = re.sub(r'\s*\b(HD|SD|HEVC|4K|UHD)\b\s*', '', raw, flags=re.I)
    return ' '.join(raw.split()).strip()

def has_blocked_words(text):
    """Return True if any blocked language word appears in the text."""
    if not text:
        return False
    lower = text.lower()
    for word in BLOCKED:
        if word in lower:
            return True
    return False

def detect_lang(name):
    n = name.lower()
    for kw in LANG_KW["tamil"]:
        if kw in n:
            return "tamil"
    for kw in LANG_KW["english"]:
        if kw in n:
            return "english"
    return None

def is_sports(name):
    return any(kw in name.lower() for kw in SPORTS_KW)

def is_local_domain(url):
    """Check if the URL's domain is in our known local cable list."""
    try:
        domain = urlparse(url).hostname
        return domain in LOCAL_DOMAINS
    except:
        return False

def detect_cat(name, url, group_title=""):
    """Return the appropriate category, or None if channel should be skipped."""
    # 1. Hard block on name or group-title
    if has_blocked_words(name) or has_blocked_words(group_title):
        return None

    n = name.lower()
    lang = detect_lang(name)

    # 2. Kids – allowed in any language
    if any(w in n for w in ["kids", "chutti", "chithiram", "cartoon", "disney",
                            "nick", "pogo", "motu patlu", "chhota bheem",
                            "scooby", "mr bean", "vir the robot"]):
        return "Tamil Kids"

    # 3. Sports
    if is_sports(name) and lang in ("tamil", "english"):
        return "Sports"

    # 4. Tamil
    if lang == "tamil":
        # Specific categories first
        if any(w in n for w in ["movie", "cinema", "ktv", "megahit", "thirai"]):
            return "Tamil Movies"
        if any(w in n for w in ["news", "seithigal", "pudhiya", "polimer news",
                                "sun news", "thanthi tv", "news18", "win news",
                                "news7", "news j"]):
            return "Tamil News"
        if any(w in n for w in ["music", "isai", "isaiaruvi", "sun music",
                                "mega music", "raj musix", "g music", "jcv musix"]):
            return "Tamil Music"

        # Major entertainment channels → Tamil Entertainment
        if any(major in n for major in MAJOR_TAMIL_ENT):
            return "Tamil Entertainment"

        # If URL indicates a local cable operator → Tamil Local
        if is_local_domain(url):
            return "Tamil Local"

        # Fallback for any other Tamil channel → Tamil Entertainment
        return "Tamil Entertainment"

    # 5. English
    if lang == "english":
        if any(w in n for w in ["news", "cnn", "bbc", "ndtv", "times now", "republic",
                                "wion", "sky news", "bloomberg"]):
            return "English News"
        if any(w in n for w in ["movie", "hbo", "star movies", "sony pix", "mn+",
                                "hits", "romedy", "comedy central", "&flix", "zee café"]):
            return "English Movies"
        # For English channels that are not movies or news, discard
        return None

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

            # Use the source group-title for blocking (if present)
            src_group = attrs.get("group-title", "")
            category = detect_cat(raw_name, url, src_group)
            if category is None:
                continue

            if category not in SKIP_URL_CHECK:
                if not check_url(url):
                    print(f"  ✗ Dead: {raw_name} ({category})")
                    continue

            new_attrs = dict(attrs)
            new_attrs["group-title"] = category
            channels[category][url] = (new_attrs, raw_name)
            print(f"  ✓ {raw_name} → {category}")

    # Write output
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
    main()    "telugu", "hindi", "marathi", "malayalam", "kannada", "bengali", "punjabi",
    "gujarati", "oriya", "assamese", "bhojpuri", "urdu", "sanskrit",
    "etv telugu", "gemini", "maa tv", "tv9 telugu", "tv9 marathi",
    "zee marathi", "zee talkies", "colors marathi", "star pravah",
    "asianet", "surya tv", "kiran", "flowers", "mazhavil", "kairali",
    "amrita", "dd malayalam", "dd telugu", "dd hindi", "dd bengali",
    "sangeet", "b4u", "aaj tak", "india today", "ndtv india",
    "sony sab", "sony pal", "star plus", "colors", "zee tv",
    "star utsav", "star gold", "sony max", "zee cinema", "&pictures",
    "sony wah", "star bharat", "dangal", "big magic", "dd national",
    "dd india", "lok sabha", "rajya sabha"
}

# ---------- LANGUAGE DETECTION KEYWORDS ----------
LANG_KW = {
    "tamil": ["tamil", "sun ", "vijay", "kalaignar", "jaya ", "raj ", "captain",
              "polimer", "mega ", "pudhiya", "thanthi", "vasanth", "isaiaruvi",
              "k tv", "ktv", "adithya", "chutti", "chithiram", "makkal", "sirippoli",
              "vendhar", "peppers", "angel", "murugan", "madha", "velicham", "seithigal",
              "podhigai", "puthiya", "thalaimurai", "sathiyam", "madhimugam"],
    "english": ["english", "hbo", "cnn", "bbc", "disney", "discovery", "nat geo",
                "sony pix", "star movies", "mn+", "hits", "romedy", "comedy central",
                "axn", "colors infinity", "zee café", "&flix", "&privé", "star world",
                "fox", "fyi", "tlc", "animal planet", "history tv18", "news", "bloomberg"]
}

SPORTS_KW = ["sports", "star sports", "sony ten", "eurosport", "dsport",
             "olympics", "cricket", "football", "tennis", "f1", "nba", "wwe"]

# Major Tamil entertainment channels → Tamil Entertainment (not Local)
MAJOR_TAMIL_ENT = {
    "sun tv", "star vijay", "vijay tv", "vijay super", "zee tamil",
    "colors tamil", "kalaignar tv", "jaya tv", "raj tv", "polimer tv",
    "puthuyugam tv", "dd podhigai", "vasanth tv", "d tamil", "eet tv"
}

# Domains that indicate a small local cable channel → Tamil Local
LOCAL_DOMAINS = {
    "galaxyott.live", "sscloud7.in", "sscloud7.com", "applelive.in",
    "maxtn.in", "olidigital.in", "rojatv.cloud", "thendralcloud.in",
    "singamcloud.in", "onecloudlive.in", "ipcloud.live", "notvstream.in",
    "livebox.co.in", "ashokadigital.net", "phoenixcreations.online",
    "7starcloud.com", "brightmeltech.in", "rcserver.in", "apserver.in",
    "bmlive.net", "mindspell.in", "yettelevision.com", "103.140.254.2",
    "103.87.105.51"
}

def clean_name(raw):
    raw = re.sub(r'\s*\[.*?\]\s*', '', raw)
    raw = re.sub(r'\s*\(.*?\)\s*', '', raw)
    raw = re.sub(r'\s*\b(HD|SD|HEVC|4K|UHD)\b\s*', '', raw, flags=re.I)
    return ' '.join(raw.split()).strip()

def has_blocked_words(text):
    """Return True if any blocked language word appears in the text."""
    if not text:
        return False
    lower = text.lower()
    for word in BLOCKED:
        if word in lower:
            return True
    return False

def detect_lang(name):
    n = name.lower()
    for kw in LANG_KW["tamil"]:
        if kw in n:
            return "tamil"
    for kw in LANG_KW["english"]:
        if kw in n:
            return "english"
    return None

def is_sports(name):
    return any(kw in name.lower() for kw in SPORTS_KW)

def is_local_domain(url):
    """Check if the URL's domain is in our known local cable list."""
    try:
        domain = urlparse(url).hostname
        return domain in LOCAL_DOMAINS
    except:
        return False

def detect_cat(name, url, group_title=""):
    """Return the appropriate category, or None if channel should be skipped."""
    # 1. Hard block on name or group-title
    if has_blocked_words(name) or has_blocked_words(group_title):
        return None

    n = name.lower()
    lang = detect_lang(name)

    # 2. Kids – allowed in any language
    if any(w in n for w in ["kids", "chutti", "chithiram", "cartoon", "disney",
                            "nick", "pogo", "motu patlu", "chhota bheem",
                            "scooby", "mr bean", "vir the robot"]):
        return "Tamil Kids"

    # 3. Sports
    if is_sports(name) and lang in ("tamil", "english"):
        return "Sports"

    # 4. Tamil
    if lang == "tamil":
        # Specific categories first
        if any(w in n for w in ["movie", "cinema", "ktv", "megahit", "thirai"]):
            return "Tamil Movies"
        if any(w in n for w in ["news", "seithigal", "pudhiya", "polimer news",
                                "sun news", "thanthi tv", "news18", "win news",
                                "news7", "news j"]):
            return "Tamil News"
        if any(w in n for w in ["music", "isai", "isaiaruvi", "sun music",
                                "mega music", "raj musix", "g music", "jcv musix"]):
            return "Tamil Music"

        # Major entertainment channels → Tamil Entertainment
        if any(major in n for major in MAJOR_TAMIL_ENT):
            return "Tamil Entertainment"

        # If URL indicates a local cable operator → Tamil Local
        if is_local_domain(url):
            return "Tamil Local"

        # Fallback for any other Tamil channel → Tamil Entertainment
        return "Tamil Entertainment"

    # 5. English
    if lang == "english":
        if any(w in n for w in ["news", "cnn", "bbc", "ndtv", "times now", "republic",
                                "wion", "sky news", "bloomberg"]):
            return "English News"
        if any(w in n for w in ["movie", "hbo", "star movies", "sony pix", "mn+",
                                "hits", "romedy", "comedy central", "&flix", "zee café"]):
            return "English Movies"
        # For English channels that are not movies or news, discard
        return None

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

            # Use the source group-title for blocking (if present)
            src_group = attrs.get("group-title", "")
            category = detect_cat(raw_name, url, src_group)
            if category is None:
                continue

            if category not in SKIP_URL_CHECK:
                if not check_url(url):
                    print(f"  ✗ Dead: {raw_name} ({category})")
                    continue

            new_attrs = dict(attrs)
            new_attrs["group-title"] = category
            channels[category][url] = (new_attrs, raw_name)
            print(f"  ✓ {raw_name} → {category}")

    # Write output
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
