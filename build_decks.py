"""Generate the 10-slide class guides (every class except Rogue, whose Combat guide is hand-made in build.py).

Structure (same as the Combat Rogue guide):
  01 cover · 02 build · 03 rotation & buttons · 04 level plan 1-30 · 05 stats & gear · 06 dungeons & gear
  07 races · 08 professions · 09 macros & tips · 10 after 30

Inputs
  data/classes.json, data/tooltips_classes.json   client data + talents.standards.gg data (scripts/build_classes.py)
  data/guides/<class>.json                        guide content: a condensed, editable template (EDIT THIS FILE)

  python build_decks.py   ->  slides/<class>/NN-*.html, data/decks_generated.json
"""
import html
import json
import math
import os
import random
import re

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

D = json.load(open('data/classes.json', encoding='utf-8'))
CLASSES, SHARED, BUILD = D['classes'], D['shared'], D['build']
TT_ENTRIES = json.load(open('data/tooltips_classes.json', encoding='utf-8'))['entries']
TOTAL = 10
ORDER = ['warrior', 'paladin', 'hunter', 'rogue', 'priest', 'shaman', 'mage', 'warlock', 'druid']
E = lambda s: html.escape(str(s), quote=False)
MISSING = {}
EXTRA_PROF = {'First Aid': '135966', 'Cooking': '133971', 'Fishing': '136245'}


def tidy(s):
    return re.sub(r'\s+', ' ', s or '').strip()


# ---------------------------------------------------------------------------------------------- shared look
def bg_svg(variant):
    rng = random.Random(1000 + variant * 7)
    W, H = 1920, 1080
    out = [f'<svg class="bg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg"><defs>'
           '<linearGradient id="gg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3fa383"/><stop offset=".55" stop-color="#145c45"/><stop offset="1" stop-color="#062a1f"/></linearGradient>'
           '<linearGradient id="bgr" x1="1" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b3a78"/><stop offset=".5" stop-color="#1b6ea8"/><stop offset="1" stop-color="#5bbdd1"/></linearGradient>'
           '<linearGradient id="cg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f27863"/><stop offset="1" stop-color="#d4503d"/></linearGradient></defs>']
    layouts = [
        ((-140, 560, 860, 70, -90, 760), (2060, 520, 880, -90, 70, 760)),
        ((-40, 120, 820, 90, 60, 740), (1960, 1000, 900, -80, -70, 790)),
        ((260, 1180, 900, 40, -110, 800), (1800, -120, 860, -20, 90, 770)),
        ((-100, 900, 830, 110, -40, 740), (2000, 160, 840, -70, 50, 760)),
        ((300, -140, 860, -60, 80, 780), (1700, 1240, 900, 30, -100, 800)),
    ]
    g, b = layouts[variant % len(layouts)]
    for i, (cx, cy, r, ox, oy, r2) in enumerate((g, b)):
        grad = 'gg' if i == 0 else 'bgr'
        rim = '#8fe0c0' if i == 0 else '#9fe1f0'
        out.append(f'<mask id="m{i}"><rect width="{W}" height="{H}" fill="#000"/><circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff"/>'
                   f'<circle cx="{cx+ox}" cy="{cy+oy}" r="{r2}" fill="#000"/></mask>')
        out.append(f'<g mask="url(#m{i})"><rect width="{W}" height="{H}" fill="url(#{grad})" opacity=".92"/></g>')
        out.append(f'<g mask="url(#m{i})"><circle cx="{cx+ox}" cy="{cy+oy}" r="{r2+2}" fill="none" stroke="{rim}" stroke-width="5" opacity=".55"/></g>')
    tris = [[(1500, -20), (1740, -20), (1260, 330)], [(-40, 760), (380, 560), (330, 960)], [(1640, 700), (1990, 600), (1900, 920)],
            [(760, 1100), (900, 780), (1010, 1100)], [(180, -10), (520, -10), (120, 300)]]
    rng.shuffle(tris)
    for tri in tris[:3]:
        (x1, y1), (x2, y2), (x3, y3) = tri
        out.append(f'<polygon points="{x1},{y1} {x2},{y2} {x3},{y3}" fill="url(#cg)" opacity=".86"/>')
        out.append(f'<polyline points="{x1},{y1} {x2},{y2}" stroke="#f9a08e" stroke-width="5" fill="none" opacity=".6"/>')
        for _ in range(34):
            a, b2 = rng.random(), rng.random()
            if a + b2 > 1:
                a, b2 = 1 - a, 1 - b2
            px = x1 + a * (x2 - x1) + b2 * (x3 - x1)
            py = y1 + a * (y2 - y1) + b2 * (y3 - y1)
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{rng.choice([2, 2.5, 3, 4, 5, 6.5])}" fill="#b8483a" opacity=".82"/>')
    out.append('</svg>')
    return ''.join(out)


def speck_layer(variant, pool, n=9):
    rng = random.Random(77 + variant * 13)
    spots = [(10, 160), (150, 880), (1700, 170), (1780, 900), (880, 20), (1000, 940), (30, 520), (1850, 520), (1300, 40), (420, 960), (1500, 980), (700, 30)]
    rng.shuffle(spots)
    items = []
    for x, y in spots[:n]:
        s = rng.choice([84, 104, 126, 150])
        h = rng.choice(pool)
        items.append(f'<img src="../../assets/icf/{h}.png" style="left:{x}px;top:{y}px;width:{s}px;height:{s}px;transform:rotate({rng.randint(-24, 24)}deg)">')
    return '<div class="speck">' + ''.join(items) + '</div>'


def icn(img, size='md', cls='', key=None, rank=None, rk_cls=''):
    a = f' data-tt="{key}"' if key else ''
    r = f'<span class="rk {rk_cls}">{rank}</span>' if rank is not None else ''
    return f'<div class="ic {size} {cls}"{a}><img src="../../assets/icf/{img}.png" alt="">{r}</div>'


COMMON_CSS = '''
.edit{font:600 italic 18px 'Barlow Condensed';letter-spacing:.06em;color:#7d7967;text-transform:uppercase;padding:14px 4px}
'''


