"""Fetch real sites with urllib and extract visible copy by slot using html.parser (stdlib only)."""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sources import SOURCES

UA = {"User-Agent": "Mozilla/5.0 (compatible; CoreCraftTrainer/1.0; research)"}
SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "form", "select", "option", "head", "iframe"}
LINK_HINT = re.compile(r"/(about|services|menu|features|products|programs|courses|solutions|why|our-story|classes|learn|pricing|plans|benefits|how-it-works|team|stories|locations|catalog|collections|resources)\b", re.I)


class Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth_skip = 0
        self.stack = []
        self.buf = []
        self.out = {"heading": [], "para": [], "cta": [], "title": [], "meta": []}
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in SKIP:
            self.depth_skip += 1
        if tag == "meta" and (a.get("name") or "").lower() in ("description",) or a.get("property") == "og:description":
            if a.get("content"):
                self.out["meta"].append(a["content"])
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag in ("h1", "h2", "h3", "p", "button", "a", "title", "li"):
            self.stack.append(tag)
            self.buf = []

    def handle_endtag(self, tag):
        if tag in SKIP and self.depth_skip:
            self.depth_skip -= 1
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
            text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
            self.buf = []
            if not text or self.depth_skip:
                return
            if tag in ("h1", "h2", "h3"):
                self.out["heading"].append(text)
            elif tag in ("p", "li"):
                self.out["para"].append(text)
            elif tag in ("button", "a"):
                self.out["cta"].append(text)
            elif tag == "title":
                self.out["title"].append(text)

    def handle_data(self, data):
        if self.stack and not self.depth_skip:
            self.buf.append(data)


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15) as r:
        if "html" not in r.headers.get("Content-Type", ""):
            return ""
        return r.read(1_500_000).decode(r.headers.get_content_charset() or "utf-8", "replace")


def clean(items, lo, hi):
    seen, res = set(), []
    for t in items:
        t = t.strip()
        words = t.split()
        if lo <= len(words) <= hi and re.search(r"[A-Za-z]{3}", t) and not re.search(r"https?:|@|©|cookie|privacy|javascript|\{|\}|<|>", t, re.I) and t.lower() not in seen:
            seen.add(t.lower())
            res.append(t)
    return res


def brand_of(url):
    host = urllib.parse.urlparse(url).netloc.lower().split(".")
    host = [h for h in host if h not in ("www", "com", "co", "uk", "org", "net", "io", "life")]
    return host[0] if host else ""


def crawl(site, max_pages=10):
    pages, queue, done = [], [site], set()
    host = urllib.parse.urlparse(site).netloc
    while queue and len(done) < max_pages:
        u = queue.pop(0)
        if u in done:
            continue
        done.add(u)
        try:
            html_text = get(u)
        except Exception as e:
            print("   skip", u, type(e).__name__)
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
    path = Path(__file__).parent.parent / "data" / "corpus.json"
    corpus = json.loads(path.read_text()) if path.exists() else {}
    done_path = path.parent / "done_sites.json"
    done = set(json.loads(done_path.read_text())) if done_path.exists() else set()
    only = sys.argv[1:] or list(SOURCES)
    for niche in only:
        sites = [u for u in SOURCES[niche] if u not in done]
        corpus.setdefault(niche, {"heading": [], "para": [], "cta": [], "meta": [], "sites_ok": 0})
        base = corpus[niche]
        agg = {"heading": list(base["heading"]), "para": list(base["para"]), "cta": list(base["cta"]), "meta": [], "sites_ok": base.get("sites_ok", 0)}
        for s in sites:
            pages = crawl(s)
            brand = brand_of(s)
            got = 0
            for p in pages:
                nb = lambda xs: [x for x in xs if not (len(brand) >= 4 and brand in re.sub(r"[^a-z]", "", x.lower())) and "■" not in x and "button-" not in x]
                agg["heading"] += nb(clean(p["heading"], 2, 9))
                agg["para"] += nb(clean(p["para"] + p["meta"], 8, 45))
                agg["cta"] += clean(p["cta"], 1, 4)
                got += len(p["heading"]) + len(p["para"])
            agg["sites_ok"] += 1 if got else 0
            print(niche, s, "->", got)
            done.add(s)
            done_path.write_text(json.dumps(sorted(done)))
            path.write_text(json.dumps({**corpus, niche: {**agg, "sites_ok": agg["sites_ok"]}}, indent=1, ensure_ascii=False), encoding="utf-8")
        for k in ("heading", "para", "cta"):
            agg[k] = list(dict.fromkeys(agg[k]))
        corpus[niche] = agg
        print("==", niche, {k: len(v) for k, v in agg.items() if isinstance(v, list)}, "sites_ok", agg["sites_ok"])
    path.write_text(json.dumps(corpus, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
