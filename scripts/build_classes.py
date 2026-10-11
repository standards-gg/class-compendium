"""Build data for the per-class decks: data/classes.json, data/tooltips_classes.json, data/icon_ids.json.

Sources (see README):
- Client DB2 tables for WoW Forever (wago.tools, product wow_classic_beta): trainer abilities, ranks, levels, tooltips.
- Standards.gg talent calculator data (talents.standards.gg, repo forevertalent): talent trees, racials, class notes,
  professions, dungeons.
"""
import csv
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spelltext import CACHE, Db, Renderer, fmt_num  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data")
SRC = os.environ.get("FOREVERTALENT", r"E:\Dropbox\GitHub\Repos\forevertalent\src\data")
BUILD = open(os.path.join(CACHE, "build.txt")).read().strip()

LINES = {  # class -> skill lines (spec trees)
    "warrior": [26, 256, 257], "paladin": [594, 267, 184], "hunter": [50, 163, 51], "rogue": [253, 38, 39],
    "priest": [613, 56, 78], "shaman": [375, 373, 374], "mage": [8, 237, 6], "warlock": [355, 354, 593],
    "druid": [574, 134, 573],
}
BAD = re.compile(r"\(DND\)|Test|Copy of|Deprecated|NYI|\bOLD\b|TEMP|^zz|DEBUG|Passive$|^Improved ", re.I)

db = Db()
R = Renderer(db, level=30)
rd = lambda n: list(csv.DictReader(open(os.path.join(CACHE, n + ".csv"), encoding="utf-8", newline="")))

# --- listfile: icon name -> FileDataID -----------------------------------------------------------------------
name2fid = {}
with open(os.path.join(CACHE, "listfile.zip"), encoding="utf-8", errors="ignore") as f:
    for line in f:
        i, _, p = line.partition(";")
        if p.startswith("interface/icons/"):
            name2fid[p.strip()[len("interface/icons/"):-4]] = int(i)

talents = json.load(open(os.path.join(SRC, "talents.json"), encoding="utf-8"))
racials = json.load(open(os.path.join(SRC, "racials.json"), encoding="utf-8"))
review = json.load(open(os.path.join(SRC, "review-status.json"), encoding="utf-8"))
notes = json.load(open(os.path.join(SRC, "classNotes.json"), encoding="utf-8"))
profs = json.load(open(os.path.join(SRC, "professions.json"), encoding="utf-8"))
dung = json.load(open(os.path.join(SRC, "dungeons.json"), encoding="utf-8"))

# spells that are talent ranks in the client -> not trainer abilities
talent_spells = set()
for r in rd("Talent"):
    for k in range(9):
        v = r["SpellRank_%d" % k]
        if v and v != "0":
            talent_spells.add(v)

sla = rd("SkillLineAbility")
entries = {}
need_fids = set()
POWER = {"0": "Mana", "1": "Rage", "2": "Focus", "3": "Energy"}


fallback_icons = set()


def fid_of_icon(name):
    """Image key for an icon name: the FileDataID when the Forever client has it, else n_<name> (mirrored art)."""
    f = name2fid.get((name or "").lower())
    if f:
        need_fids.add(f)
        return str(f)
    if name:
        fallback_icons.add(name)
        return "n_" + name
    return None


def spell_entry(sid):
    sid = str(sid)
    s = db.spell[sid]
    desc = s["Description_lang"]
    m = re.fullmatch(r"\s*\$@spelldesc(\d+)\s*", desc)
    if m and m.group(1) in db.spell:
        text = R.render(m.group(1), db.spell[m.group(1)]["Description_lang"])
    else:
        text = R.render(sid, desc)
    cost = ""
    for p in sorted(db.power.get(sid, []), key=lambda p: int(p["OrderIndex"])):
        if p["PowerType"] in POWER:
            if int(p["ManaCost"]) > 0:
                amt = int(p["ManaCost"]) // 10 if p["PowerType"] == "1" else int(p["ManaCost"])  # rage is stored x10
                cost = "%s %s" % (amt, POWER[p["PowerType"]])
                break
            if float(p["PowerCostPct"] or 0) > 0:
                cost = "%s%% of base %s" % (fmt_num(float(p["PowerCostPct"])), POWER[p["PowerType"]].lower())
                break
    misc = db.misc.get(sid, {})
    rng = ""
    r = db.range.get(misc.get("RangeIndex", ""))
    if r and r["DisplayName_lang"] not in ("Self Only", ""):
        mx = float(r["RangeMax_0"])
        rng = "Melee Range" if (r["DisplayName_lang"] in ("Combat Range", "Melee Range") or mx <= 5) else "%s yd range" % fmt_num(mx)
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
    lv = int(db.levels.get(sid, {}).get("BaseLevel", 0) or 0)
    name = db.name[sid]
    if s["NameSubtext_lang"].startswith("Rank"):
        name = re.sub(r" (I|II|III|IV|V|VI|VII|VIII|IX|X)$", "", name)
    return {"k": "spell", "n": name, "r": s["NameSubtext_lang"], "cost": cost, "range": rng, "cast": cast, "cd": cd,
            "d": text, "lvl": lv, "id": int(sid)}


def clean(entry):
    return not re.search(r"[$]|\?\?|\{|\}|\bNaN\b", entry["d"])


