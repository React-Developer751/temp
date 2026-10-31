"""Niche registry. Each niche is a scene function ``scene(S)`` (see studio/stage.py) plus what the prompt matcher needs."""
from dataclasses import dataclass, field

NICHES = {}


@dataclass
class Niche:
    id: str
    title: str
    fn: object
    subjects: tuple              # prop / subject names that must be visible (declared with put(subject=True) or mark_subject)
    strong: tuple                # words / phrases that name this business (English, Hinglish, Devanagari)
    weak: tuple                  # words that only hint at it
    accent: str                  # default accent colour
    mood: str                    # default mood
    group: str
    avoid: tuple = ()            # words that mean "this is NOT it" (e.g. "dental" for a generic clinic)


def niche(id, title, subjects, strong, weak=(), accent="#c0392b", mood="warm", group="", avoid=()):
    def deco(fn):
        if id in NICHES:
            raise ValueError("duplicate niche id %s" % id)
        NICHES[id] = Niche(id, title, fn, tuple(subjects), tuple(strong), tuple(weak), accent, mood, group, tuple(avoid))
        return fn
    return deco


def load_all():
    """Import every niche module (they register themselves)."""
    import importlib
    import pkgutil
    for m in pkgutil.iter_modules(__path__):
        importlib.import_module("%s.%s" % (__name__, m.name))
    from .. import vocab
    vocab.apply(NICHES)                                        # idempotent: only adds words that are not there yet
    return NICHES