def frame(c, idx, title, sub, body, extra_css=''):
    dots = ''.join(f'<i class="{"on" if i == idx else ""}"></i>' for i in range(1, TOTAL + 1))
    pool = [r['img'] for a in c['abilities'] for r in a['ranks'][:1]] + [t['img'] for tr in c['trees'] for t in tr['talents'] if t['img']]
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{E(c['name'])} · {title}</title>
<meta name="viewport" content="width=1920"><link rel="stylesheet" href="../../assets/style.css">
<style>:root{{--rogue:{c['color']};--acc:{c['color']}}}.ic.new{{border-color:var(--acc)}}{COMMON_CSS}{extra_css}</style></head>
<body><div class="slide">{bg_svg(idx + ORDER.index(c['slug']))}{speck_layer(idx + ORDER.index(c['slug']), pool)}<div class="vig"></div>
<div class="hdr"><img class="logo" src="../../assets/logo.png" alt="">
<div><div class="kick">WoW FOREVER &middot; {E(c['name']).upper()} &middot; LEVEL 1 &rarr; 30</div><h1 class="disp x3d">{title}</h1></div><div class="sub">{sub}</div>
<div class="right"><div class="num">{idx:02d}<small>/{TOTAL}</small></div></div></div>
<div class="main">{body}</div>
<div class="ftr"><b>WoW Forever Beta</b><span>&middot;</span><span>{E(c['name'])} guide</span><div class="dots">{dots}</div></div>
</div></body></html>'''


def save(slug, n, name, page):
    keys = sorted(set(re.findall(r'data-tt="([^"]+)"', page)))
    data = {k: TT_ENTRIES[k] for k in keys if k in TT_ENTRIES}
    inject = ('<script>window.TTBUILD=%s;window.TT=%s;</script><script src="../../assets/tooltips.js"></script>'
              % (json.dumps(BUILD), json.dumps(data, ensure_ascii=False)))
    page = page.replace('</body>', inject + '</body>')
    os.makedirs(f'slides/{slug}', exist_ok=True)
    fn = f'slides/{slug}/{n:02d}-{name}.html'
    open(fn, 'w', encoding='utf-8').write(page)
    return fn


# ---------------------------------------------------------------------------------------------- lookups
class Ctx:
    def __init__(self, c, g):
        self.c, self.g = c, g
        self.talents = {t['name']: (tr['name'], t) for tr in c['trees'] for t in tr['talents']}
        self.abil = {a['name']: a for a in c['abilities']}

    def ability(self, name, level=30):
        a = self.abil.get(name)
        if not a:
            for x in self.c.get('extras', []):
                if x['name'] == name:
                    return {'img': x['img'], 'key': x['key']}
            return None
        ok = [r for r in a['ranks'] if r['lv'] <= level] or a['ranks'][:1]
        r = ok[-1]
        return {'img': r['img'], 'key': r['key']}

    def talent(self, name, rank=None):
        t = self.talents.get(name)
        if not t:
            return None
        rk = t[1]['max'] if rank is None else rank
        return {'img': t[1]['img'], 'key': f"tl:{t[1]['id']}:{rk}", 'tree': t[0], 'id': t[1]['id'], 'max': t[1]['max']}

    def icon_for(self, name):
        r = self.ability(name) or self.talent(name)
        if not r:
            MISSING.setdefault(self.c['slug'], set()).add(name)
        return r

    def ranks(self):
        out = {}
        for e in self.g['build']['order']:
            out[e[1]] = out.get(e[1], 0) + e[2]
        return out

    def sequence(self, start=10):
        """one entry per talent point: (level, tree, name, rank_after)"""
        seq, cum = [], {}
        lvl = start
        for e in self.g['build']['order']:
            tree, name, pts = e[0], e[1], e[2]
            legacy = len(e) > 3 and e[3] == 'L'
            for _ in range(pts):
                cum[name] = cum.get(name, 0) + 1
                if not legacy:
                    seq.append((lvl, tree, name, cum[name]))
                    lvl += 1
        return seq

    def build_code(self):
        r = self.ranks()
        code = ''
        for tr in self.c['trees']:
            for t in sorted(tr['talents'], key=lambda t: (t['row'], t['col'])):
                code += str(r.get(t['name'], 0)) if self.talents.get(t['name'], (None,))[0] == tr['name'] else '0'
        return code.rstrip('0')


def ab_icon(cx, name, size='md', cls='', label=None, sub=None, w=None):
    ic = cx.icon_for(name)
    st = f' style="width:{w}px"' if w else ''
    lab = f'<div class="lab">{E(label if label is not None else name)}</div>' if label != '' else ''
    sb = f'<div class="sub2">{E(sub)}</div>' if sub else ''
    if not ic:
        body = f'<div class="ic {size} off"><img src="../../assets/icf/{cx.c["emblem"]}.png" alt=""></div>'
    else:
        body = icn(ic['img'], size, cls, ic['key'])
    return f'<div class="cell"{st}>{body}{lab}{sb}</div>'


# ---------------------------------------------------------------------------------------------- 01 cover
def cover(cx):
    c, g = cx.c, cx.g
    nrank = sum(len(a['ranks']) for a in c['abilities'])
    ntal = sum(len(tr['talents']) for tr in c['trees'])
    stats = [(str(len(c['abilities'])), 'TRAINER ABILITIES'), (str(nrank), 'ABILITY RANKS'), (str(ntal), 'TALENTS'), (str(len(c['races'])), 'RACES')]
    specs = ''
    for tr in c['trees']:
        on = tr['name'] == g['build']['tree']
        icons = ''.join(icn(t['img'], 'md', key=f"tl:{t['id']}:0") for t in sorted(tr['talents'], key=lambda t: (t['row'], t['col']))[:4])
        specs += (f'<div class="spec {"on" if on else ""}"><div class="sn disp">{E(tr["name"])}</div><div class="si">{icons}</div>'
                  f'<div class="sc">{"THIS GUIDE &middot; " if on else ""}{len(tr["talents"])} talents</div></div>')
    side = lambda lst, cls: f'<div class="side {cls}">' + ''.join(f'<div class="cs"><b class="disp">{a}</b><span>{b}</span></div>' for a, b in lst) + '</div>'
    url = f"https://talents.standards.gg/{c['slug']}/{cx.build_code()}"
    css = '''
