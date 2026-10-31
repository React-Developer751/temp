"""Labelled examples the owner adds from the web UI ("this prompt is a bakery"). Stored in data/feedback.json of the repo checkout (web UI and
training are repo-only; the installed package never reads it) and used by the detector training."""
import json
import threading
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "data" / "feedback.json"
_lock = threading.Lock()


def load():
    try:
        rows = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [r for r in rows if isinstance(r, dict) and isinstance(r.get("prompt"), str) and isinstance(r.get("type"), str)]


def add(prompt, type_id):
    from .business_types import T
    prompt = " ".join(str(prompt).split())[:500]
    if not prompt or type_id not in T:
        raise ValueError("need a prompt and a known business type")
    with _lock:
        rows = load()
        rows = [r for r in rows if r["prompt"] != prompt] + [{"prompt": prompt, "type": type_id}]
        PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(rows)


def remove(prompt):
    with _lock:
        rows = [r for r in load() if r["prompt"] != prompt]
        PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(rows)


def pairs():
    return [(r["prompt"], r["type"]) for r in load()]
