"""Build data/tooltips.json and data/icon_map.json for the slides.

Sources
- Abilities, poisons, profession skills, Thistle Tea: Blizzard WoW Forever client DB2 tables (wago.tools CSV exports,
  product wow_classic_beta, build recorded in the output). Descriptions are rendered with scripts/spelltext.py.
- Talents and racials: the Standards.gg talent calculator data (talents.standards.gg, repo forevertalent).

Usage:  python scripts/build_tooltips.py   (needs the DB2 CSVs in $DB2_CACHE, see README)
"""
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spelltext import CACHE, Db, Renderer, fmt_num  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data")
TALENT_SRC = os.environ.get("FOREVERTALENT", r"E:\Dropbox\GitHub\Repos\forevertalent\src\data")
BUILD = open(os.path.join(CACHE, "build.txt")).read().strip()

db = Db()
R = Renderer(db, level=30)

# --- which spell does each icon stand for ------------------------------------------------------------------
# name = spell name in the client; ranked spells are resolved to every rank with its trainer level.
ABIL = {
    "7ac9": "Sinister Strike", "58c6": "Eviscerate", "f8bc": "Slice and Dice", "44a5": "Gouge",
    "5770": "Sprint", "202b": "Vanish", "e8a5": "Kick", "89db": "Stealth", "7abb": "Sap",
    "872c": "Backstab", "eee5": "Expose Armor", "a1e7": "Garrote", "dbce": "Feint", "18a1": "Ambush",
    "f240": "Rupture", "0d10": "Kidney Shot",
}
SINGLE = {  # hash -> spell id (unranked spells)
    "1789": 5277,    # Evasion
    "baac": 13877,   # Blade Flurry
    "f7b4": 14251,   # Riposte
    "2097": 921,     # Pick Pocket
    "4a9e": 1725,    # Distract
    "c3cb": 2094,    # Blind
    "881e": 6510,    # Blinding Powder
    "19c8": 2836,    # Detect Traps
    "683d": 1842,    # Disarm Trap
    "9041": 1860,    # Safe Fall
    # professions (Apprentice skill spell)
    "e9a2": 3273, "eaf3": 8613, "4b66": 2108, "417f": 2575, "88ca": 2366, "a8e1": 2550,
    "9331": 2259, "5310": 7620, "0aa1": 7411, "27ea": 4036, "58f1": 3908, "ee21": 2018,
}
# poisons: (spell id, level the guide picks it up)
POISONS = {
    "1cdc": [(8681, 20), (8687, 28), (8691, 36), (11341, 44), (11342, 52), (11343, 60)],   # Instant
    "b915": [(2835, 30), (2837, 38), (11357, 46), (11358, 54), (25347, 60)],                # Deadly
    "dd2a": [(3420, 20), (3421, 50)],                                                       # Crippling
    "efd2": [(13220, 32), (13228, 40), (13229, 48), (13230, 56)],                           # Wound
    "a155": [(5763, 24), (8694, 38), (11400, 52)],                                          # Mind-numbing
}
CLASS_LINES = {"38", "39", "253"}

sla = list(csv.DictReader(open(os.path.join(CACHE, "SkillLineAbility.csv"), encoding="utf-8")))
class_spells = {}
for r in sla:
    if r["SkillLine"] in CLASS_LINES and r["Spell"] in db.spell:
        class_spells.setdefault(db.name.get(r["Spell"], ""), set()).add(r["Spell"])


def rank_chain(name):
    out = []
    for sid in class_spells.get(name, ()):
        sub = db.spell[sid]["NameSubtext_lang"]
        lv = db.levels.get(sid)
        if sub.startswith("Rank") and lv:
            out.append((int(lv["BaseLevel"]), int(sub.split()[1]), sid))
    out.sort(key=lambda x: (x[1], x[0]))
    # one spell per rank
    seen, res = set(), []
    for b, rk, sid in out:
        if rk not in seen:
            seen.add(rk)
            res.append((b, sid))
    return res


# --- tooltip text -------------------------------------------------------------------------------------------
POWER = {"0": "Mana", "1": "Rage", "2": "Focus", "3": "Energy"}


def spell_entry(sid, learn_level=None):
    sid = str(sid)
    s = db.spell[sid]
    desc = s["Description_lang"]
    m = re.fullmatch(r"\s*\$@spelldesc(\d+)\s*", desc)
    if m:
        desc = db.spell[m.group(1)]["Description_lang"]
        text = R.render(m.group(1), desc)
    else:
        text = R.render(sid, desc)
    cost = ""
    for p in sorted(db.power.get(sid, []), key=lambda p: int(p["OrderIndex"])):
        if p["PowerType"] in POWER and int(p["ManaCost"]) > 0:
            cost = "%s %s" % (p["ManaCost"], POWER[p["PowerType"]])
            break
    misc = db.misc.get(sid, {})
    rng = ""
    r = db.range.get(misc.get("RangeIndex", ""))
    if r and r["DisplayName_lang"] not in ("Self Only", ""):
        mx = float(r["RangeMax_0"])
        rng = "Melee Range" if r["DisplayName_lang"] in ("Combat Range", "Melee Range") or mx <= 5 else "%s yd range" % fmt_num(mx)
    cast = ""
    c = db.casttime.get(misc.get("CastingTimeIndex", ""))
    if c:
        cast = "Instant" if int(c["Base"]) == 0 else "%s sec cast" % fmt_num(int(c["Base"]) / 1000)
    cd = ""
    k = db.cooldown.get(sid)
    if k:
        ms = max(int(k["RecoveryTime"]), int(k["CategoryRecoveryTime"]))
        if ms > 0:
            sec = ms / 1000
            cd = "%s min cooldown" % fmt_num(sec / 60) if sec >= 60 else "%s sec cooldown" % fmt_num(sec)
    lv = learn_level if learn_level is not None else int(db.levels.get(sid, {}).get("BaseLevel", 0) or 0)
    return {
        "k": "spell", "n": re.sub(r" (I|II|III|IV|V|VI)$", "", db.name[sid]) if s["NameSubtext_lang"].startswith("Rank") else db.name[sid],
        "r": s["NameSubtext_lang"], "cost": cost, "range": rng, "cast": cast, "cd": cd, "d": text, "lvl": lv, "id": int(sid),
    }


