"""Turn extracted client icons (64px) into the crisp 128px assets/icf/*.png used by the class decks.

  python scripts/make_icons.py

Inputs: $DB2_CACHE/../icf/<FileDataID>.png from scripts/extract-icons.ts, the forevertalent public folder for the few
icons the client has no file name for, and its class emblems. Writes assets/icf/<key>.png for every key in data/classes.json.
"""
import json
import os
import shutil
import sys

from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
TEMP = os.environ.get("TEMP", "/tmp")
EXTRACTED = os.environ.get("ICON_DIR", os.path.join(TEMP, "icf"))
PUB = os.environ.get("FOREVERTALENT_PUBLIC", r"E:\Dropbox\GitHub\Repos\forevertalent\public")
OUT = os.path.join(ROOT, "assets", "icf")
os.makedirs(OUT, exist_ok=True)

data = json.load(open(os.path.join(ROOT, "data", "classes.json"), encoding="utf-8"))
keys = set()
for c in data["classes"].values():
    keys.add(c["emblem"])
    for tr in c["trees"]:
        keys.update(t["img"] for t in tr["talents"] if t["img"])
    for a in c["abilities"]:
        keys.update(r["img"] for r in a["ranks"])
    for r in c["races"]:
        keys.update(a["img"] for a in r["abilities"] if a["img"])
for p in data["shared"]["professions"]:
    keys.add(p["img"])
    keys.update(b["img"] for b in p["bonuses"] if b["img"])
EXTRA_FIDS = ['135966', '133971', '136245']  # First Aid, Cooking, Fishing (not in professions.json)
keys.update(EXTRA_FIDS)
keys.discard(None)


def up(im, size=128):
    im = im.convert("RGB").resize((size, size), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.6, 55, 2))
    return im.quantize(256, method=Image.MEDIANCUT, dither=Image.NONE)


missing = []
for k in sorted(keys):
    dst = os.path.join(OUT, k + ".png")
    src = None
    if k.isdigit():
        src = os.path.join(EXTRACTED, k + ".png")
    elif k.startswith("e_"):
        src = os.path.join(PUB, "classes", k[2:] + ".jpg")
    elif k.startswith("n_"):
        n = k[2:]
        for cand in (("icons", "wow", "large", n + ".jpg"), ("abilities", n + ".jpg"), ("icons", "wow", "medium", n + ".jpg")):
            p = os.path.join(PUB, *cand)
            if os.path.exists(p):
                src = p
                break
    if not src or not os.path.exists(src):
        missing.append(k)
        continue
    size = 192 if k.startswith("e_") else 128
    up(Image.open(src), size).save(dst, optimize=True)
print("icons:", len(keys) - len(missing), "missing:", missing)
