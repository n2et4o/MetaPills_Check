"""
Vérifie que fr.json et en.json ont exactement les mêmes clés et les mêmes {variables}.
Usage : python scripts/check_locales.py   (code de sortie 1 en cas d'écart)
"""
import json
import re
import sys
from pathlib import Path

LOCALES = Path(__file__).resolve().parent.parent / "locales"


def flatten(d: dict, prefix: str = "") -> dict:
    """{'a': {'b': 'x'}} -> {'a.b': 'x'}"""
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        out.update(flatten(v, key + ".") if isinstance(v, dict) else {key: v})
    return out


def placeholders(text: str) -> set:
    return set(re.findall(r"\{(\w+)\}", text))


fr = flatten(json.loads((LOCALES / "fr.json").read_text(encoding="utf-8")))
en = flatten(json.loads((LOCALES / "en.json").read_text(encoding="utf-8")))

errors = [f"absente de en.json : {k}" for k in sorted(fr.keys() - en.keys())]
errors += [f"absente de fr.json : {k}" for k in sorted(en.keys() - fr.keys())]
errors += [f"variables différentes pour {k} : fr={placeholders(fr[k])} en={placeholders(en[k])}"
           for k in sorted(fr.keys() & en.keys()) if placeholders(fr[k]) != placeholders(en[k])]

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"OK : {len(fr)} clés, identiques en français et en anglais.")