classes_out = {}
dropped = []
for c in talents["classes"]:
    slug = c["slug"]
    talent_names = {t["name"] for tr in c["trees"] for t in tr["talents"]}
    # ---- trainer abilities
    chains = defaultdict(list)
    for r in sla:
        if int(r["SkillLine"]) not in LINES[slug]:
            continue
        sid = r["Spell"]
        n = db.name.get(sid, "")
        if not n or sid not in db.spell or BAD.search(n) or r["AcquireMethod"] == "3" or sid in talent_spells or n in talent_names:
            continue
        lv = db.levels.get(sid)
        m = db.misc.get(sid)
        if not lv or not m or not (1 <= int(lv["BaseLevel"]) <= 60) or m["SpellIconFileDataID"] in ("", "0"):
            continue
        sub = db.spell[sid]["NameSubtext_lang"]
        rk = int(sub.split()[1]) if sub.startswith("Rank ") and sub.split()[1].isdigit() else 0
        chains[re.sub(r" (I|II|III|IV|V|VI|VII|VIII|IX|X)$", "", n) if rk else n].append((int(lv["BaseLevel"]), rk, sid, sub))
    abilities = []
    for n, lst in chains.items():
        seen, ranks = set(), []
        for lvl, rk, sid, sub in sorted(lst):
            if (rk, lvl) in seen and rk:
                continue
            seen.add((rk, lvl))
            e = spell_entry(sid)
            if not clean(e) or not e["d"]:
                dropped.append((slug, n, sub, e["d"]))
                e = None
            key = "sp:%s" % sid
            if e:
                entries[key] = e
            fid = int(db.misc[sid]["SpellIconFileDataID"])
            need_fids.add(fid)
            ranks.append({"lv": lvl, "rk": sub, "sp": int(sid), "key": key if e else None, "img": str(fid)})
        # keep only the lowest-level entry per rank number
        abilities.append({"name": n, "first": ranks[0]["lv"], "ranks": ranks})
    abilities.sort(key=lambda a: (a["first"], a["name"]))

    # ---- talents
    trees = []
    for tr in c["trees"]:
        tl = []
        for t in tr["talents"]:
            reqs = []
            for rq in t.get("requires", []):
                other = next(x for x in tr["talents"] if x["id"] == rq["id"])
                reqs.append("%s rank %d" % (other["name"], rq["qty"]))
            for r in range(0, t["maxRank"] + 1):
                cur = t["ranks"][max(r, 1) - 1]["description"]
                nxt = t["ranks"][r]["description"] if 0 < r < t["maxRank"] else ""
                entries["tl:%d:%d" % (t["id"], r)] = {"k": "talent", "n": t["name"], "rk": "Rank %d/%d" % (r, t["maxRank"]),
                                                         "tree": tr["name"], "need": t["row"] * 5, "req": reqs, "d": cur, "next": nxt}
            st = review.get(str(t["id"]), {}).get("review", "")
            tl.append({"id": t["id"], "name": t["name"], "row": t["row"], "col": t["col"], "max": t["maxRank"],
                       "img": fid_of_icon(t["icon"]), "status": st, "requires": [{"id": q["id"], "qty": q["qty"]} for q in t.get("requires", [])]})
        trees.append({"name": tr["name"], "talents": tl})

    # ---- races
    races = []
    for race in racials["races"]:
        if slug not in race["allowedClasses"]:
            continue
        ab = []
        for a in race["abilities"]:
            key = "ra:%s:%s" % (race["slug"], a["name"])
            entries[key] = {"k": "racial", "n": a["name"], "race": race["name"], "passive": bool(a.get("passive")),
                            "cd": a.get("cooldown") if a.get("cooldown") not in (None, "TBD", "None", "Active") else "", "d": a["description"]}
            ab.append({"name": a["name"], "img": fid_of_icon(a["icon"]), "passive": bool(a.get("passive")), "key": key})
        races.append({"slug": race["slug"], "name": race["name"], "faction": race["faction"], "abilities": ab})

    extras = []
    for ename, esid in (("Shoot", 5019),):
        if slug in ("priest", "mage", "warlock") and str(esid) in db.spell:
            e = spell_entry(esid)
            if clean(e):
                fid = int(db.misc[str(esid)]["SpellIconFileDataID"])
                need_fids.add(fid)
                entries["sp:%d" % esid] = e
                extras.append({"name": ename, "img": str(fid), "key": "sp:%d" % esid})

    classes_out[slug] = {
        "extras": extras, "slug": slug, "name": c["name"], "color": c["color"], "emblem": "e_" + slug,
        "trees": trees, "abilities": abilities, "races": races,
        "notes": notes["classes"].get(slug, {}).get("newAbilities", []),
    }

# ---- shared reference data
shared = {
    "professions": [{"name": p["name"], "img": fid_of_icon(p["icon"]),
                     "bonuses": [{"name": b["name"], "img": fid_of_icon(b["icon"]), "d": b["description"]} for b in p["bonuses"]]}
                    for p in profs["professions"]],
    "dungeons": dung["dungeons"],
    "notes_source": notes["source"],
}
os.makedirs(OUT, exist_ok=True)
json.dump({"build": BUILD, "classes": classes_out, "shared": shared}, open(os.path.join(OUT, "classes.json"), "w", encoding="utf-8"), ensure_ascii=False)
json.dump({"build": BUILD, "entries": entries}, open(os.path.join(OUT, "tooltips_classes.json"), "w", encoding="utf-8"), ensure_ascii=False)
json.dump(sorted(f for f in need_fids if f), open(os.path.join(CACHE, "ids_all.json"), "w"))
json.dump(sorted(fallback_icons), open(os.path.join(CACHE, "fallback_icons.json"), "w"))
print("fallback icons:", len(fallback_icons), sorted(fallback_icons)[:12])
print("classes:", len(classes_out), "entries:", len(entries), "icons:", len(need_fids), "dropped tooltips:", len(dropped))
json.dump(dropped, open(os.path.join(CACHE, "dropped.json"), "w", encoding="utf-8"))
for slug, c in classes_out.items():
    print(slug, "abilities", len(c["abilities"]), "ranks", sum(len(a["ranks"]) for a in c["abilities"]), "races", len(c["races"]))