entries = {}
icon_map = {}


def add_spell(sid, learn_level=None):
    key = "sp:%s" % sid
    if key not in entries:
        entries[key] = spell_entry(sid, learn_level)
    return key


for h, name in ABIL.items():
    chain = rank_chain(name)
    assert chain, name
    icon_map[h] = {"name": name, "ranks": [[b, add_spell(sid)] for b, sid in chain]}
for h, sid in SINGLE.items():
    icon_map[h] = {"name": db.name[str(sid)], "ranks": [[0, add_spell(sid)]]}
for h, lst in POISONS.items():
    ranks = [[lvl, add_spell(sid, lvl)] for sid, lvl in lst]
    icon_map[h] = {"name": re.sub(r" (I|II|III|IV|V|VI)$", "", db.name[str(lst[0][0])]), "ranks": ranks}
# Cheap Shot and a few spells have no "Rank" chain: SINGLE-style fallback
for h, nm, sid in (("0819", "Cheap Shot", 1833),):
    icon_map[h] = {"name": nm, "ranks": [[0, add_spell(sid)]]}

# --- Thistle Tea (item) -------------------------------------------------------------------------------------
item_effect = list(csv.DictReader(open(os.path.join(CACHE, "ItemEffect.csv"), encoding="utf-8")))
spar = {r["ID"]: r for r in csv.DictReader(open(os.path.join(CACHE, "ItemSparse.csv"), encoding="utf-8"))}
xie = None
tea = spar["7676"]
tea_effect = None
try:
    xie = list(csv.DictReader(open(os.path.join(CACHE, "ItemXItemEffect.csv"), encoding="utf-8")))
except OSError:
    pass
if xie:
    for r in xie:
        if r["ItemID"] == "7676":
            for e in item_effect:
                if e["ID"] == r["ItemEffectID"]:
                    tea_effect = e
if tea_effect:
    sid = tea_effect["SpellID"]
    entries["it:7676"] = {
        "k": "item", "n": tea["Display_lang"], "q": int(tea["OverallQualityID"] or 1),
        "bind": "", "lvl": int(tea["RequiredLevel"]), "use": R.render(sid, db.spell[sid]["Description_lang"]),
        "stack": int(tea["Stackable"]), "id": 7676,
    }

# --- talents (talents.standards.gg data) ---------------------------------------------------------------------
tal = json.load(open(os.path.join(TALENT_SRC, "talents.json"), encoding="utf-8"))
rogue = [c for c in tal["classes"] if c["slug"] == "rogue"][0]
talent_ids = {}
combat_grid = {}
for tree in rogue["trees"]:
    for t in tree["talents"]:
        talent_ids["%s/%s" % (tree["name"], t["name"])] = t["id"]
        if tree["name"] == "Combat":
            combat_grid["%d,%d" % (t["row"], t["col"])] = t["id"]
        reqs = []
        for rq in t.get("requires", []):
            other = next(x for x in tree["talents"] if x["id"] == rq["id"])
            reqs.append("%s rank %d" % (other["name"], rq["qty"]))
        for r in range(0, t["maxRank"] + 1):
            cur = t["ranks"][max(r, 1) - 1]["description"]
            nxt = t["ranks"][r]["description"] if 0 < r < t["maxRank"] else ""
            entries["tl:%d:%d" % (t["id"], r)] = {
                "k": "talent", "n": t["name"], "rk": "Rank %d/%d" % (r, t["maxRank"]), "tree": tree["name"],
                "need": t["row"] * 5, "req": reqs, "d": cur, "next": nxt,
            }

# --- racials (talents.standards.gg data) ----------------------------------------------------------------------
rac = json.load(open(os.path.join(TALENT_SRC, "racials.json"), encoding="utf-8"))
for race in rac["races"]:
    for a in race["abilities"]:
        entries["ra:%s:%s" % (race["slug"], a["name"])] = {
            "k": "racial", "n": a["name"], "race": race["name"], "passive": bool(a.get("passive")),
            "cd": (a.get("cooldown") or "").replace("None", "") if a.get("cooldown") not in (None, "TBD") else "",
            "d": a["description"],
        }

os.makedirs(OUT, exist_ok=True)
json.dump({"build": BUILD, "entries": entries}, open(os.path.join(OUT, "tooltips.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"icons": icon_map, "talents": {k: v for k, v in talent_ids.items()}, "combat_grid": combat_grid}, open(os.path.join(OUT, "icon_map.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("entries:", len(entries), "icons:", len(icon_map), "build:", BUILD)
