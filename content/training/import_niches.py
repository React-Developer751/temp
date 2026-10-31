"""Read the owner's "Content AI: training prompts" PDF (stdlib only) and write corecraft/data/niche_spec.json: the 99 niches (id, label, theme, keywords, the 6 services,
the 6 ways people ask for it) and the 20 business types. Then run training/build_niches.py to refresh corecraft/data/niches.json. Run: python3 training/import_niches.py /path/to/Content-AI-training.pdf  (or data/niche_spec_source.txt, the text already extracted from it)"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIG = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}
# the PDF lists these services with a comma inside one service name; the spec says 6 per niche
MERGE = {"mobile_repair": ("Speaker", "Mic And Camera Fix"), "cloud_kitchen": ("Multiple Brands", "One Kitchen"), "kirana_grocery": ("Dairy", "Bread And Eggs"),
         "mobile_phone_store": ("Cases", "Chargers", "Earbuds"), "tailoring_alterations": ("Shirts", "Pants And Suits"), "travel_cab_taxi": ("Sedans", "SUVs And Tempo Vans"),
         "plumber_electrician": ("Fan", "Light And Geyser Fitting")}
REQ = re.compile(r"^(.*?) website Create a website for a (.*?) in Jaipur mujhe (.*?) ki website banakar do meri (.*?) ki dukaan ke liye website banao, with online contact and WhatsApp "
                 r"modern (.*?) website with animation, premium colours and a gallery (.*?) landing page, short, with pricing and FAQ$")


def pdf_to_text(path):
    if path.endswith(".txt"):
        return Path(path).read_text(encoding="utf-8")   # text already pulled out of the PDF (data/niche_spec_source.txt)
    out = subprocess.run([sys.executable, str(Path(__file__).with_name("pdf_text.py")), path], capture_output=True, text=True, check=True).stdout
    return out


def parse(text):
    for a, b in LIG.items():
        text = text.replace(a, b)
    flat = re.sub(r"\s+", " ", text.replace("=====PAGE=====", "\n").replace("\x00", "~"))
    body = flat[flat.index("2. Business prompts (99)"):]
    niches, types = [], []
    for b in (x.strip() for x in body.split("Return the JSON object only.")):
        if not b:
            continue
        m = re.search(r"([A-Z].{1,80}?) \(([a-z][a-z_0-9]*) · ([a-z_]+)\) What people will type (.*?) Prompt Write the website content pack", b)
        if m:
            bt = re.search(r'for this business: "(.*?)" \(business type: (.*?)\)\.', b)
            kw = re.search(r"Words people use to ask for it: (.*?)\. Cover these services", b)
            sv = re.search(r'in this spirit\): (.*?)\. Follow the system', b)
            services = [x.strip() for x in sv.group(1).split(". It is a food")[0].split(",")]
            nid = m.group(2)
            if nid in MERGE:
                k = MERGE[nid]
                i = services.index(k[0])
                services[i:i + len(k)] = [", ".join(k)]
            rq = REQ.match(m.group(4).strip())
            niches.append({"id": nid, "label": bt.group(1), "theme": m.group(3), "business_type": bt.group(2), "services": services,
                           "keywords": [k.strip() for k in kw.group(1).split(",") if k.strip() and "~" not in k], "requests": list(rq.groups()) if rq else [],
                           "food": 'add the "menu" block' in b})
            continue
        m = re.search(r"(.{3,80}?) \(theme:([a-z_]+) · ([a-z_]+)\) What people will type (.*?) Prompt Write the general website content pack for any business of this type: (.*?)\. It is the fallback", b)
        if m:
            types.append({"theme": m.group(2), "type_text": m.group(5), "requests": m.group(4).strip()})
    return niches, types


def main():
    niches, types = parse(pdf_to_text(sys.argv[1]))
    assert len(niches) == 99 and len(types) == 20, (len(niches), len(types))
    assert all(len(n["services"]) == 6 and len(n["requests"]) == 6 for n in niches), [n["id"] for n in niches if len(n["services"]) != 6 or len(n["requests"]) != 6]
    (ROOT / "corecraft" / "data" / "niche_spec.json").write_text(json.dumps({"niches": niches, "types": types}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("niches", len(niches), "| types", len(types), "| requests", sum(len(n["requests"]) for n in niches))


if __name__ == "__main__":
    main()
