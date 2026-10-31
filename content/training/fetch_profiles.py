"""Fetch public pages for each profile with urllib + html.parser (stdlib only), obeying robots.txt.
Text is cleaned before it is stored: brand names, phone numbers, e-mails, URLs, prices and street addresses are removed.
About one site in five is written to data/profile_holdout.json and is never used for training."""
import json
import re
import socket
import sys
import time
import urllib.parse
import urllib.request
import urllib.robotparser
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fetch_corpus import Extractor, LINK_HINT, UA   # noqa: E402
from sources_profiles import PROFILE_SOURCES   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TRAIN_PATH, HOLDOUT_PATH = ROOT / "data" / "profile_corpus.json", ROOT / "data" / "profile_holdout.json"
UA_NAME = "CoreCraftTrainer"
socket.setdefaulttimeout(12)   # robots.txt reads and page fetches must never hang
PHONE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
URL = re.compile(r"(?:https?://|www\.)\S+")
PRICE = re.compile(r"(?:₹|Rs\.?|INR|\$|£|€)\s?\d[\d,.]*")
ADDRESS = re.compile(r"\b(?:road|street|st\.|avenue|lane|nagar|floor|sector|plot|pin|pincode|postcode|po box)\b|\b\d{5,6}\b", re.I)
_robots = {}


def is_holdout(url):
    return zlib.crc32(urllib.parse.urlparse(url).netloc.encode()) % 5 == 0


def allowed(url):
    host = urllib.parse.urlparse(url)
    base = "%s://%s" % (host.scheme, host.netloc)
    if base not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(base + "/robots.txt")
        try:
            rp.read()
        except Exception:
            rp = None   # robots.txt unreachable: treat as no restrictions
        _robots[base] = rp
    rp = _robots[base]
    return True if rp is None else rp.can_fetch(UA_NAME, url)


def polite_get(url):
    if not allowed(url):
        return ""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; %s/1.0; research)" % UA_NAME})
    with urllib.request.urlopen(req, timeout=15) as r:
        if "html" not in r.headers.get("Content-Type", ""):
            return ""
        return r.read(1_500_000).decode(r.headers.get_content_charset() or "utf-8", "replace")


def brand_words(url):
    host = [h for h in urllib.parse.urlparse(url).netloc.lower().split(".") if h not in ("www", "com", "co", "uk", "org", "net", "in", "io", "au")]
    return {re.sub(r"[^a-z]", "", host[0])} if host else set()


def clean_text(t, brands):
    t = URL.sub(" ", EMAIL.sub(" ", t))
    if PHONE.search(t) or ADDRESS.search(t) or PRICE.search(t):
        return ""
    low = re.sub(r"[^a-z]", "", t.lower())
    if any(len(b) >= 4 and b in low for b in brands):
        return ""
    if re.search(r"cookie|privacy|terms|log ?in|sign ?up|javascript|©|subscribe|newsletter", t, re.I):
        return ""
    return t.strip()


def crawl(site, max_pages=8):
    pages, queue, done, host = [], [site], set(), urllib.parse.urlparse(site).netloc
    while queue and len(done) < max_pages:
        u = queue.pop(0)
        if u in done:
            continue
        done.add(u)
        try:
            html_text = polite_get(u)
        except Exception as e:
            print("   skip", u, type(e).__name__, flush=True)
            continue
        if not html_text:
            continue
        ex = Extractor()
        try:
            ex.feed(html_text)
        except Exception:
            pass
        pages.append(ex.out)
        for l in ex.links:
            full = urllib.parse.urljoin(u, l.split("#")[0])
            if urllib.parse.urlparse(full).netloc == host and LINK_HINT.search(full) and full not in done and full not in queue:
                queue.append(full)
        time.sleep(1)
    return pages


def main():
    only = sys.argv[1:] or list(PROFILE_SOURCES)
    stores = {p: (json.loads(p.read_text()) if p.exists() else {}) for p in (TRAIN_PATH, HOLDOUT_PATH)}
    done_path = ROOT / "data" / "profile_done.json"
    done = set(json.loads(done_path.read_text())) if done_path.exists() else set()
    for profile in only:
        for site in PROFILE_SOURCES[profile]:
            if site in done:
                continue
            store_path = HOLDOUT_PATH if is_holdout(site) else TRAIN_PATH
            store = stores[store_path]
            entry = store.setdefault(profile, {"heading": [], "para": [], "title": [], "sites": []})
            brands = brand_words(site)
            got = 0
            for p in crawl(site):
                for key, lo, hi in (("heading", 1, 9), ("para", 6, 45), ("title", 1, 12)):
                    for t in p.get(key, []):
                        t = clean_text(t, brands)
                        if t and lo <= len(t.split()) <= hi and re.search(r"[A-Za-z]{3}", t) and t not in entry[key]:
                            entry[key].append(t)
                            got += 1
            entry["sites"].append({"site": urllib.parse.urlparse(site).netloc, "texts": got})
            done.add(site)
            done_path.write_text(json.dumps(sorted(done)))
            store_path.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
            print(profile, "HOLDOUT" if store_path == HOLDOUT_PATH else "train", site, "->", got, flush=True)


if __name__ == "__main__":
    main()
