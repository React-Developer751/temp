"""Local web UI for Core-Craft AI: write a prompt, see the page and the report, correct the business type, retrain the detector.
Run: python3 webui.py   then open http://127.0.0.1:8765   (stdlib only; listens on this computer only; repo checkout only, not in the package).

Guards (other web pages open in the same browser must not drive it): the Host header must be this server (127.0.0.1, localhost or [::1]
with its port: stops DNS rebinding); a POST/PUT/DELETE with a foreign Origin or `Sec-Fetch-Site: cross-site` is refused (CSRF); a JSON body
must say `Content-Type: application/json` (a cross-site form or text/plain post cannot); the generated preview is served sandboxed."""
import json
import re
import shutil
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "training"))
from corecraft import detector, feedback, pipeline   # noqa: E402
from corecraft.business_types import T   # noqa: E402

OUT = ROOT / "output" / "ui"
MAX_BODY = 200_000
LOCAL_HOSTS = ("127.0.0.1", "localhost", "[::1]")
PREVIEW_CSP = "sandbox allow-scripts"   # the preview runs in an opaque origin: it cannot call the API as this page
TRAIN_LOCK = threading.Lock()


def holdout_accuracy():
    from labelled import HOLDOUT
    detector._cache.pop("m", None)
    ok = sum(detector.detect(p)[0] == t for p, t in HOLDOUT)
    return ok, len(HOLDOUT)


def status():
    ok, n = holdout_accuracy()
    from labelled import TRAIN
    return {"feedback": feedback.load(), "holdout": [ok, n], "train_prompts": len(TRAIN),
            "types": sorted(({"id": k, "label": v["label"]} for k, v in T.items()), key=lambda x: x["label"])}


def generate(body):
    prompt = str(body.get("prompt", ""))
    facts = {k: v for k, v in (body.get("facts") or {}).items() if v}
    if isinstance(facts.get("services"), str):
        facts["services"] = [x.strip() for x in facts["services"].split(",") if x.strip()]
    seed = body.get("seed")
    seed = int(seed) if str(seed or "").lstrip("-").isdigit() else None
    shutil.rmtree(OUT, ignore_errors=True)
    r = pipeline.run(prompt, str(OUT), seed, facts or None, body.get("lang") or None)
    c = json.loads((Path(r["dir"]) / "content.json").read_text(encoding="utf-8"))
    tid, conf, det = detector.detect(" ".join(prompt.split()))
    slug = Path(r["dir"]).name
    return {"preview": "/site/%s/preview.html" % slug, "brand": c["brand"], "type": c["business_type"], "type_label": c["type_label"], "profile": c["profile"], "lang": c["lang"],
            "confidence": conf, "detected": tid, "location": c["location"], "hero": c["hero_heading"], "tagline": c["tagline"], "hours": c["hours"],
            "services": c["generated_by"]["items_from_prompt"], "offers": [o["text"] for o in c["offers"]], "missing": c["missing"], "needs_review": c["needs_review"],
            "contact": c["contact"], "files": r["files"]}


def train():
    """Retrain the detector on the shipped labels + the owner's corrections. Kept only if hold-out accuracy does not drop."""
    import train_detector
    with TRAIN_LOCK:
        mp = detector.MODEL_PATH
        backup = mp.read_bytes() if mp.exists() else None
        before = holdout_accuracy()
        train_detector.main(verbose=False)
        after = holdout_accuracy()
        kept = after[0] >= before[0] - 1   # a one-prompt wobble is tolerated; a real drop is rolled back
        if not kept:
            if backup is not None:
                mp.write_bytes(backup)
            detector._cache.pop("m", None)
            after = holdout_accuracy()
        return {"before": before, "after": after, "kept": kept, "examples": len(feedback.load())}