.cov{position:absolute;inset:0;background:url(../../assets/banner.jpg) center/cover}
.scrim{position:absolute;inset:0;background:radial-gradient(ellipse 60% 55% at 50% 52%,rgba(3,5,12,.84),rgba(3,5,12,.18) 80%),linear-gradient(180deg,rgba(3,5,12,0) 40%,rgba(3,5,12,.9) 100%)}
.emb{position:absolute;left:50%;top:40px;width:330px;height:330px;transform:translateX(-50%);display:flex;align-items:center;justify-content:center}
.emb::before{content:'';position:absolute;inset:0;background:var(--acc);clip-path:polygon(25% 3%,75% 3%,99% 50%,75% 97%,25% 97%,1% 50%);opacity:.95}
.emb::after{content:'';position:absolute;inset:10px;background:#05070f;clip-path:polygon(25% 3%,75% 3%,99% 50%,75% 97%,25% 97%,1% 50%)}
.emb img{position:relative;z-index:2;width:214px;height:214px;border-radius:14px;border:4px solid var(--gold);box-shadow:0 0 0 3px #04060d,8px 8px 0 3px var(--brown),0 0 60px color-mix(in srgb,var(--acc) 55%,transparent)}
.ttl{position:absolute;left:0;right:0;top:372px;text-align:center}
.ttl h1{font-size:170px;letter-spacing:.005em;display:inline-block}
.ttl .l2{font:800 italic 40px 'Barlow Condensed';letter-spacing:.24em;color:var(--cream);text-transform:uppercase;margin-top:18px}
.ttl .l2 b{color:var(--acc)}
.specs{position:absolute;left:0;right:0;bottom:158px;display:flex;justify-content:center;gap:26px}
.spec{width:400px;padding:14px 20px 12px;background:rgba(5,8,18,.8);border-top:5px solid #3a3320;text-align:center;opacity:.72}
.spec.on{border-top-color:var(--acc);opacity:1;box-shadow:0 0 30px color-mix(in srgb,var(--acc) 35%,transparent)}
.spec .sn{font-size:40px;color:var(--cream);text-shadow:3px 3px 0 var(--brown)}
.spec .si{display:flex;justify-content:center;gap:12px;margin:10px 0 7px}
.spec .sc{font:700 17px 'Barlow Condensed';letter-spacing:.2em;color:var(--acc);text-transform:uppercase}
.ctas{position:absolute;left:0;right:0;bottom:50px;display:flex;justify-content:center;gap:30px}
.cta.cls{background:linear-gradient(180deg,#fff,var(--acc))}
.src{position:absolute;left:0;right:0;bottom:14px;text-align:center;font:600 15px 'Barlow Condensed';letter-spacing:.16em;color:#7d7967;text-transform:uppercase}
.side{position:absolute;top:230px;display:flex;flex-direction:column;gap:20px}
.side .cs{padding:10px 20px 12px;background:rgba(5,8,18,.8);border-left:5px solid var(--acc);min-width:270px}
.side .cs b{display:block;font-size:58px;color:var(--acc);text-shadow:3px 3px 0 var(--brown),4px 4px 0 #04060d}
.side .cs span{font:700 18px 'Barlow Condensed';letter-spacing:.22em;color:var(--cream)}
.side.r{right:56px;align-items:flex-end}.side.l{left:56px}
.side.r .cs{border-left:0;border-right:5px solid var(--acc);text-align:right}
.tag-top{position:absolute;left:56px;right:56px;top:28px;display:flex;justify-content:space-between;font:700 19px 'Barlow Condensed';letter-spacing:.34em;color:var(--gold)}
'''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{E(c['name'])} · WoW Forever</title>
<link rel="stylesheet" href="../../assets/style.css"><style>:root{{--rogue:{c['color']};--acc:{c['color']}}}{css}</style></head><body><div class="slide">
<div class="cov"></div><div class="scrim"></div><div class="vig"></div>
<div class="tag-top"><span>WoW FOREVER BETA</span><span>{E(c['name']).upper()} &middot; LEVELING GUIDE TEMPLATE</span></div>
{side(stats[:2], 'l')}{side(stats[2:], 'r')}
<div class="emb"><img src="../../assets/icf/{c['emblem']}.png" alt=""></div>
<div class="ttl"><h1 class="disp x3d">{E(c['name']).upper()}</h1><div class="l2"><b>{E(g['spec']).upper()}</b> &nbsp;&middot;&nbsp; LEVEL <b>1 &rarr; 30</b> &nbsp;&middot;&nbsp; WoW FOREVER BETA</div></div>
<div class="specs">{specs}</div>
<div class="ctas"><a class="cta cls" href="{url}"><div><b>OPEN THIS {E(g['spec']).upper()} BUILD</b><span>talents.standards.gg &middot; recommended 21-point build</span></div>
<svg viewBox="0 0 24 24" fill="none" stroke="#0a0c14" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17 17 7M8 7h9v9"/></svg></a></div>
<div class="src">template condensed from {E(g['source']['name'])} &middot; {E(g['source']['author'])} &middot; edit freely</div>
</div></body></html>'''


# ---------------------------------------------------------------------------------------------- 02 build
def build_slide(cx):
    c, g = cx.c, cx.g
    b = g['build']
    ranks = cx.ranks()
    tr = next(t for t in c['trees'] if t['name'] == b['tree'])
    by = {(t['row'], t['col']): t for t in tr['talents']}
    cells = ''
    for r in range(7):
        cells += f'<div class="tier">{r*5}</div>'
        for col in range(4):
            t = by.get((r, col))
            if not t:
                cells += '<div class="tc"></div>'
                continue
            n = ranks.get(t['name'], 0) if cx.talents[t['name']][0] == tr['name'] else 0
            rcls = 'zero' if n == 0 else ('part' if n < t['max'] else '')
            cls = 'off' if n == 0 else ''
            cells += (f'<div class="tc">{icn(t["img"], "md", cls, f"tl:{t["id"]}:{n}", f"{n}/{t["max"]}", rcls)}'
                      f'<div class="tn">{E(t["name"]) if n else ""}</div></div>')
    other = sum(e[2] for e in b['order'] if e[0] != b['tree'])
    spent = sum(e[2] for e in b['order'])
    nleg = sum(e[2] for e in b['order'] if len(e) > 3 and e[3] == 'L')
    cards, cum, lvl = '', {}, 10
    for e in b['order']:
        tree, name, pts = e[0], e[1], e[2]
        legacy = len(e) > 3 and e[3] == 'L'
        cum[name] = cum.get(name, 0) + pts
        t = cx.talent(name, cum[name])
        if legacy:
            lv = 'LEGACY'
        else:
            lv = f'{lvl}&ndash;{lvl+pts-1}' if pts > 1 else f'{lvl}'
            lvl += pts
        why = b.get('why', {}).get(name, '')
        cards += (f'<div class="oc">{icn(t["img"], "md", "", t["key"]) if t else ""}<div class="ot"><div class="lv disp">{lv}</div>'
                  f'<b>{E(name)} {pts}</b><span>{E(why)}</span></div></div>')
    extra = (f' &middot; plus {other} pts in other trees' if other else '') + (f' &middot; incl. {nleg} legacy points' if nleg else '')
    css = '''
.wrap{display:grid;grid-template-columns:660px 1fr;grid-template-rows:minmax(0,1fr);gap:22px;height:100%}
.tg{display:grid;grid-template-columns:40px repeat(4,1fr);grid-template-rows:repeat(7,108px);margin-top:4px}
.tier{font:800 italic 22px 'Barlow Condensed';color:#7d7967;display:flex;align-items:center;justify-content:center;border-right:1px solid rgba(227,175,74,.22);margin-right:6px}
.tc{display:flex;flex-direction:column;align-items:center;padding-top:6px}
.tc .ic{--s:68px}
.tn{font:700 12.5px/1.05 'Barlow Condensed';letter-spacing:.02em;text-transform:uppercase;color:var(--mute);margin-top:9px;text-align:center;width:128px;height:27px;overflow:hidden}
.right{display:flex;flex-direction:column;gap:20px;min-height:0}
.ocg{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.oc{display:flex;gap:14px;align-items:center;padding:10px 12px;border-radius:12px;background:linear-gradient(160deg,rgba(32,38,58,.88),rgba(17,21,36,.88));border:1px solid rgba(227,175,74,.2);min-height:112px}
.oc .ic{--s:68px;flex:none}
.ot{min-width:0}
.ot .lv{font-size:34px;word-break:keep-all;color:var(--acc);text-shadow:2px 2px 0 var(--brown);line-height:1}
.ot b{display:block;font:800 italic 21px/1.05 'Barlow Condensed';text-transform:uppercase;letter-spacing:.02em;margin-top:2px}
.ot span{display:-webkit-box;font:500 13px/1.3 Inter;color:#b9b39d;margin-top:3px;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.note{padding:16px 22px;border-radius:12px;background:linear-gradient(90deg,rgba(80,46,14,.9),rgba(40,24,10,.9));border:2px solid #ff9d2e}
.note b{color:#ffb347;font:800 italic 22px 'Barlow Condensed';text-transform:uppercase;letter-spacing:.04em}
.note p{font:500 16px/1.4 Inter;color:#f1e6cf;margin-top:4px}
'''
    early = E(b.get('early', 'Spend the points in order from level 10.')) + (' ' + E(b['skip']) if b.get('skip') else '')
    body = f'''<div class="wrap"><div class="panel"><div class="ph"><h2 class="disp x3d" style="font-size:42px">{E(b['tree']).upper()}</h2><span class="tag">{spent} points{extra}</span></div><div class="tg">{cells}</div></div>
<div class="right"><div class="panel" style="flex:1 1 auto;min-height:0"><div class="ph"><h2 class="disp x3d">TALENT ORDER</h2><span class="tag">1 point per level from level 10{' &middot; then legacy points' if nleg else ''}</span></div><div class="ocg">{cards}</div></div>
<div class="note"><b>Leveling notes</b><p>{early}</p></div></div></div>'''
    return frame(c, 2, 'THE BUILD', f'{E(g["spec"])} &middot; {spent}/51 points', body, css)


# ---------------------------------------------------------------------------------------------- 03 rotation
def rotation_slide(cx):
    c, g = cx.c, cx.g
    core = ''.join(f'<div class="cc">{ab_icon(cx, x["a"], "lg", "new", label="")}<div class="ct"><b>{E(x["a"])}</b><span>{E(x["t"])}</span></div></div>' for x in g['core'])
    rows = ''
    for st in g['steps']:
        items = ''.join(ab_icon(cx, it['a'], 'md', '', sub=it['t'], w=122) for it in st['items'])
        rows += f'<div class="srow"><div class="slv">Lv<br>{E(st["lv"])}</div><div class="sit">{items}</div></div>'
    tips = ''.join(f'<div class="tp">{ab_icon(cx, x["a"], "md", "", label="")}<div class="tt2"><b>{E(x["a"])}</b><span>{E(x["t"])}</span></div></div>' for x in g['tips'])
    css = '''
.g{display:grid;grid-template-columns:1fr 620px;grid-template-rows:auto minmax(0,1fr);gap:20px;height:100%}
.corep{grid-column:1/3}
.cg{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}
.cc{display:flex;gap:12px;align-items:flex-start;padding:10px 12px;border-radius:12px;background:linear-gradient(160deg,rgba(32,38,58,.88),rgba(17,21,36,.88));border:1px solid rgba(227,175,74,.2);min-height:132px}
.cc .ic{--s:72px;flex:none}
.ct b{display:block;font:900 italic 24px/1 'Barlow Condensed';text-transform:uppercase;color:var(--acc)}
.ct span{display:block;font:500 14px/1.32 Inter;color:#cfc9b4;margin-top:4px}
.srow{display:flex;gap:16px;align-items:flex-start;padding:10px 0;border-bottom:1px solid rgba(227,175,74,.2)}
.srow:last-child{border:0}
.slv{width:86px;font:900 italic 36px/.95 'Barlow Condensed';color:var(--acc);text-transform:uppercase;flex:none}
.sit{display:flex;flex-wrap:wrap;gap:8px 6px}
.sit .ic{--s:60px}
.cell .lab{font-size:14px;margin-top:8px;line-height:1.05}
.sub2{font:500 12px/1.2 Inter;color:#b9b39d;text-align:center;margin-top:4px;max-width:118px}
.tp{display:flex;align-items:center;gap:14px;padding:8px 14px;border-radius:12px;background:linear-gradient(160deg,rgba(32,38,58,.88),rgba(17,21,36,.88));border:1px solid rgba(227,175,74,.2);flex:1;min-height:0}
.tp .ic{--s:60px;flex:none}
.tt2 b{display:block;font:900 italic 28px/1 'Barlow Condensed';text-transform:uppercase}
.tt2 span{font:600 20px 'Barlow Condensed';letter-spacing:.1em;text-transform:uppercase;color:var(--coral)}
.tips{display:flex;flex-direction:column;gap:9px;height:calc(100% - 66px)}
'''
    body = f'''<div class="g"><div class="panel corep"><div class="ph" style="margin-bottom:10px"><h2 class="disp x3d">CORE PRIORITIES</h2><span class="tag">{E(g['headline'])}</span></div><div class="cg">{core}</div></div>
<div class="panel" style="overflow:hidden"><div class="ph" style="margin-bottom:6px"><h2 class="disp x3d">ROTATION</h2></div>{rows}</div>
<div class="panel" style="--edge1:#ef5e48;--edge2:#4a1a12"><div class="ph"><h2 class="disp x3d" style="color:#ffb7a8">OH NO! BUTTONS</h2></div><div class="tips">{tips}</div></div></div>'''
    return frame(c, 3, 'ROTATION &amp; BUTTONS', 'core loop &middot; panic buttons', body, css)


# ---------------------------------------------------------------------------------------------- 04 / 10 abilities
def ability_slide(cx, idx, lo, hi, title, with_talents):
    c = cx.c
    levels = {}
    for a in c['abilities']:
        for r in a['ranks']:
            if lo <= r['lv'] <= hi:
                levels.setdefault(r['lv'], []).append((a['name'], r))
    lvs = sorted(levels)
    pts = {}
    if with_talents:
        for lvl, tree, name, rank in cx.sequence():
            if not (lo <= lvl <= hi):
                continue
            card = max([l for l in lvs if l <= lvl] or [lvs[0]])
            t = cx.talent(name, rank)
            if t:
                pts.setdefault(card, []).append(t)
    nic = sum(len(v) for v in levels.values())
    cards = ''
    for lv in lvs:
        icons = ''
        for name, r in levels[lv]:
            lab = name if len(name) <= 18 else name[:17] + '…'
            rk = ('r' + r['rk'].split()[1]) if r['rk'].startswith('Rank') else ''
            icons += f'<div class="cell">{icn(r["img"], "md", "", r["key"])}<div class="lab">{E(lab)}</div><div class="sub">{rk}</div></div>'
        tp = ''
        if pts.get(lv):
            tp = '<div class="tpts"><span>talents</span>' + ''.join(icn(t['img'], 'sm', 'new', t['key']) for t in pts[lv]) + '</div>'
        cards += f'<div class="lc"><div class="lv">{lv}</div><div class="bd"><div class="is">{icons}</div>{tp}</div></div>'
    css = """
.lcols{--sz:60px;column-count:4;column-gap:16px;column-fill:auto;height:726px;overflow:hidden}
.lc{display:flex;gap:12px;align-items:flex-start;padding:7px 10px 8px 0;border-radius:10px;border-left:8px solid var(--acc);background:linear-gradient(90deg,color-mix(in srgb,var(--acc) 16%,#0a0e1a),rgba(15,19,34,.9) 60%);break-inside:avoid;margin-bottom:10px}
.lc .lv{font:900 italic 54px 'Barlow Condensed';color:var(--acc);width:82px;text-align:center;flex:none;text-shadow:3px 3px 0 var(--brown),4px 4px 0 #04060d;line-height:1;margin-top:6px}
.lc .bd{min-width:0}
.lc .is{display:flex;flex-wrap:wrap;gap:6px 0}
.lc .is .ic{--s:var(--sz)}
.lc .cell{width:calc(var(--sz) + 14px)}
.lc .cell .lab{font-size:13px;margin-top:9px;letter-spacing:.01em;width:calc(var(--sz) + 14px)}
.lcols.big .cell .lab{font-size:14px}.lcols.small .cell .lab{font-size:12px}
.lcols.nolab .cell .lab,.lcols.nolab .cell .sub{display:none}
.lcols.nolab .cell{width:calc(var(--sz) + 8px)}
.lc .cell .sub{font:700 13px 'Barlow Condensed';color:var(--acc);letter-spacing:.08em}
.tpts{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:8px;padding-top:7px;border-top:1px dashed rgba(227,175,74,.3)}
.tpts span{font:800 12px 'Barlow Condensed';letter-spacing:.2em;color:var(--acc);text-transform:uppercase;margin-right:4px}
.tpts .ic{--s:40px}
"""
    fit = """<script>
(function(){
  function fit(){
    var el=document.querySelector('.lcols'); if(!el) return;
    var sizes=[88,80,72,66,60,54,50,46,42,38,34], cols=[3,4,5,6,7];
    for(var i=0;i<sizes.length;i++){ for(var j=0;j<cols.length;j++){
      el.style.setProperty('--sz',sizes[i]+'px'); el.style.columnCount=cols[j];
      el.className='lcols '+(sizes[i]>=72?'big':(sizes[i]<=50?'small':''));
      if(el.scrollWidth<=el.clientWidth+2) return;
    }}
    var t=[50,46,42,38,34];
    for(var i=0;i<t.length;i++){ for(var j=0;j<cols.length;j++){
      el.style.setProperty('--sz',t[i]+'px'); el.style.columnCount=cols[j]; el.className='lcols small nolab';
      if(el.scrollWidth<=el.clientWidth+2) return;
    }}
  }
  (document.fonts&&document.fonts.ready?document.fonts.ready:Promise.resolve()).then(function(){setTimeout(fit,50)});
})();
</script>"""
    sub = f'{len(lvs)} trainer levels &middot; {nic} ranks'
    leg = '<span>number = trainer level</span><span>r# = rank</span>'
    if with_talents and pts:
        leg += '<span class="yel" style="color:var(--acc)">talents row = points spent at those levels</span>'
    body = f'''<div class="panel" style="height:100%;padding-bottom:14px"><div class="ph" style="margin-bottom:10px"><span class="tag" style="font-size:26px">CLASS TRAINER ABILITIES &middot; LEVELS {lo} &rarr; {hi}</span>
<div class="legend" style="margin-left:auto">{leg}</div></div>
<div class="lcols">{cards}</div></div>{fit}'''
    return frame(c, idx, title, sub, body, css)


# ---------------------------------------------------------------------------------------------- 05 stats & gear
def stats_slide(cx):
    c, g = cx.c, cx.g
    st = ''.join(f'<div class="sr"><div class="sn">{i+1}</div><div><b>{E(s["n"])}</b><p>{E(s["t"])}</p></div></div>' for i, s in enumerate(g['stats']))
    gear = ''.join(f'<div class="gi"><i></i><p>{E(t)}</p></div>' for t in g['gear'])
    notes = ''.join(f'<div class="gi"><i></i><p>{E(t)}</p></div>' for t in g.get('notes', []))
    css = '''
.g{display:grid;grid-template-columns:900px 1fr;gap:22px;height:100%}
.sr{display:flex;gap:22px;align-items:center;padding:14px 18px;margin-bottom:12px;border-radius:12px;background:linear-gradient(160deg,rgba(32,38,58,.9),rgba(17,21,36,.9));border-left:8px solid var(--acc)}
.sr .sn{font:900 italic 84px 'Barlow Condensed';color:var(--acc);width:70px;text-align:center;text-shadow:3px 3px 0 var(--brown),4px 4px 0 #04060d;line-height:.9}
.sr b{font:900 italic 38px 'Barlow Condensed';text-transform:uppercase;line-height:1}
.sr p{font:500 18px/1.38 Inter;color:#cfc9b4;margin-top:4px}
.col{display:flex;flex-direction:column;gap:22px;min-height:0}
.gi{display:flex;gap:14px;align-items:flex-start;padding:10px 14px;margin-bottom:9px;border-radius:10px;background:rgba(255,255,255,.04)}
.gi i{width:12px;height:12px;border-radius:3px;background:var(--acc);margin-top:7px;flex:none;transform:rotate(45deg)}
.gi p{font:500 17px/1.4 Inter;color:#e1dcc8}
'''
    body = f'''<div class="g"><div class="panel" style="height:100%"><div class="ph"><h2 class="disp x3d">STAT PRIORITY</h2><span class="tag">highest first</span></div>{st}</div>
<div class="col"><div class="panel" style="flex:0 0 auto"><div class="ph"><h2 class="disp x3d">GEAR &amp; WEAPONS</h2></div>{gear}</div>
<div class="panel" style="flex:1 1 auto;min-height:0"><div class="ph"><h2 class="disp x3d">THINGS TO REMEMBER</h2></div>{notes}</div></div></div>'''
    return frame(c, 5, 'STATS &amp; GEAR', 'what to stack &middot; what to wield', body, css)


# ---------------------------------------------------------------------------------------------- 06 dungeons & gear
def dungeons_slide(cx):
    c, g = cx.c, cx.g
    ds = sorted(SHARED['dungeons'], key=lambda d: (d['minLevel'], d['maxLevel']))
    rows = ''
    for d in ds:
        left = (d['minLevel'] - 1) / 59 * 100
        width = max(1.2, (d['maxLevel'] - d['minLevel']) / 59 * 100)
        cls = 'forever' if d['type'] == 'forever' else 'classic'
        tag = '<span class="chip">NEW</span>' if d['type'] == 'forever' else ''
        rows += (f'<div class="dr {cls}"><div class="dn">{E(d["name"])}{tag}</div><div class="bar"><i style="left:{left:.2f}%;width:{width:.2f}%"></i></div>'
                 f'<div class="dl">{d["minLevel"]}&ndash;{d["maxLevel"]}</div></div>')
    axis = ''.join(f'<span style="left:{(lv-1)/59*100:.2f}%">{lv}</span>' for lv in (1, 10, 20, 30, 40, 50, 60))
    dg = ''.join(f'<div class="dg"><b>{E(x["dungeon"])}</b><p>{E(x["items"])}</p></div>' for x in g.get('dungeon_gear', []))
    if not dg:
        dg = '<div class="edit">This guide has no dungeon gear list. Add your picks in data/guides/' + c['slug'] + '.json &rarr; dungeon_gear.</div>'
    tips = ''.join(f'<div class="gi"><i></i><p>{E(t)}</p></div>' for t in g.get('dungeon_tips', []))
    css = '''
.g{display:grid;grid-template-columns:940px 1fr;gap:22px;height:100%}
.dr{display:grid;grid-template-columns:290px 1fr 64px;align-items:center;gap:12px;height:18.5px}
.dn{font:800 italic 17px 'Barlow Condensed';text-transform:uppercase;letter-spacing:.03em;display:flex;align-items:center;gap:8px;white-space:nowrap}
.dn .chip{font-size:12px;padding:0 6px}
.bar{position:relative;height:10px;background:rgba(255,255,255,.06);border-radius:7px}
.bar i{position:absolute;top:0;height:100%;border-radius:7px;background:linear-gradient(90deg,#6db6ff,#4aa8ff);box-shadow:0 0 12px rgba(74,168,255,.5)}
.dr.forever .bar i{background:linear-gradient(90deg,var(--acc),#fff);box-shadow:0 0 14px color-mix(in srgb,var(--acc) 70%,transparent)}
.dr.forever .dn{color:var(--acc)}
.dl{font:900 italic 18px 'Barlow Condensed';text-align:right}
.axis{position:relative;height:22px;margin-left:302px;margin-right:76px;margin-bottom:4px}
.axis span{position:absolute;transform:translateX(-50%);font:800 15px 'Barlow Condensed';letter-spacing:.12em;color:#7d7967}
.lvl{display:grid;gap:2px}
.col{display:flex;flex-direction:column;gap:22px;min-height:0}
.dg{padding:10px 14px;margin-bottom:9px;border-radius:10px;border-left:6px solid var(--acc);background:rgba(255,255,255,.04)}
.dg b{font:900 italic 24px 'Barlow Condensed';text-transform:uppercase}
.dg p{font:500 16px/1.4 Inter;color:#cfc9b4;margin-top:2px}
.gi{display:flex;gap:14px;align-items:flex-start;padding:10px 14px;margin-bottom:9px;border-radius:10px;background:rgba(255,255,255,.04)}
.gi i{width:12px;height:12px;border-radius:3px;background:var(--acc);margin-top:7px;flex:none;transform:rotate(45deg)}
.gi p{font:500 17px/1.4 Inter;color:#e1dcc8}
'''
    body = f'''<div class="g"><div class="panel" style="height:100%;padding-bottom:8px"><div class="ph" style="margin-bottom:6px"><span class="tag" style="font-size:24px">35 DUNGEONS BY LEVEL</span>
<div class="legend" style="margin-left:auto"><span><span class="chip">NEW</span> new in Forever</span></div></div><div class="axis">{axis}</div><div class="lvl">{rows}</div></div>
<div class="col"><div class="panel" style="flex:0 0 auto"><div class="ph"><h2 class="disp x3d">GEAR BY DUNGEON</h2></div>{dg}</div>
<div class="panel" style="flex:1 1 auto;min-height:0"><div class="ph"><h2 class="disp x3d">DUNGEON &amp; GROUP TIPS</h2></div>{tips}</div></div></div>'''
    return frame(c, 6, 'DUNGEONS &amp; GEAR', '35 dungeons &middot; level 1 &rarr; 60', body, css)


# ---------------------------------------------------------------------------------------------- 07 races
def races_slide(cx):
    c, g = cx.c, cx.g
    chip = {'GREAT': 'great', 'SOLID': 'solid', 'DECENT': 'decent', 'OK': 'ok', 'PVP': 'pvp', 'WEAKEST': 'weak'}

    def col(fac, name, color):
        cards = ''
        for rr in g['races'][fac]:
            race = next((r for r in c['races'] if r['faction'] == fac and (r['name'] == rr['race'] or (rr['race'] == 'Skyborne' and 'Skyborne' in r['name']))), None)
            if not race:
                continue
            icons = ''.join(f'<div class="cell" style="width:88px">{icn(a["img"], "md", "" if a["passive"] else "new", a["key"])}<div class="lab">{E(a["name"])}</div></div>' for a in race['abilities'])
            rating = f'<span class="chip {chip.get(rr["rating"], "ok")}">{E(rr["rating"])}</span>' if rr['rating'] else ''
            cards += (f'<div class="rc" style="--c:{color}"><div class="rn"><h3>{E(rr["race"])}</h3>{rating}<p>{E(rr["note"])}</p></div><div class="is">{icons}</div></div>')
        return f'<div class="fac"><div class="fh" style="color:{color}">{name}</div>{cards}</div>'
    css = '''
.g{display:grid;grid-template-columns:1fr 1fr;gap:22px;height:100%}
.fac{display:flex;flex-direction:column;gap:10px}
.fh{font:900 italic 52px 'Barlow Condensed';text-transform:uppercase;letter-spacing:.03em;line-height:.9;display:flex;align-items:center;gap:16px}
.fh::after{content:'';flex:1;height:5px;background:linear-gradient(90deg,currentColor,transparent);opacity:.7;transform:skewX(-30deg)}
.rc{display:grid;grid-template-columns:330px 1fr;gap:12px;align-items:center;padding:8px 14px 8px 18px;border-radius:12px;border-left:10px solid var(--c);background:linear-gradient(90deg,color-mix(in srgb,var(--c) 18%,#0a0e1a),rgba(15,19,34,.92) 55%);flex:0 1 150px;min-height:0}
.rc h3{font:900 italic 34px 'Barlow Condensed';text-transform:uppercase;line-height:1;margin-bottom:4px;display:inline-block;margin-right:10px}
.rc p{display:-webkit-box;font:500 13.5px/1.3 Inter;color:#cfc9b4;margin-top:4px;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.rc .is{display:flex;gap:2px;justify-content:flex-end}
.rc .ic{--s:56px}
.rc .cell .lab{font-size:12.5px;margin-top:7px;width:86px;letter-spacing:.01em;line-height:1.05}
'''
    pick = g['races'].get('pick', '')
    note = f'<div class="pickn"><b>Pick</b><span>{E(pick)}</span></div>' if pick else ''
    css += '''.pickn{grid-column:1/3;padding:10px 18px;border-radius:12px;background:linear-gradient(90deg,rgba(80,46,14,.9),rgba(40,24,10,.9));border:2px solid #ff9d2e;display:flex;gap:16px;align-items:center}
.pickn b{font:900 italic 26px 'Barlow Condensed';text-transform:uppercase;color:#ffb347}
.pickn span{font:500 17px/1.35 Inter;color:#f1e6cf}
.g{grid-template-rows:minmax(0,1fr) auto}
'''
    body = f'<div class="g">{col("alliance", "ALLIANCE", "#4a9dff")}{col("horde", "HORDE", "#ef5e48")}{note}</div>'
    return frame(c, 7, 'RACES', f'{len(c["races"])} races can play {E(c["name"])}', body, css)


# ---------------------------------------------------------------------------------------------- 08 professions
def profs_slide(cx):
    c, g = cx.c, cx.g
    profs = {p['name']: p for p in SHARED['professions']}

    def pimg(name):
        return profs[name]['img'] if name in profs else EXTRA_PROF.get(name)
    picks = ''
    for p in g['professions']:
        im = pimg(p['n'])
        icon = icn(im, 'lg') if im else ''
        picks += (f'<div class="pk">{icon}<div><div class="ph3"><span class="badge t-{p["tier"]}">{p["tier"]}</span><b>{E(p["n"])}</b></div><p>{E(p["note"])}</p></div></div>')
    if not picks:
        picks = '<div class="edit">No profession advice in this guide: add yours in data/guides/' + c['slug'] + '.json &rarr; professions.</div>'
    grid = ''
    for p in SHARED['professions']:
        bs = ''.join(f'<div class="b">{icn(b["img"], "sm")}<div><b>{E(b["name"])}</b><p>{E(tidy(b["d"]))}</p></div></div>' for b in p['bonuses'])
        grid += f'<div class="pc"><div class="ph2">{icn(p["img"], "md")}<h3>{E(p["name"])}</h3></div>{bs}</div>'
    css = '''
.g{display:grid;grid-template-columns:600px 1fr;gap:22px;height:100%}
.pk{display:flex;gap:16px;align-items:center;padding:14px 16px;margin-bottom:12px;border-radius:12px;background:linear-gradient(160deg,rgba(32,38,58,.9),rgba(17,21,36,.9));border-left:8px solid var(--acc)}
.pk .ic{flex:none}
.ph3{display:flex;align-items:center;gap:12px}
.ph3 b{font:900 italic 36px 'Barlow Condensed';text-transform:uppercase}
.pk p{font:500 16px/1.38 Inter;color:#cfc9b4;margin-top:5px}
.pg{display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:repeat(3,minmax(0,1fr));gap:10px;height:calc(100% - 52px)}
.pc{padding:8px 12px;border-radius:12px;border-left:6px solid var(--acc);background:linear-gradient(90deg,color-mix(in srgb,var(--acc) 12%,#0a0e1a),rgba(15,19,34,.92) 60%);overflow:hidden}
.ph2{display:flex;align-items:center;gap:12px;margin-bottom:4px}
.ph2 .ic{--s:40px}
.ph2 h3{font:900 italic 26px 'Barlow Condensed';text-transform:uppercase}
.b{display:flex;gap:8px;align-items:flex-start;margin-top:4px}
.b .ic{--s:28px;margin-top:2px;flex:none}
.b b{font:800 italic 15px 'Barlow Condensed';text-transform:uppercase;letter-spacing:.02em}
.b p{font:500 11.5px/1.25 Inter;color:#cfc9b4;margin-top:1px}
'''
    tiers = '<span class="legend" style="margin-left:12px">' + ''.join(f'<span class="badge t-{t}" style="margin-left:6px">{t}</span>' for t in 'SABCD') + '</span>'
    body = f'''<div class="g"><div class="panel" style="height:100%"><div class="ph"><h2 class="disp x3d" style="font-size:42px">YOUR PICKS</h2>{tiers}</div>{picks}</div>
<div class="panel" style="height:100%;padding-bottom:10px"><div class="ph" style="margin-bottom:8px"><span class="tag" style="font-size:24px">FOREVER PROFESSION BONUSES</span></div><div class="pg">{grid}</div></div></div>'''
    return frame(c, 8, 'PROFESSIONS', 'tier picks &middot; Forever bonuses', body, css)


# ---------------------------------------------------------------------------------------------- 09 macros
def macros_slide(cx):
    c, g = cx.c, cx.g

    def colr(line):
        e = E(line)
        if line.startswith('#'):
            return f'<span style="color:#b79cff">{e}</span>'
        if line.startswith('/cast') or line.startswith('/use'):
            a, _, b = e.partition(' ')
            return f'<span style="color:#7be08e">{a}</span> <span style="color:var(--cream)">{b}</span>'
        return f'<span style="color:var(--cyan)">{e}</span>'
    mac = ''
    for m in g['macros']:
        ics = ''.join(ab_icon(cx, a, 'md', '', label='') for a in m['a'])
        mac += (f'<div class="mc"><div class="mi"><div class="ics">{ics}</div><div class="lab">{E(m["label"])}</div></div>'
                f'<code>{chr(10).join(colr(l) for l in m["lines"])}</code></div>')
    if not mac:
        mac = '<div class="edit">No macros in this guide: add yours in data/guides/' + c['slug'] + '.json &rarr; macros.</div>'
    tr = ''.join(f'<div class="gi"><i></i><p>{E(t)}</p></div>' for t in g.get('trainers', []))
    steps = '<div class="steps"><div class="st"><b>1</b>type /macro</div><span class="arr" style="font-size:34px">&#10132;</span><div class="st"><b>2</b>New</div><span class="arr" style="font-size:34px">&#10132;</span><div class="st"><b>3</b>paste</div></div>'
    css = '''
.g{display:grid;grid-template-columns:1fr 640px;gap:22px;height:100%}
.mc{display:grid;grid-template-columns:170px 1fr;gap:16px;align-items:center;margin-bottom:10px}
.mi{display:flex;flex-direction:column;align-items:center}
.mi .ics{display:flex;gap:10px}
.mi .ic{--s:60px}
.mi .lab{font-size:15px;margin-top:8px}
code{display:block;font:500 19px/1.35 'JetBrains Mono',monospace;background:#03050b;border:1px solid rgba(227,175,74,.35);border-radius:10px;padding:9px 16px;white-space:pre-wrap;box-shadow:inset 0 0 24px rgba(0,0,0,.6)}
.steps{display:flex;gap:10px;align-items:center;margin:2px 0 12px}
.st{display:flex;align-items:center;gap:12px;padding:7px 14px;border-radius:8px;background:color-mix(in srgb,var(--acc) 12%,transparent);border:1px solid var(--acc);font:800 21px 'Barlow Condensed';letter-spacing:.08em;text-transform:uppercase}
.st b{display:inline-flex;width:30px;height:30px;align-items:center;justify-content:center;border-radius:50%;background:var(--acc);color:#0a0c14;font:900 italic 21px 'Barlow Condensed'}
.gi{display:flex;gap:14px;align-items:flex-start;padding:10px 14px;margin-bottom:9px;border-radius:10px;background:rgba(255,255,255,.04)}
.gi i{width:12px;height:12px;border-radius:3px;background:var(--acc);margin-top:7px;flex:none;transform:rotate(45deg)}
.gi p{font:500 17px/1.4 Inter;color:#e1dcc8}
'''
    right = (f'<div class="panel" style="height:100%"><div class="ph"><h2 class="disp x3d">TRAINERS</h2></div>{tr}</div>' if tr else
             '<div class="panel" style="height:100%"><div class="ph"><h2 class="disp x3d">TRAINERS</h2></div><div class="edit">Add weapon / class trainer locations: data/guides/' + c['slug'] + '.json &rarr; trainers.</div></div>')
    body = f'''<div class="g"><div class="panel" style="height:100%"><div class="ph" style="margin-bottom:8px"><h2 class="disp x3d">MACROS</h2><span class="tag">copy &middot; paste &middot; play</span></div>{steps}{mac}</div>{right}</div>'''
    return frame(c, 9, 'MACROS &amp; TRAINERS', 'one-button quality of life', body, css)


# ---------------------------------------------------------------------------------------------- run
decks = {}
for slug in ORDER:
    if slug == 'rogue':
        continue
    gp = f'data/guides/{slug}.json'
    if not os.path.exists(gp):
        print('skip (no guide yet):', slug)
        continue
    g = json.load(open(gp, encoding='utf-8'))
    cx = Ctx(CLASSES[slug], g)
    for e in g['build']['order']:
        assert e[1] in cx.talents, f'{slug}: unknown talent {e[1]}'
    files = [
        save(slug, 1, 'cover', cover(cx)),
        save(slug, 2, 'build', build_slide(cx)),
        save(slug, 3, 'rotation', rotation_slide(cx)),
        save(slug, 4, 'level-plan', ability_slide(cx, 4, 1, 30, 'LEVEL PLAN', True)),
        save(slug, 5, 'stats-gear', stats_slide(cx)),
        save(slug, 6, 'dungeons-gear', dungeons_slide(cx)),
        save(slug, 7, 'races', races_slide(cx)),
        save(slug, 8, 'professions', profs_slide(cx)),
        save(slug, 9, 'macros', macros_slide(cx)),
        save(slug, 10, 'after-30', ability_slide(cx, 10, 31, 60, 'AFTER 30', True)),
    ]
    decks[slug] = {'files': files, 'spec': g['spec'], 'source': g['source']}
json.dump(decks, open('data/decks_generated.json', 'w'), indent=1)
for k, v in MISSING.items():
    print('no icon for', k, sorted(v))
print('built', sum(len(v['files']) for v in decks.values()), 'slides for', list(decks))
