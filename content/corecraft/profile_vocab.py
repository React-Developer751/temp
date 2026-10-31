"""Learned vocabulary per profile (corecraft/data/profile_vocab.json, built by training/train_templates.py from real public pages).
Used softly when choosing the sub-niche: words such as 'mascarpone' or 'sambar' count for Italian or South Indian even when the
prompt names no cuisine."""
import json
from pathlib import Path

PATH = Path(__file__).resolve().parent / "data" / "profile_vocab.json"
_cache = {}


def load():
    if "v" not in _cache:
        _cache["v"] = json.loads(PATH.read_text(encoding="utf-8")) if PATH.exists() else {}
    return _cache["v"]


def learned_score(profile, words, cap=3.0):
    vocab = load().get(profile, {})
    return min(cap, sum(vocab.get(w, 0.0) for w in set(words)) * 4.0)