class Handler(BaseHTTPRequestHandler):
    server_version = "CoreCraft"

    def log_message(self, *a):
        pass

    def send(self, code, data, ctype="application/json; charset=utf-8", csp=None):
        raw = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")   # no other site may frame the UI (clickjacking the Train button)
        if csp:
            self.send_header("Content-Security-Policy", csp)
        self.end_headers()
        self.wfile.write(raw)

    def origins(self):
        port = self.server.server_address[1]
        return {"%s:%d" % (h, port) for h in LOCAL_HOSTS}

    def refusal(self, state_changing=False):
        """Why a request from anywhere but this UI is refused (wrong Host: DNS rebinding; foreign Origin or cross-site fetch: CSRF), or None."""
        if (self.headers.get("Host") or "").strip().lower() not in self.origins():
            return "wrong host"
        if state_changing:
            origin = self.headers.get("Origin")
            if origin is not None and origin.strip().lower() not in {"http://" + h for h in self.origins()}:
                return "cross-origin request refused"
            if (self.headers.get("Sec-Fetch-Site") or "").strip().lower() == "cross-site":
                return "cross-site request refused"
        return None

    def refused(self, state_changing=False):
        why = self.refusal(state_changing)
        if why:
            self.send(403, {"error": why})
        return why

    def do_GET(self):
        if self.refused():
            return
        path = unquote(urlparse(self.path).path)
        if path == "/":
            return self.send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/api/status":
            return self.send(200, status())
        if path.startswith("/site/"):
            f = (OUT / path[len("/site/"):]).resolve()
            if OUT.resolve() in f.parents and f.is_file():
                ctype = {".html": "text/html; charset=utf-8", ".css": "text/css", ".svg": "image/svg+xml", ".json": "application/json", ".jsx": "text/plain; charset=utf-8", ".png": "image/png",
                         ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(f.suffix, "application/octet-stream")
                return self.send(200, f.read_bytes(), ctype, csp=PREVIEW_CSP)
        self.send(404, {"error": "not found"})

    def do_PUT(self):
        if not self.refused(state_changing=True):
            self.send(405, {"error": "method not allowed"})

    do_DELETE = do_PATCH = do_PUT

    def do_POST(self):
        if self.refused(state_changing=True):
            return
        try:
            length = (self.headers.get("Content-Length") or "0").strip()
            if not (length.isascii() and length.isdigit()):   # "-1" would make rfile.read() read to the end, past MAX_BODY
                return self.send(400, {"error": "bad Content-Length"})
            n = int(length)
            if n > MAX_BODY:
                return self.send(413, {"error": "request too large"})
            if (self.headers.get("Content-Type") or "").split(";")[0].strip().lower() != "application/json":   # also for an empty body
                return self.send(415, {"error": "send JSON with Content-Type: application/json"})
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
            except (ValueError, UnicodeDecodeError):
                return self.send(400, {"error": "the request body is not valid JSON"})
            if not isinstance(body, dict):
                raise ValueError("expected a JSON object")
            if self.path == "/api/generate":
                return self.send(200, generate(body))
            if self.path == "/api/feedback":
                return self.send(200, {"count": feedback.add(body.get("prompt", ""), body.get("type", ""))})
            if self.path == "/api/feedback/remove":
                return self.send(200, {"count": feedback.remove(body.get("prompt", ""))})
            if self.path == "/api/pack":
                from corecraft.pack_api import generate_pack
                return self.send(200, generate_pack(str(body.get("request", ""))))
            if self.path == "/api/train":
                return self.send(200, train())
            self.send(404, {"error": "not found"})
        except ValueError as e:   # the engine's own messages for bad input (empty prompt, unknown type)
            self.send(400, {"error": str(e)})
        except Exception:   # never leak a traceback to the page
            traceback.print_exc()
            self.send(500, {"error": "something went wrong; see the terminal"})


PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Core-Craft AI</title>
<style>
:root{--bg:#f6f5f2;--card:#fff;--ink:#1d1d1b;--mute:#6b6a65;--line:#e2e0da;--acc:#2f5d50;--warn:#9a5b00;--bad:#a12d2d}
@media(prefers-color-scheme:dark){:root{--bg:#161615;--card:#1f1f1d;--ink:#eceae4;--mute:#a2a098;--line:#33322f;--acc:#7fc0ad;--warn:#e0a24a;--bad:#e27b7b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}
header{padding:14px 20px;border-bottom:1px solid var(--line);display:flex;gap:16px;align-items:center;flex-wrap:wrap}
h1{font-size:18px;margin:0}nav button{background:none;border:0;color:var(--mute);padding:6px 10px;font:inherit;cursor:pointer;border-bottom:2px solid transparent}
nav button.on{color:var(--ink);border-color:var(--acc)}
main{display:grid;grid-template-columns:minmax(300px,380px) 1fr;gap:16px;padding:16px 20px}
@media(max-width:860px){main{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
label{display:block;font-size:12px;color:var(--mute);margin:10px 0 3px}textarea,input,select{width:100%;padding:8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink);font:inherit}
textarea{min-height:110px;resize:vertical}.row{display:grid;grid-template-columns:1fr 1fr;gap:8px}
button.go{margin-top:12px;width:100%;padding:10px;background:var(--acc);color:var(--bg);border:0;border-radius:6px;font:inherit;font-weight:600;cursor:pointer}
button.go:disabled{opacity:.5}button.sm{padding:5px 10px;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;cursor:pointer;font:inherit}
iframe{width:100%;height:70vh;border:1px solid var(--line);border-radius:8px;background:#fff}
.tag{display:inline-block;padding:1px 8px;border-radius:99px;border:1px solid var(--line);font-size:12px;margin:0 4px 4px 0}
.high{color:var(--acc)}.medium{color:var(--warn)}.low{color:var(--bad)}.warn{color:var(--warn)}.bad{color:var(--bad)}.mute{color:var(--mute)}
dl{display:grid;grid-template-columns:110px 1fr;gap:4px 10px;margin:0}dt{color:var(--mute)}dd{margin:0;overflow-wrap:anywhere}
table{width:100%;border-collapse:collapse}td{padding:6px 4px;border-top:1px solid var(--line);vertical-align:top;overflow-wrap:anywhere}
.hide{display:none}h2{font-size:15px;margin:0 0 8px}
</style></head><body>
<header><h1>Core-Craft AI</h1><nav><button id="t-gen" class="on">Generate &amp; check</button><button id="t-pack">Content pack</button><button id="t-train">Train</button></nav><span class="mute" id="stat"></span></header>
<main id="gen">
 <section class="card"><label for="prompt">Describe the business (English, Hinglish or Hindi)</label>
  <textarea id="prompt" placeholder="Italian restaurant Forno Rosso, Mumbai, wood fired pizza, fresh pasta, tiramisu, open 12pm to 11pm, online booking"></textarea>
  <details><summary class="mute">Real details (optional, these win over the prompt)</summary>
   <div class="row"><div><label for="f-name">Name</label><input id="f-name"></div><div><label for="f-city">City</label><input id="f-city"></div></div>
   <div class="row"><div><label for="f-phone">Phone</label><input id="f-phone"></div><div><label for="f-email">Email</label><input id="f-email"></div></div>
   <label for="f-address">Address</label><input id="f-address"><label for="f-services">Services (comma separated)</label><input id="f-services">
   <div class="row"><div><label for="seed">Seed (optional)</label><input id="seed" inputmode="numeric"></div><div><label for="lang">Language</label><select id="lang"><option value="">auto</option><option value="en">English</option><option value="hi">Hindi</option></select></div></div>
  </details><button class="go" id="go">Generate</button><p id="err" class="bad"></p></section>
 <section id="out" class="hide"><div class="card" style="margin-bottom:16px"><h2>Report</h2><dl id="rep"></dl><div id="notes" style="margin-top:10px"></div>
   <div style="margin-top:12px" class="row"><select id="fix" aria-label="Correct business type"></select><button class="sm" id="save">Wrong type? Save as training example</button></div><p id="saved" class="mute"></p></div>
  <iframe id="pv" title="Page preview" sandbox="allow-scripts"></iframe></section>
</main>
<main id="pk" class="hide" style="grid-template-columns:minmax(300px,380px) 1fr">
 <section class="card"><label for="req">What would a person type? (English, Hinglish)</label>
  <textarea id="req" placeholder="Create a website for a pest control in Jaipur&#10;mujhe termite treatment ki website banakar do"></textarea><button class="go" id="mk">Write the content pack</button><p id="perr" class="bad"></p>
  <p class="mute">The pack follows the Content AI training spec: 3 hero titles, 6 features, 4 steps, 5 FAQ, pricing, gallery, team, testimonials, blog, marquee (and a menu for food).</p></section>
 <section class="card"><h2>Understood</h2><dl id="pu"></dl><div id="pn" style="margin:8px 0"></div><h2>Pack (JSON)</h2><pre id="pj" style="white-space:pre-wrap;max-height:60vh;overflow:auto;font-size:12px"></pre></section>
</main>
<main id="trn" class="hide" style="grid-template-columns:1fr">
 <section class="card"><h2>Detector training</h2><p class="mute" id="tinfo"></p><button class="go" id="train" style="max-width:320px">Train on my corrections</button><p id="tres"></p>
  <p class="mute">Training runs on this computer only (no internet). The new model is kept only if its score on the held-out prompts does not drop; otherwise the old one is restored.</p></section>
 <section class="card"><h2>My corrections</h2><table id="fb"></table></section>
</main>
<script>
const $=id=>document.getElementById(id);let last="",types=[];
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
async function api(p,b){const r=await fetch(p,b===undefined?{}:{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)});const j=await r.json();if(!r.ok)throw new Error(j.error||r.status);return j}
function tab(n){$("pk").classList.toggle("hide",n!=="pk");$("t-pack").classList.toggle("on",n==="pk");$("gen").classList.toggle("hide",n!=="gen");$("trn").classList.toggle("hide",n!=="trn");$("t-gen").classList.toggle("on",n==="gen");$("t-train").classList.toggle("on",n==="trn");if(n==="trn")refresh()}
$("t-pack").onclick=()=>tab("pk");$("mk").onclick=async()=>{$("perr").textContent="";$("mk").disabled=true;try{const r=await api("/api/pack",{request:$("req").value});const u=r.understood;
 $("pu").innerHTML=[["Source",esc(r.source)],["Niche",esc(u.niche||u.type_theme||"-")],["Brand",esc(u.brand||"not given: {brand} stays")],["City",esc(u.city||"not given")],["Language",esc(u.lang)],["Spec check",r.problems.length?'<span class="bad">'+esc(r.problems.join("; "))+"</span>":'<span class="high">0 problems</span>']].map(x=>`<dt>${x[0]}</dt><dd>${x[1]}</dd>`).join("");
 $("pn").innerHTML=r.notes.map(n=>`<div class="warn">• ${esc(n)}</div>`).join("");$("pj").textContent=JSON.stringify(r.pack,null,2)}catch(e){$("perr").textContent=e.message}finally{$("mk").disabled=false}};
$("t-gen").onclick=()=>tab("gen");$("t-train").onclick=()=>tab("trn");
async function refresh(){const s=await api("/api/status");types=s.types;
 $("stat").textContent="held-out detection: "+s.holdout[0]+"/"+s.holdout[1]+" ("+Math.round(100*s.holdout[0]/s.holdout[1])+"%)";
 const cur=$("fix").value;$("fix").innerHTML=types.map(t=>`<option value="${esc(t.id)}">${esc(t.label)}</option>`).join("");if(cur)$("fix").value=cur;
 $("tinfo").textContent=s.train_prompts+" shipped training prompts + "+s.feedback.length+" of your corrections.";
 $("fb").innerHTML=s.feedback.length?s.feedback.map((r,i)=>`<tr><td>${esc(r.prompt)}</td><td>${esc(r.type)}</td><td><button class="sm" data-i="${i}">remove</button></td></tr>`).join(""):"<tr><td class='mute'>None yet. Generate a page, and if the type is wrong, pick the right one and save it.</td></tr>";
 document.querySelectorAll("#fb button").forEach(b=>b.onclick=async()=>{await api("/api/feedback/remove",{prompt:s.feedback[b.dataset.i].prompt});refresh()})}
$("go").onclick=async()=>{$("err").textContent="";$("go").disabled=true;$("go").textContent="Generating...";
 try{last=$("prompt").value;const r=await api("/api/generate",{prompt:last,seed:$("seed").value,lang:$("lang").value,facts:{name:$("f-name").value,city:$("f-city").value,phone:$("f-phone").value,email:$("f-email").value,address:$("f-address").value,services:$("f-services").value}});
  $("out").classList.remove("hide");$("pv").src=r.preview+"?t="+Date.now();
  const rows=[["Business",`${esc(r.brand)} <span class="mute">(${esc(r.lang)})</span>`],["Type",`${esc(r.type_label)} <span class="tag ${r.confidence}">${r.confidence} confidence</span>`],["City",esc(r.location||"not given")],["Hours",esc(r.hours||"not given")],
   ["Services",r.services.map(s=>`<span class="tag">${esc(s)}</span>`).join("")||"none read"],["Offers",r.offers.map(s=>`<span class="tag">${esc(s)}</span>`).join("")||"none"],["Headline",esc(r.hero)],["Missing",esc(r.missing.join(", ")||"nothing")]];
  $("rep").innerHTML=rows.map(x=>`<dt>${x[0]}</dt><dd>${x[1]}</dd>`).join("");
  $("notes").innerHTML=r.needs_review.map(n=>`<div class="warn">• ${esc(n)}</div>`).join("")||'<div class="high">No review notes.</div>';
  $("saved").textContent="";if(r.detected)$("fix").value=r.detected;
 }catch(e){$("err").textContent=e.message}finally{$("go").disabled=false;$("go").textContent="Generate"}};
$("save").onclick=async()=>{try{const r=await api("/api/feedback",{prompt:last,type:$("fix").value});$("saved").textContent="Saved ("+r.count+" corrections). Open the Train tab to retrain."}catch(e){$("saved").textContent=e.message}};
$("train").onclick=async()=>{$("train").disabled=true;$("tres").textContent="Training... (about 15 seconds)";
 try{const r=await api("/api/train",{});$("tres").innerHTML=`Held-out: ${r.before[0]}/${r.before[1]} → ${r.after[0]}/${r.after[1]}. `+(r.kept?'<span class="high">New model kept.</span>':'<span class="bad">Score dropped, so the previous model was restored.</span>')+` (${r.examples} corrections used)`;refresh()}
 catch(e){$("tres").textContent=e.message}finally{$("train").disabled=false}};
refresh();
</script></body></html>"""


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("Core-Craft AI UI: http://127.0.0.1:%d   (Ctrl+C to stop)" % port)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
