"""Render WoW Forever spell descriptions from client DB2 tables (wago.tools CSV exports).

Resolves the client's description tokens ($s1, $d, $o1, $b1, ${expr}, $<var>, $?s123[a][b], $lx:y;) the way
the in-game tooltip does for a character who has not trained any talent (conditionals take their else branch).
"""
import csv
import math
import os
import re

CACHE = os.environ.get("DB2_CACHE", os.path.join(os.environ.get("TEMP", "/tmp"), "db2"))


def _rd(name):
    with open(os.path.join(CACHE, name + ".csv"), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


class Db:
    def __init__(self):
        self.spell = {r["ID"]: r for r in _rd("Spell")}
        self.name = {r["ID"]: r["Name_lang"] for r in _rd("SpellName")}
        self.effects = {}
        for r in _rd("SpellEffect"):
            self.effects.setdefault(r["SpellID"], {})[int(r["EffectIndex"])] = r
        self.misc = {r["SpellID"]: r for r in _rd("SpellMisc")}
        self.duration = {r["ID"]: r for r in _rd("SpellDuration")}
        self.range = {r["ID"]: r for r in _rd("SpellRange")}
        self.casttime = {r["ID"]: r for r in _rd("SpellCastTimes")}
        self.cooldown = {}
        for r in _rd("SpellCooldowns"):
            self.cooldown[r["SpellID"]] = r
        self.power = {}
        for r in _rd("SpellPower"):
            self.power.setdefault(r["SpellID"], []).append(r)
        self.levels = {}
        for r in _rd("SpellLevels"):
            self.levels.setdefault(r["SpellID"], r)
        self.radius = {r["ID"]: r for r in _rd("SpellRadius")}
        sv = {r["ID"]: r["Variables"] for r in _rd("SpellDescriptionVariables")}
        self.vars = {}
        for r in _rd("SpellXDescriptionVariables"):
            self.vars.setdefault(r["SpellID"], []).append(sv.get(r["SpellDescriptionVariablesID"], ""))
        self.aura_opts = {r["SpellID"]: r for r in _rd("SpellAuraOptions")}
        self.targets = {r["SpellID"]: r for r in _rd("SpellTargetRestrictions")}

    # ------------------------------------------------------------------ values
    def eff(self, sid, idx):
        return self.effects.get(str(sid), {}).get(idx - 1)

    def base(self, sid, idx):
        e = self.eff(sid, idx)
        return float(e["EffectBasePointsF"]) if e else 0.0

    def minmax(self, sid, idx):
        e = self.eff(sid, idx)
        if not e:
            return 0.0, 0.0
        b = float(e["EffectBasePointsF"])
        v = float(e["Variance"] or 0)
        lo, hi = b * (1 - v / 2), b * (1 + v / 2)
        if b < 0:
            lo, hi = hi, lo
        return lo, hi

    def dur_ms(self, sid):
        m = self.misc.get(str(sid))
        if not m:
            return 0
        d = self.duration.get(m["DurationIndex"])
        return int(d["Duration"]) if d else 0

    def period_ms(self, sid, idx):
        e = self.eff(sid, idx)
        return int(e["EffectAuraPeriod"]) if e else 0


def fmt_num(x):
    x = float(x)
    if abs(x - round(x)) < 0.05:
        return str(int(round(x)))
    return ("%.1f" % x).rstrip("0").rstrip(".")


def fmt_time(ms):
    s = ms / 1000.0
    if s >= 3600 and s % 3600 == 0:
        n = int(s // 3600)
        return "%d hour%s" % (n, "" if n == 1 else "s")
    if s >= 60:
        m = s / 60.0
        return "%s min" % fmt_num(m)
    return "%s sec" % fmt_num(s)


class Renderer:
    def __init__(self, db, level=30):
        self.db = db
        self.level = level

    # ---- expression evaluation ------------------------------------------------
    def _val(self, sid, kind, idx, other=None, signed=False):
        d = self.db
        s = other or sid
        ab = (lambda v: v) if signed else abs
        if kind == "s":
            return ab(round(d.base(s, idx))) if d.eff(s, idx) else 0
        if kind == "m":
            return ab(round(d.minmax(s, idx)[0]))
        if kind == "M":
            return ab(round(d.minmax(s, idx)[1]))
        if kind == "b":
            e = d.eff(s, idx)
            return float(e["EffectPointsPerResource"]) if e else 0
        if kind in ("t", "T"):
            return d.period_ms(s, idx) / 1000.0
        if kind == "d":
            return d.dur_ms(s) / 1000.0
        if kind == "o":
            per = d.period_ms(s, idx)
            dur = d.dur_ms(s)
            if per and dur:
                return abs(round(d.base(s, idx))) * (dur / per)
            return abs(round(d.base(s, idx)))
        if kind == "w":
            return abs(round(d.base(s, idx)))
        if kind == "x":
            e = d.eff(s, idx)
            return int(e["EffectChainTargets"]) if e else 0
        if kind == "a":
            e = d.eff(s, idx)
            if not e:
                return 0
            r = d.radius.get(e["EffectRadiusIndex_0"])
            return float(r["Radius"]) if r else 0
        if kind == "n":
            ao = d.aura_opts.get(str(s))
            return int(ao["ProcCharges"]) if ao else 0
        if kind == "u":
            ao = d.aura_opts.get(str(s))
            return int(ao["CumulativeAura"]) if ao else 0
        if kind == "i":
            tr = d.targets.get(str(s))
            return int(tr["MaxTargets"]) if tr else 0
        if kind == "v":
            tr = d.targets.get(str(s))
            return int(tr["MaxTargetLevel"]) if tr else 0
        if kind == "q":
            e = d.eff(s, idx)
            return abs(int(float(e["EffectMiscValue_0"]))) if e else 0
        if kind == "e":
            e = d.eff(s, idx)
            return float(e["EffectAmplitude"]) if e else 0
        if kind == "r":
            m = d.misc.get(str(s))
            r = d.range.get(m["RangeIndex"]) if m else None
            return float(r["RangeMax_0"]) if r else 0
        if kind == "h":
            ao = d.aura_opts.get(str(s))
            return int(ao["ProcChance"]) if ao else 0
        return 0

    def _variables(self, sid):
        out = {}
        for blob in self.db.vars.get(str(sid), []):
            for line in re.split(r"\r?\n", blob):
                m = re.match(r"\$(\w+)=(.*)$", line.strip())
                if m:
                    out[m.group(1)] = m.group(2)
        return out

    def _expr(self, expr, sid, vars_, depth=0):
        """Evaluate a ${...} arithmetic expression."""
        def repl_tok(m):
            return str(self._token_num(m.group(0), sid, vars_, depth))
        e = re.sub(r"\$\?[sa]\d+\[[^\]]*\]\[[^\]]*\]", lambda m: str(self._cond_num(m.group(0), sid, vars_, depth)), expr)
        e = re.sub(r"\$<(\w+)>", lambda m: str(self._var_num(m.group(1), sid, vars_, depth)), e)
        e = re.sub(r"\$(\d+)?([smMboOdtTwxahniuvqer])(\d*)", repl_tok, e)
        e = re.sub(r"\$PL", str(self.level), e)
        e = e.replace("$@", "")
        if not re.fullmatch(r"[0-9eE+\-*/(). ]*", e):
            raise ValueError("unsupported expression: %r from %r" % (e, expr))
        try:
            return eval(e, {"__builtins__": {}}, {})
        except ZeroDivisionError:
            return 0

    def _token_num(self, tok, sid, vars_, depth):
        m = re.fullmatch(r"\$(\d+)?([smMboOdtTwxahniuvqer])(\d*)", tok)
        other = m.group(1)
        kind = m.group(2)
        idx = int(m.group(3)) if m.group(3) else 1
        v = self._val(sid, kind, idx, other, signed=True)
        return v

    def _var_num(self, name, sid, vars_, depth):
        if depth > 8 or name not in vars_:
            return 0
        body = vars_[name].strip()
        mm = re.fullmatch(r"\$\{(.*)\}", body)
        if mm:
            return self._expr(mm.group(1), sid, vars_, depth + 1)
        cm = re.fullmatch(r"\$\?[sa]\d+\[(.*)\]\[(.*)\]", body)
        if cm:
            inner = cm.group(2)
            mm = re.fullmatch(r"\s*\$\{(.*)\}\s*", inner)
            return self._expr(mm.group(1), sid, vars_, depth + 1) if mm else 0
        try:
            return float(body)
        except ValueError:
            return 0

    def _cond_num(self, text, sid, vars_, depth):
        m = re.fullmatch(r"\$\?[sa]\d+\[[^\]]*\]\[([^\]]*)\]", text)
        inner = m.group(1).strip() if m else "0"
        mm = re.fullmatch(r"\$\{(.*)\}", inner)
        if mm:
            return self._expr(mm.group(1), sid, vars_, depth + 1)
        try:
            return float(inner)
        except ValueError:
            return 0

    # ---- main renderer -----------------------------------------------------------
    def render(self, sid, text, depth=0):
        sid = str(sid)
        vars_ = self._variables(sid)
        t = text.replace("\r", "")
        # conditionals: choose else-branch (talents / auras not active). Nested brackets are rare; handle one level.
        for _ in range(4):
            t2 = re.sub(r"\$\?\$?[sapcr]\d+\[((?:[^\[\]]|\[[^\]]*\])*)\]\[((?:[^\[\]]|\[[^\]]*\])*)\]", lambda m: m.group(2), t)
            t2 = re.sub(r"\$\?\$?[sapcr]\d+\[((?:[^\[\]]|\[[^\]]*\])*)\]", "", t2)
            if t2 == t:
                break
            t = t2
        def opsub(m):
            op, num, other, kind, idx = m.group(1), float(m.group(2)), m.group(3), m.group(4), int(m.group(5) or 1)
            v = self._val(sid, kind, idx, other)
            return fmt_num(math.floor((v / num if op == "/" else v * num) + 1e-9))
        t = re.sub(r"\$([/*])(\d+);(\d+)?([smMboOtTwxahniuvqer])(\d*)", opsub, t)
        # ${expr}[.n]
        def expr_sub(m):
            try:
                return fmt_num(math.floor(self._expr(m.group(1), sid, vars_) + 1e-9))
            except Exception:
                return "?"
        t = re.sub(r"\$\{([^{}]*)\}(?:\.\d)?", expr_sub, t)
        # $d with time formatting, $<var>
        # $<id>d reads another spell's duration; if that spell no longer exists in the client, use this spell's own
        t = re.sub(r"\$(\d+)?d\b", lambda m: fmt_time(self.db.dur_ms(m.group(1) if (m.group(1) and m.group(1) in self.db.spell) else sid)), t)
        t = re.sub(r"\$<(\w+)>", lambda m: fmt_num(self._var_num(m.group(1), sid, vars_, 0)), t)
        # simple numeric tokens
        def tok_sub(m):
            v = self._val(sid, m.group(2), int(m.group(3) or 1), m.group(1))
            return fmt_num(v)
        t = re.sub(r"\$(\d+)?([smMboOtTwxahniuvqer])(\d*)", tok_sub, t)
        # plurals: "$lpoint:points;" -> depends on previous number
        def plural(m):
            nums = re.findall(r"\d+(?:\.\d+)?", t_prefix[0])
            return m.group(2) if (nums and float(nums[-1]) != 1) else m.group(1)
        out, pos = [], 0
        t_prefix = [""]
        for m in re.finditer(r"\$[lL]([^:;]*):([^;]*);", t):
            out.append(t[pos:m.start()])
            t_prefix[0] = "".join(out)
            out.append(plural(m))
            pos = m.end()
        out.append(t[pos:])
        t = "".join(out)
        t = re.sub(r"\$[gG]([^:;]*):([^;]*);", lambda m: m.group(1), t)
        t = re.sub(r"\$PL", str(self.level), t)
        t = re.sub(r"[ \t]+\n", "\n", t)
        return t.strip()
