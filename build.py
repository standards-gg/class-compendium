import json, random, os, glob, html
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
os.makedirs('slides', exist_ok=True)

# ------------------------------------------------------------------ prep assets
if not os.path.exists('assets/logo.png'):
    Image.open('src/logo.png').resize((900, 900), Image.LANCZOS).save('assets/logo.png', optimize=True)
if not os.path.exists('assets/banner.jpg'):
    Image.open('src/banner.png').convert('RGB').resize((1920, 1080), Image.LANCZOS).save('assets/banner.jpg', quality=93)

CLS = json.load(open('src/cls.json'))
TTD = json.load(open('data/tooltips.json', encoding='utf-8'))
TT_ENTRIES, TT_BUILD = TTD['entries'], TTD['build']
IMAP = json.load(open('data/icon_map.json', encoding='utf-8'))
ICONS, TALENTS, GRID = IMAP['icons'], IMAP['talents'], IMAP['combat_grid']
RAW = json.load(open('src/images.json'))
ALL_ICONS = sorted(os.path.basename(f)[:-4] for f in glob.glob('assets/ic/*.png'))
TOTAL = 10
PVP_URL = 'https://talents.standards.gg/rogue/000000000000000003200331120141'
PVE_URL = 'https://talents.standards.gg/rogue/000000000000000003200332110141'

def esc(s): return html.escape(s, quote=False)

# ------------------------------------------------------------------ components
def abil(h, level=None):
    """Tooltip key for an ability icon: the rank the trainer teaches at `level` (default: best rank by level 30)."""
    m = ICONS.get(h)
    if not m:
        return None
    lv = 30 if level is None else level
    ok = [r for r in m['ranks'] if r[0] <= lv]
    return (ok[-1] if ok else m['ranks'][0])[1]

def talent(name, rank):
    return 'tl:%d:%d' % (TALENTS['Combat/' + name], rank)

def ic(h, size='md', cls='', rank=None, rk_cls='', tt=None):
    r = ''
    if rank is not None:
        r = f'<span class="rk {rk_cls}">{rank}</span>'
    key = abil(h) if tt is None else (tt or None)
    a = f' data-tt="{key}"' if key else ''
    return f'<div class="ic {size} {cls}"{a}><img src="../assets/ic/{h}.png" alt="">{r}</div>'

def cell(h, label='', size='md', cls='', red=False, w=None, tt=None):
    st = f' style="width:{w}px"' if w else ''
    lab = f'<div class="lab {"red" if red else ""}">{label}</div>' if label else ''
    return f'<div class="cell"{st}>{ic(h,size,cls,tt=tt)}{lab}</div>'

ARROW = '<div class="arr">&#10132;</div>'

def tri_pts(rng, kind):
    return kind

def bg_svg(variant):
    rng = random.Random(1000 + variant * 7)
    W, H = 1920, 1080
    out = [f'<svg class="bg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg"><defs>'
           '<linearGradient id="gg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3fa383"/><stop offset=".55" stop-color="#145c45"/><stop offset="1" stop-color="#062a1f"/></linearGradient>'
           '<linearGradient id="bgr" x1="1" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b3a78"/><stop offset=".5" stop-color="#1b6ea8"/><stop offset="1" stop-color="#5bbdd1"/></linearGradient>'
           '<linearGradient id="cg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f27863"/><stop offset="1" stop-color="#d4503d"/></linearGradient>'
           '<filter id="sh" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="14"/></filter></defs>']
    # crescents (green + blue) via masks
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
    # coral speckled triangles
    tris = [
        [(1500, -20), (1740, -20), (1260, 330)],
        [(-40, 760), (380, 560), (330, 960)],
        [(1640, 700), (1990, 600), (1900, 920)],
        [(760, 1100), (900, 780), (1010, 1100)],
        [(180, -10), (520, -10), (120, 300)],
    ]
    rng.shuffle(tris)
    for tri in tris[:3]:
        (x1, y1), (x2, y2), (x3, y3) = tri
        out.append(f'<polygon points="{x1},{y1} {x2},{y2} {x3},{y3}" fill="url(#cg)" opacity=".86"/>')
        out.append(f'<polyline points="{x1},{y1} {x2},{y2}" stroke="#f9a08e" stroke-width="5" fill="none" opacity=".6"/>')
        for _ in range(34):
            a, b2 = rng.random(), rng.random()
            if a + b2 > 1: a, b2 = 1 - a, 1 - b2
            px = x1 + a * (x2 - x1) + b2 * (x3 - x1)
            py = y1 + a * (y2 - y1) + b2 * (y3 - y1)
            rr = rng.choice([2, 2.5, 3, 4, 5, 6.5])
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{rr}" fill="#b8483a" opacity=".82"/>')
    out.append('</svg>')
    return ''.join(out)

def speck_layer(variant, n=9):
    rng = random.Random(77 + variant * 13)
    spots = [(10, 160), (150, 880), (1700, 170), (1780, 900), (880, 20), (1000, 940), (30, 520), (1850, 520), (1300, 40), (420, 960), (1500, 980), (700, 30)]
    rng.shuffle(spots)
    items = []
    for x, y in spots[:n]:
        s = rng.choice([84, 104, 126, 150])
        h = rng.choice(ALL_ICONS)
        rot = rng.randint(-24, 24)
        items.append(f'<img src="../assets/ic/{h}.png" style="left:{x}px;top:{y}px;width:{s}px;height:{s}px;transform:rotate({rot}deg)">')
    return '<div class="speck">' + ''.join(items) + '</div>'

def frame(idx, title, sub, body, kicker='COMBAT ROGUE &middot; LEVEL 1 &rarr; 30', variant=None, extra_right=''):
    variant = idx if variant is None else variant
    dots = ''.join(f'<i class="{"on" if i == idx else ""}"></i>' for i in range(1, TOTAL + 1))
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(title)}</title>
<meta name="viewport" content="width=1920"><link rel="stylesheet" href="../assets/style.css"></head>
<body><div class="slide">{bg_svg(variant)}{speck_layer(variant)}<div class="vig"></div>
<div class="hdr"><img class="logo" src="../assets/logo.png" alt="">
<div><div class="kick">{kicker}</div><h1 class="disp x3d">{title}</h1></div><div class="sub">{sub}</div>
<div class="right">{extra_right}<div class="num">{idx:02d}<small>/{TOTAL}</small></div></div></div>
<div class="main">{body}</div>
<div class="ftr"><b>WoW Forever Beta</b><span>&middot;</span><span>Combat Rogue guide</span><div class="dots">{dots}</div></div>
</div></body></html>'''

def save(n, slug, htmlstr):
    import re as _re
    keys = sorted(set(_re.findall(r'data-tt="([^"]+)"', htmlstr)))
    data = {k: TT_ENTRIES[k] for k in keys}
    inject = ('<script>window.TTBUILD=%s;window.TT=%s;</script><script src="../assets/tooltips.js"></script>'
              % (json.dumps(TT_BUILD), json.dumps(data, ensure_ascii=False)))
    htmlstr = htmlstr.replace('</body>', inject + '</body>')
    open(f'slides/{n:02d}-{slug}.html', 'w', encoding='utf-8').write(htmlstr)

ARR_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="#0a0c14" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17 17 7M8 7h9v9"/></svg>'
def cta(kind, title, sub):
    url = PVP_URL if kind == 'pvp' else PVE_URL
    return f'<a class="cta {kind}" href="{url}" target="_blank" rel="noopener"><div><b>{title}</b><span>{sub}</span></div>{ARR_SVG}</a>'

# =================================================================== 01 COVER
def cover():
    kit = [('7ac9', 'Sinister Strike'), ('58c6', 'Eviscerate'), ('f8bc', 'Slice and Dice'), ('1789', 'Evasion'),
           ('44a5', 'Gouge'), ('5770', 'Sprint'), ('202b', 'Vanish'), ('e8a5', 'Kick'), ('baac', 'Blade Flurry')]
    kit_html = ''.join(cell(h, n, 'lg', 'new' if i in (0, 8) else '', w=130) for i, (h, n) in enumerate(kit))
    stats = [('9', 'SLIDES OF INTEL'), ('1&rarr;30', 'LEVEL PLAN'), ('0/21/0', 'COMBAT TALENTS'), ('117', 'REAL ICONS')]
    stat_html = ''.join(f'<div class="cs"><b class="disp">{a}</b><span>{b}</span></div>' for a, b in stats)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Combat Rogue 1-30</title>
<link rel="stylesheet" href="../assets/style.css"><style>
.cov{{position:absolute;inset:0;background:url(../assets/banner.jpg) center/cover}}
.scrim{{position:absolute;inset:0;background:radial-gradient(ellipse 60% 55% at 50% 52%,rgba(3,5,12,.82),rgba(3,5,12,.15) 80%),linear-gradient(180deg,rgba(3,5,12,.0) 40%,rgba(3,5,12,.88) 100%)}}
.big{{position:absolute;left:50%;top:44px;width:470px;height:470px;transform:translateX(-50%);filter:drop-shadow(0 22px 40px rgba(0,0,0,.8))}}
.ttl{{position:absolute;left:0;right:0;top:470px;text-align:center}}
.ttl h1{{font-size:188px;letter-spacing:.005em}}
.ttl .l2{{font:800 italic 40px 'Barlow Condensed';letter-spacing:.26em;color:var(--cream);text-transform:uppercase;margin-top:26px}}
.ttl .l2 b{{color:var(--rogue)}}
.kit{{position:absolute;left:0;right:0;bottom:158px;display:flex;justify-content:center;gap:10px}}
.ctas{{position:absolute;left:0;right:0;bottom:30px;display:flex;justify-content:center;gap:30px}}
.cs{{position:absolute}}
.side{{position:absolute;top:210px;display:flex;flex-direction:column;gap:22px}}
.side .cs{{position:static;text-align:left;padding:10px 20px 12px;background:rgba(5,8,18,.78);border-left:5px solid var(--rogue);min-width:250px}}
.side .cs b{{display:block;font-size:56px;color:var(--rogue);text-shadow:3px 3px 0 var(--brown),4px 4px 0 #04060d}}
.side .cs span{{font:700 18px 'Barlow Condensed';letter-spacing:.22em;color:var(--cream)}}
.side.r{{right:56px;align-items:flex-end}} .side.l{{left:56px}}
.side.r .cs{{border-left:0;border-right:5px solid var(--rogue);text-align:right}}
.tag-top{{position:absolute;left:56px;right:56px;top:28px;display:flex;justify-content:space-between;font:700 19px 'Barlow Condensed';letter-spacing:.34em;color:var(--gold)}}
</style></head><body><div class="slide">
<div class="cov"></div><div class="scrim"></div><div class="vig"></div>
<div class="tag-top"><span>WoW FOREVER BETA</span><span>ROGUE &middot; COMBAT &middot; 0/21/0</span></div>
<div class="side l">{''.join(f'<div class="cs"><b class="disp">{a}</b><span>{b}</span></div>' for a, b in stats[:2])}</div>
<div class="side r">{''.join(f'<div class="cs"><b class="disp">{a}</b><span>{b}</span></div>' for a, b in stats[2:])}</div>
<img class="big" src="../assets/logo.png" alt="">
<div class="ttl"><h1 class="disp x3d cream" style="display:inline-block">COMBAT <span class="yel" style="color:var(--rogue);text-shadow:1px 1px 0 #9a6a1f,2px 2px 0 #8a5c19,3px 3px 0 #6e4614,4px 4px 0 #5a3718,5px 5px 0 #4a2c12,6px 6px 0 #05070f,7px 7px 0 #05070f,0 0 28px rgba(255,245,106,.28)">ROGUE</span></h1>
<div class="l2">LEVEL <b>1 &rarr; 30</b> &nbsp;&middot;&nbsp; WoW FOREVER BETA</div></div>
<div class="kit">{kit_html}</div>
<div class="ctas">{cta('pvp','PVP REALM BUILD','hybrid PVE + PVP &middot; open in talent calculator')}{cta('pve','PVE REALM BUILD','pure leveling &middot; open in talent calculator')}</div>
</div></body></html>'''

# =================================================================== 02 BUILDS
TREE_NAMES = {'7ac9': 'Imp. Sinister Strike', '58c6': 'Imp. Eviscerate', 'f16a': 'Precision', '9a22': 'Deflection', 'f7b4': 'Riposte',
              '1789': 'Endurance', '5770': 'Imp. Sprint', '3263': 'Flawless Exec.', '490b': 'Dual Wield', 'baac': 'Blade Flurry'}
PVP_RANKS = '3/3 2/2 0/5 0/3 3/3 3/3 1/2 1/1 2/2 0/2 1/1 4/5 1/1 0/5 0/2 0/3 0/1'.split()
PVE_RANKS = '3/3 2/2 0/5 0/3 3/3 3/3 2/2 1/1 1/2 0/2 1/1 4/5 1/1 0/5 0/2 0/3 0/1'.split()

def tree(items, ranks):
    cells = {}
    for a, rk in zip(items, ranks):
        x, y = a['bbox'][0], a['bbox'][1]
        col = round(((x % 600 if x > 650 else x) - 130) / 137) if False else None
        cells[(a['h'], x, y)] = rk
    out = []
    tx = 0 if items[0]['bbox'][0] < 650 else 600
    grid = ''
    for a, rk in zip(items, ranks):
        x, y = a['bbox'][0] - (0 if a['bbox'][0] < 650 else 603), a['bbox'][1]
        col = max(0, min(3, round((x - 130) / 137)))
        row = max(0, min(6, round((y - 453) / 91.5)))
        n, m = map(int, rk.split('/'))
        rcls = 'zero' if n == 0 else ('part' if n < m else '')
        c = ''
        if a['cls'] == 'amber': c = 'amber'
        elif n == 0: c = 'off'
        nm = TREE_NAMES.get(a['h'], '') if n else ''
        nm = f'<div class="tn">{nm}</div>' if nm else '<div class="tn"></div>'
        tid = GRID.get('%d,%d' % (row, col))
        key = 'tl:%d:%d' % (tid, n) if tid else False
        grid += (f'<div class="tc" style="grid-column:{col+1};grid-row:{row+1}">{ic(a["h"],"md",c,rk,rcls,tt=key)}{nm}</div>')
    return f'<div class="tgrid">{grid}</div>'

def builds():
    d = CLS['1']
    trees = [a for a in d if 430 < a['bbox'][1] < 1020]
    pvp = [a for a in trees if a['bbox'][0] < 650]
    pve = [a for a in trees if a['bbox'][0] >= 650]
    order = [('10–11', '7ac9', 'Imp. Sinister<br>Strike 2', ''), ('12–14', '58c6', 'Imp. Eviscerate 3', ''), ('15–16', 'f16a', 'Precision 2', ''),
             ('17–19', '9a22', 'Deflection 3', ''), ('20', 'f7b4', 'Riposte 1', ''), ('21', 'f16a', 'Precision +1', ''),
             ('22', '1789', 'Endurance 1', 'amber'), ('23–24', '5770', 'Imp. Sprint 2', 'amber'), ('25', '3263', 'Flawless Exec. 1', ''),
             ('26–29', '490b', 'Dual Wield 4', ''), ('30', 'baac', 'Blade Flurry 1', 'new')]
    tkeys = [('Improved Sinister Strike', 2), ('Improved Eviscerate', 3), ('Precision', 2), ('Deflection', 3), ('Riposte', 1),
             ('Precision', 3), ('Endurance', 1), ('Improved Sprint', 2), ('Flawless Execution', 1), ('Dual Wield Specialization', 4),
             ('Blade Flurry', 1)]
    cards = ''
    for (lv, h, nm, c), (tn, tr) in zip(order, tkeys):
        hl = ' hl' if c == 'amber' else ''
        cards += f'<div class="oc{hl}"><div class="lv disp">{lv}</div>{ic(h,"lg",c,tt=talent(tn,tr))}<div class="on">{nm}</div></div>'
    css = '''<style>
.wrap{display:grid;grid-template-columns:488px 488px 1fr;grid-template-rows:minmax(0,1fr);gap:22px;height:100%}
.tgrid{display:grid;grid-template-columns:repeat(4,106px);grid-template-rows:repeat(7,104px);justify-content:center;margin-top:4px}
.tc{display:flex;flex-direction:column;align-items:center;justify-content:flex-start;padding-top:6px}
.tn{font:700 12.5px/1 'Barlow Condensed';letter-spacing:.02em;text-transform:uppercase;color:var(--mute);margin-top:9px;text-align:center;height:26px;width:100px}
.tc .ic{--s:66px}
.right{display:flex;flex-direction:column;gap:18px}
.ocg{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.oc{display:flex;flex-direction:column;align-items:center;padding:10px 6px 14px;background:linear-gradient(160deg,rgba(32,38,58,.85),rgba(17,21,36,.85));border:1px solid rgba(227,175,74,.2);border-radius:12px;height:176px}
.oc.hl{border:2px solid #ff9d2e;box-shadow:0 0 22px rgba(255,157,46,.35)}
.oc .lv{font-size:40px;color:var(--rogue);margin-bottom:6px;text-shadow:2px 2px 0 var(--brown)}
.oc .on{font:700 16px/1.05 'Barlow Condensed';letter-spacing:.05em;text-transform:uppercase;text-align:center;margin-top:12px}
.note{display:flex;gap:20px;align-items:center;padding:18px 22px;border-radius:12px;background:linear-gradient(90deg,rgba(80,46,14,.9),rgba(40,24,10,.9));border:2px solid #ff9d2e}
.note .tx{font:700 25px/1.2 'Barlow Condensed';letter-spacing:.03em;text-transform:uppercase}
.note b{color:#ffb347}.note em{font-style:normal;color:var(--rogue)}
.ctas{display:flex;gap:16px}
.ctas .cta{min-width:0;flex:1;padding:12px 20px}
.ctas .cta b{font-size:30px}
.ctas .cta span{font-size:14px}
</style>'''
    body = css + f'''<div class="wrap">
<div class="panel pvp"><div class="ph"><h2 class="disp x3d">PVP REALM</h2><span class="tag">0/21/0</span></div>{tree(pvp,PVP_RANKS)}</div>
<div class="panel pve"><div class="ph"><h2 class="disp x3d" style="color:var(--pve);text-shadow:1px 1px 0 #2a5f9e,2px 2px 0 #1f4c80,3px 3px 0 #17375e,4px 4px 0 #10294a,5px 5px 0 #05070f,6px 6px 0 #05070f">PVE REALM</h2><span class="tag">0/21/0</span></div>{tree(pve,PVE_RANKS)}</div>
<div class="right">
<div class="ctas">{cta('pvp','PVP REALM BUILD','open in talent calculator')}{cta('pve','PVE REALM BUILD','open in talent calculator')}</div>
<div class="panel" style="flex:1"><div class="ph"><h2 class="disp x3d">TALENT ORDER</h2><span class="tag">1 point per level &middot; PVP build</span></div><div class="ocg">{cards}</div></div>
<div class="note">{ic('5770','lg','amber')}<div class="tx"><b>PVP:</b> <em>Improved Sprint 2/2, Endurance 1/2</em> &rarr; Sprint breaks snares when you get ganked.</div></div>
</div></div>'''
    return frame(2, 'TALENT BUILDS', '0/21/0 &middot; PVP + PVE', body)

# =================================================================== 03 ROTATION
def rotation():
    css = '''<style>
.g{display:grid;grid-template-columns:1fr 640px;grid-template-rows:262px minmax(0,1fr);gap:20px;height:100%}
.core{grid-column:1/3}
.flow{display:flex;align-items:flex-start;gap:26px;margin-top:6px}
.dots5{display:flex;gap:11px;margin-top:24px}
.dots5 i{width:42px;height:42px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#ff9d8c,#e8523b 55%,#8e2a1d);box-shadow:0 0 16px rgba(238,106,85,.7),inset -3px -4px 6px rgba(0,0,0,.35)}
.or{font:800 italic 30px 'Barlow Condensed';color:var(--mute);margin:32px 4px 0;text-transform:uppercase}
.pri{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;flex:1;margin-left:40px;align-self:stretch}
.pc{display:flex;align-items:center;gap:20px;padding:0 22px;border-radius:12px;background:linear-gradient(160deg,rgba(32,38,58,.85),rgba(17,21,36,.85));border:1px solid rgba(227,175,74,.2)}
.pc .n{font:900 italic 72px 'Barlow Condensed';line-height:.9}
.pc .t b{display:block;font:800 26px 'Barlow Condensed';letter-spacing:.04em;text-transform:uppercase}
.pc .t span{font:500 19px Inter;color:var(--mute)}
.corebody{display:flex;gap:10px;flex-direction:column;height:100%}
.rot .row{display:flex;align-items:center;gap:20px;padding:14px 0;border-bottom:1px solid rgba(227,175,74,.2)}
.rot .row:last-child{border:0}
.rot .lvl{width:112px;font:900 italic 40px/.95 'Barlow Condensed';text-transform:uppercase}
.rot .row .arr{font-size:40px;margin:0 -2px 26px}
.rot .eq{font:800 34px 'Barlow Condensed';text-transform:uppercase;letter-spacing:.03em;margin-left:14px}
.rot .eq b{color:var(--rogue)}
.oh{display:flex;flex-direction:column;gap:9px}
.ohc{display:flex;align-items:center;gap:20px;padding:6px 18px;min-height:0;border-radius:12px;background:linear-gradient(160deg,rgba(32,38,58,.85),rgba(17,21,36,.85));border:1px solid rgba(227,175,74,.2);flex:1}
.ohc b{display:block;font:900 italic 34px 'Barlow Condensed';text-transform:uppercase;line-height:1}
.ohc span{font:600 21px 'Barlow Condensed';letter-spacing:.1em;text-transform:uppercase;color:var(--coral)}
</style>'''
    core = f'''<div class="panel core"><div class="ph"><h2 class="disp x3d">CORE LOOP</h2><span class="tag">build &rarr; spend &rarr; repeat</span></div>
<div class="flow">{cell('7ac9','Sinister<br>Strike','lg','new',w=130)}{ARROW}
<div class="cell" style="width:300px"><div class="dots5"><i></i><i></i><i></i><i></i><i></i></div><div class="lab" style="margin-top:34px">5 combo<br>points</div></div>{ARROW}
{cell('58c6','Eviscerate','lg','new',w=130)}<div class="or">or</div>{cell('f8bc','Slice and<br>Dice','lg','new',w=130)}
<div class="pri">
<div class="pc"><div class="n yel">#1</div><div class="t"><b>Auto attacks</b><span>keep SnD up</span></div></div>
<div class="pc"><div class="n" style="color:var(--good)">#2</div><div class="t"><b>Sinister Strike</b><span>slow main hand</span></div></div>
<div class="pc"><div class="n cor">#3</div><div class="t"><b>Eviscerate</b><span>mob dying / SnD up</span></div></div>
</div></div></div>'''
    rot = f'''<div class="panel rot"><div class="ph"><h2 class="disp x3d">ROTATION</h2></div>
<div class="row"><div class="lvl cor">Lv<br>1–25</div>{cell('d2e0','&times;2','lg',w=112)}{ARROW}{cell('7ac9','&times;2','lg',w=112)}{ARROW}{cell('f8bc','SnD','lg',w=112)}{ARROW}{cell('7ac9','spam','lg',w=112)}{ARROW}{cell('58c6','finish','lg',w=112)}</div>
<div class="row"><div class="lvl" style="color:var(--mount)">Lv<br>26+</div>{cell('89db','Stealth','lg',w=112)}{ARROW}{cell('0819','Cheap Shot','lg',w=112)}{ARROW}{cell('f8bc','SnD','lg',w=112)}{ARROW}{cell('7ac9','loop','lg',w=112)}</div>
<div class="row"><div class="lvl" style="color:#7be08e">Lv<br>30</div>{cell('baac','Blade Flurry','lg','new',w=132)}<div class="arr" style="margin:0 0 26px">+</div>{cell('1789','Evasion','lg','new',w=112)}<div class="eq">= kill <b>2 mobs</b> at once</div></div></div>'''
    oh = [('1789', 'Evasion', '2+ mobs'), ('44a5', 'Gouge', '&rarr; bandage'), ('5770', 'Sprint', 'run'), ('202b', 'Vanish', 'DoTs break it'), ('e8a5', 'Kick', 'stop casters')]
    ohh = ''.join(f'<div class="ohc">{ic(h,"md")}<div><b class="x3d" style="color:var(--cream)">{n}</b><span>{s}</span></div></div>' for h, n, s in oh)
    ohp = f'<div class="panel" style="--edge1:#ef5e48;--edge2:#4a1a12"><div class="ph"><h2 class="disp x3d" style="color:#ffb7a8">OH NO! BUTTONS</h2></div><div class="oh" style="height:calc(100% - 64px)">{ohh}</div></div>'
    body = css + f'<div class="g">{core}{rot}{ohp}</div>'
    return frame(3, 'ROTATION &amp; BUTTONS', 'combo loop &middot; panic buttons', body)

# =================================================================== 04 LEVEL PLAN
def levelplan():
    d = CLS['3']
    levels = [1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
    prio = ['must', 'skip', 'good', 'must', 'good', 'must', 'good', 'good', 'good', 'skip', 'must', 'must', 'good', 'must', 'skip', 'must']
    labels = {1: 'start', 10: 'full rotation', 20: 'poison quest!', 22: 'escape button', 26: 'new opener', 30: 'Blade Flurry'}
    ys = sorted(set(a['bbox'][1] for a in d if 150 < a['bbox'][1] < 1600 and a['bbox'][0] < 600))
    rows = []
    for i, y in enumerate(ys[:16]):
        left = [a for a in d if abs(a['bbox'][1] - y) < 6 and a['bbox'][0] < 700 and a['bbox'][1] > 150]
        right = [a for a in d if abs(a['bbox'][1] - y) < 6 and a['bbox'][0] > 1000]
        left.sort(key=lambda a: a['bbox'][0]); right.sort(key=lambda a: a['bbox'][0])
        rows.append((levels[i], prio[i], left, right))
    # talent points the guide spends, one per level (see the TALENT ORDER on slide 2)
    PT = ([('Improved Sinister Strike', 2)] * 0)
    seq = []
    for name, pts in (('Improved Sinister Strike', 2), ('Improved Eviscerate', 3), ('Precision', 2), ('Deflection', 3), ('Riposte', 1),
                      ('Precision', 1), ('Endurance', 1), ('Improved Sprint', 2), ('Flawless Execution', 1),
                      ('Dual Wield Specialization', 4), ('Blade Flurry', 1)):
        have = sum(1 for n, _ in seq if n == name)
        for k in range(pts):
            seq.append((name, have + k + 1))
    per_level = {10 + i: seq[i] for i in range(len(seq))}

    def row_html(lv, pr, left, right):
        li = ''.join(ic(a['h'], 'md', 'new' if a['cls'] == 'new' else ('amber' if a['cls'] == 'amber' else ''), tt=(abil(a['h'], lv) or False)) for a in left)
        pts = [per_level[l] for l in (lv, lv + 1) if l in per_level][:len(right)]
        ri = ''.join(ic(a['h'], 'md', 'amber' if a['cls'] == 'amber' else ('new' if a['cls'] else ''),
                        tt=(talent(*pts[i]) if i < len(pts) else False)) for i, a in enumerate(right))
        lab = labels.get(lv, '')
        tp = f'<div class="tp">{ri}</div>' if ri else '<div class="tp"></div>'
        return f'<div class="lr {pr}"><div class="lv disp">{lv}</div><div class="li">{li}</div><div class="lb">{lab}</div>{tp}</div>'
    css = '''<style>
.cols{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:2px}
.lr{display:flex;align-items:center;gap:16px;height:88px;padding:0 14px 0 0;margin-bottom:9px;border-radius:10px;border-left:10px solid var(--c);background:linear-gradient(90deg,var(--bgc),rgba(17,21,36,.88) 60%)}
.lr.must{--c:var(--must);--bgc:rgba(70,24,18,.9)} .lr.good{--c:var(--good);--bgc:rgba(58,40,12,.85)} .lr.skip{--c:var(--skip);--bgc:rgba(34,32,28,.9)}
.lr .lv{font-size:58px;width:74px;text-align:center;color:var(--rogue);text-shadow:3px 3px 0 var(--brown),4px 4px 0 #04060d;flex:none}
.lr .li{display:flex;gap:11px;flex:none}
.lr .lb{font:800 italic 26px 'Barlow Condensed';letter-spacing:.04em;text-transform:uppercase;color:var(--cream);flex:1;white-space:nowrap}
.lr .tp{display:flex;gap:10px;margin-left:auto;flex:none}
.lr .tp::before{content:'';}
.lr .ic{--s:64px}
</style>'''
    body = css + f'''<div class="panel" style="height:100%;padding-bottom:12px"><div class="ph" style="margin-bottom:12px"><span class="tag" style="font-size:26px">class trainer abilities</span>
<div class="legend" style="margin-left:auto"><span><i style="background:var(--must)"></i>must train</span><span><i style="background:var(--good)"></i>good</span><span><i style="background:var(--skip)"></i>skip-able</span><span><i class="ol"></i>new ability</span><span class="yel">right side = talent points</span></div></div>
<div class="cols"><div>{''.join(row_html(*r) for r in rows[:8])}</div><div>{''.join(row_html(*r) for r in rows[8:])}</div></div></div>'''
    return frame(4, 'LEVEL PLAN', 'level 1 &rarr; 30', body)

# =================================================================== 05 POISONS / WEAPONS / STATS
def gear():
    css = '''<style>
.g{display:grid;grid-template-columns:900px 1fr;grid-template-rows:minmax(0,1fr);gap:22px;height:100%}
.col{display:flex;flex-direction:column;gap:20px}
.pg{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.pz{display:flex;align-items:center;gap:16px;padding:8px 16px;border-radius:12px;background:linear-gradient(160deg,rgba(32,38,58,.85),rgba(17,21,36,.85));border:1px solid rgba(227,175,74,.2);height:88px}
.pz.hi{border:3px solid var(--rogue);box-shadow:0 0 24px rgba(255,245,106,.3);grid-column:1/3;height:104px}
.pz b{display:block;font:900 italic 32px 'Barlow Condensed';text-transform:uppercase;line-height:1}
.pz span{font:600 21px 'Barlow Condensed';letter-spacing:.06em;text-transform:uppercase;color:var(--mute)}
.pz .plus{width:56px;height:56px;border-radius:7px;border:3px solid var(--gold-d);background:#17120a;display:flex;align-items:center;justify-content:center;font:900 italic 30px 'Barlow Condensed';color:var(--good);box-shadow:0 0 0 2px #04060d,4px 4px 0 2px var(--brown)}
.wp{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.wc{display:flex;align-items:center;gap:20px;padding:10px 20px;border-radius:12px;background:linear-gradient(160deg,rgba(32,38,58,.9),rgba(17,21,36,.9));border-top:6px solid var(--rogue)}
.wc.oh{border-top-color:var(--cyan)}
.wc h4{font:900 italic 34px 'Barlow Condensed';text-transform:uppercase;line-height:1;color:var(--rogue)}
.wc.oh h4{color:var(--cyan)}
.wc .sp{font:900 italic 40px 'Barlow Condensed';text-transform:uppercase;line-height:1;margin:2px 0 2px}
.wc span.d{font:500 20px Inter;color:var(--mute)}
.can{margin-top:12px;display:flex;flex-wrap:wrap;gap:9px;align-items:center}
.can .c{font:700 20px 'Barlow Condensed';letter-spacing:.1em;text-transform:uppercase;padding:3px 13px;border-radius:6px;background:rgba(255,255,255,.07);border:1px solid rgba(227,175,74,.3)}
.can .c.new{background:rgba(255,245,106,.15);color:var(--rogue);border-color:var(--rogue)}
.can .l{font:700 20px 'Barlow Condensed';letter-spacing:.2em;color:var(--mute);margin-right:6px}
.bars{display:flex;flex-direction:column;gap:14px;margin-top:2px}
.br{display:grid;grid-template-columns:200px 1fr 70px;align-items:center;gap:16px}
.br .n{font:800 28px 'Barlow Condensed';letter-spacing:.04em;text-transform:uppercase}
.br .t{height:30px;background:rgba(255,255,255,.06);border-radius:6px;overflow:hidden;transform:skewX(-14deg)}
.br .t i{display:block;height:100%;border-radius:6px}
.br .v{font:900 italic 44px 'Barlow Condensed';text-align:left;line-height:1}
.hit{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:10px}
.hit div{text-align:center;padding:10px 8px 8px;border-radius:12px;background:linear-gradient(160deg,rgba(32,38,58,.9),rgba(17,21,36,.9))}
.hit b{display:block;font:900 italic 70px 'Barlow Condensed';line-height:.9}
.hit span{font:700 22px 'Barlow Condensed';letter-spacing:.14em;text-transform:uppercase;color:var(--mute)}
.sh{font:900 italic 34px 'Barlow Condensed';text-transform:uppercase;color:var(--cream);margin:14px 0 2px;letter-spacing:.03em}
.ex{display:flex;align-items:center;gap:20px;padding:8px 18px;border-radius:12px;background:linear-gradient(160deg,rgba(32,38,58,.9),rgba(17,21,36,.9));margin-top:10px}
.ex b{display:block;font:900 italic 34px 'Barlow Condensed';text-transform:uppercase;line-height:1}
.ex span{font:600 24px 'Barlow Condensed';letter-spacing:.06em;color:var(--mute)}
.ex.win{border:2px solid #7be08e;box-shadow:0 0 22px rgba(123,224,142,.25)}
</style>'''
    poisons = [('1cdc 1cdc', 'Instant &times;2', 'leveling: both weapons', True), ('b915', 'Deadly', 'off hand in dungeons', False), ('dd2a', 'Crippling', 'slow &middot; PVP', False),
               ('efd2', 'Wound', 'less healing &middot; PVP', False), ('a155', 'Mind-numbing', 'slower casts', False), ('PLUS', 'Thistle Tea', 'energy at 0 &rarr; spend', False)]
    ph = ''
    for h, n, s, hi in poisons:
        if h == 'PLUS': icon = '<div class="plus" data-tt="it:7676">+100</div>'
        else: icon = ''.join(ic(x, 'lg' if hi else 'sm') for x in h.split())
        ph += f'<div class="pz {"hi" if hi else ""}">{icon}<div><b class="{"yel" if hi else ""}">{n}</b><span>{s}</span></div></div>'
    left = f'''<div class="col"><div class="panel"><div class="ph"><div style="margin-right:2px">{ic('1cdc','md')}</div><h2 class="disp x3d">POISONS</h2><span class="tag">Lv 20 &middot; rogue class quest</span></div><div class="pg">{ph}</div></div>
<div class="panel" style="flex:1"><div class="ph"><h2 class="disp x3d">WEAPONS</h2></div>
<div class="wp"><div class="wc">{ic('3023','lg')}<div><h4>Main hand</h4><div class="sp">SLOW</div><span class="d">bigger Sinister Strike</span></div></div>
<div class="wc oh">{ic('5c38','lg')}<div><h4>Off hand</h4><div class="sp">FAST</div><span class="d">or just highest DPS</span></div></div></div>
<div class="can"><span class="l">CAN USE</span><span class="c">swords</span><span class="c new">axes (new)</span><span class="c">daggers</span><span class="c">maces</span><span class="c">fist</span><span class="c">thrown</span><span class="c">bows</span><span class="c">crossbows</span><span class="c">guns</span></div></div></div>'''
    bars = [('1% Crit', 23, 100, 'linear-gradient(90deg,#c9402d,#ff6a54)', 'var(--must)'), ('1% Hit', 18, 78, 'linear-gradient(90deg,#d99a1e,#ffc94a)', 'var(--good)'),
            ('Agility', 1.8, 8, 'var(--rogue)', 'var(--rogue)'), ('Strength', 1, 4.3, 'var(--rogue)', 'var(--rogue)'), ('Attack Power', 1, 4.3, 'var(--rogue)', 'var(--rogue)')]
    bh = ''.join(f'<div class="br"><div class="n">{n}</div><div class="t"><i style="width:{w}%;background:{c}"></i></div><div class="v" style="color:{tc}">{v}</div></div>' for n, v, w, c, tc in bars)
    right = f'''<div class="panel" style="height:100%"><div class="ph"><h2 class="disp x3d">STATS</h2><span class="tag">AP-equivalent value</span></div>
<div class="bars">{bh}</div><div class="mut" style="font:700 22px 'Barlow Condensed';letter-spacing:.1em;text-transform:uppercase;margin-top:10px">tie &rarr; <span class="yel">more Stamina wins</span></div>
<div class="sh">HIT TARGETS</div><div class="hit"><div><b style="color:var(--good)">5%</b><span>mobs</span></div><div><b style="color:var(--must)">8%</b><span>raid boss</span></div><div><b style="color:var(--mount)">27%</b><span>off-hand</span></div></div>
<div class="sh">EXAMPLE</div>
<div class="ex win">{ic('05fe','md','new')}<div><b>Grave Shroud <span style="color:#7be08e">&#10004;</span></b><span>3 Str + 2 Agi = 6.6</span></div></div>
<div class="ex">{ic('63b5','md')}<div><b>Catacomb Cloak</b><span>6–10 AP</span></div></div></div>'''
    return frame(5, 'POISONS &middot; WEAPONS &middot; STATS', 'what to wield &amp; stack', css + f'<div class="g">{left}{right}</div>')

# =================================================================== 06 DUNGEON WEAPONS
def dungeons():
    D = [
        ('Wailing Caverns', '—', 'n', [('e450', 'Stinging Viper', 0), ('5c38', 'Tail Spike', 0), ('77a2', 'Wingblade', 1)]),
        ('The Deadmines', '—', 'n', [('3023', 'Buzz Saw', 0), ('00e5', 'Dull Sawblade', 0), ('dfd6', 'Goblin Hammer', 0), ('3023', 'Thief\'s Blade', 0), ('3023', 'Cruel Barb', 0), ('89f7', 'Cookie\'s Tenderizer', 0)]),
        ('Hall of Thanes', '13–18', 'a', [('e628', 'Durgen\'s Crescent Axe', 0)]),
        ('Ragefire Chasm', '13–18', 'h', [('f6a8', 'Bone Knuckles', 0), ('d3cc', 'Cursed Felblade', 0), ('0f58', 'Chanting Blade', 0), ('4052', 'Hammer of Orgrimmar', 1)]),
        ('Ruins of Lordaeron', '16–20', 'n', [('3580', 'Meathook Slicer', 0), ('77a2', 'Vileblood Scimitar', 0), ('47b3', 'Plaguefang', 1), ('cf1a', 'Edwards\' Knife', 1)]),
        ('Shadowfang Keep', '22–30', 'n', [('ada6', 'Butcher\'s Cleaver', 0), ('77a2', 'Butcher\'s Slicer', 0), ('699c', 'Baron\'s Scepter', 0), ('0f58', 'Meteor Shard', 0)]),
        ('Blackfathom Deeps', '24–32', 'n', [('bbe9', 'Darkwater Talwar', 0), ('3580', 'Bite of Serra\'kis', 0)]),
        ('The Stockade', '24–32', 'n', [('8629', 'Prison Shank', 0), ('f602', 'Hamhock\'s Cleaver', 0)]),
        ('Gnomeregan', '29–38', 'n', [('e86d', 'Toxic Revenger', 0), ('be0b', 'Electrocutioner Leg', 0)]),
        ('Excavation Site · Dalaran', '24–33', 'n', []),
    ]
    css = '''<style>
.dg{display:grid;grid-template-columns:1fr 1fr;grid-template-rows:repeat(5,minmax(0,1fr));gap:11px;height:100%}
.dc{position:relative;padding:8px 18px 6px 22px;border-radius:12px;border-left:9px solid #7a6a3a;overflow:hidden;background:linear-gradient(160deg,rgba(30,34,52,.92),rgba(14,18,32,.92))}
.dc.a{border-left-color:#4a9dff}.dc.h{border-left-color:#ef5e48}
.dc .t{display:flex;justify-content:space-between;align-items:baseline}
.dc h3{font:900 italic 30px 'Barlow Condensed';text-transform:uppercase;letter-spacing:.02em}
.dc .lv{font:900 italic 30px 'Barlow Condensed';color:var(--rogue);text-shadow:2px 2px 0 var(--brown)}
.dc .is{display:flex;gap:8px;margin-top:4px}
.dc .cell .lab{font-size:14px;margin-top:6px;width:126px;letter-spacing:.02em}
.dc .ic{--s:56px}
.dc .none{font:600 italic 26px 'Barlow Condensed';color:var(--mute);letter-spacing:.06em;margin-top:12px;text-transform:uppercase}
.lg2{display:flex;gap:20px;align-items:center}
</style>'''
    cards = ''
    for n, lv, f, items in D:
        inner = ''.join(cell(h, nm.replace(' ', '<br>', 1) if len(nm) > 14 else nm, 'md', '', red=bool(r), w=126) for h, nm, r in items)
        inner = f'<div class="is">{inner}</div>' if items else '<div class="none">drops not known yet</div>'
        cards += f'<div class="dc {f}"><div class="t"><h3>{n}</h3><div class="lv">{lv}</div></div>{inner}</div>'
    lgd = '<div class="legend" style="margin-left:auto"><span><i style="background:var(--coral)"></i>red = HORDE quest</span><span><i style="background:#4a9dff"></i>Alliance dungeon</span><span><i style="background:#ef5e48"></i>Horde dungeon</span></div>'
    body = css + f'<div class="dg">{cards}</div>'
    return frame(6, 'DUNGEON WEAPONS', 'quest &amp; drop upgrades &middot; <span style="color:var(--coral)">red = HORDE quest</span>', body, extra_right='')

# =================================================================== 07 RACES
def races():
    A = [('Gnome', 'GREAT', 'great', [('590d', 'Eureka!'), ('8b7d', '105 energy'), ('a623', 'Escape Artist')], 'best Alliance PVP', '#7be08e'),
         ('Night Elf', 'GREAT', 'great', [('89fa', 'crit CD'), ('9b8e', 'Quickness'), ('7ff7', 'Shadowmeld')], 'PVE + PVP', '#7be08e'),
         ('Human', 'SOLID', 'solid', [('0bef', '+2% crit swords'), ('acd9', 'Will to Survive'), ('6801', 'Perception')], 'best Ally PVE if swords win', '#6db6ff'),
         ('Dwarf', 'PVP', 'pvp', [('7296', 'Mace Spec'), ('e8df', 'Stoneform')], 'clean Vanish vs bleeds', '#d9b26a'),
         ('Skyborne', 'WEAKEST', 'weak', [('c8d3', '+1% haste'), ('8382', 'Walk on Air'), ('e5f1', 'Ley Line')], '', '#ef5e48')]
    Hh = [('Orc', 'DECENT', 'decent', [('1365', 'Blood Fury'), ('f865', 'Axe Spec'), ('d744', 'short stuns'), ('1852', 'Shatter Curse')], 'decent overall', '#f5b941'),
          ('Forsaken', 'PVP', 'pvp', [('7c34', 'WotF'), ('59f8', 'Touch of Grave'), ('c0c3', 'Cannibalize')], 'top PVP, ok PVE', '#d9b26a'),
          ('Troll', 'OK', 'ok', [('e4b2', 'Berserking'), ('e62a', 'Rapid Regen'), ('9e75', 'Beast Slaying')], 'Orc / Forsaken better', '#a39b86'),
          ('Skyborne', 'WEAKEST', 'weak', [('c8d3', '+1% haste'), ('4e60', 'Skysight'), ('8382', 'Walk on Air')], '', '#ef5e48')]
    css = '''<style>
.g{display:grid;grid-template-columns:1fr 1fr;gap:22px;height:100%}
.fac{display:flex;flex-direction:column;gap:11px}
.fh{font:900 italic 60px 'Barlow Condensed';text-transform:uppercase;letter-spacing:.03em;line-height:.9;display:flex;align-items:center;gap:16px}
.fh::after{content:'';flex:1;height:5px;background:linear-gradient(90deg,currentColor,transparent);opacity:.7;transform:skewX(-30deg)}
.rc{display:grid;grid-template-columns:230px 1fr;gap:16px;align-items:center;padding:12px 18px 12px 22px;border-radius:12px;border-left:10px solid var(--c);background:linear-gradient(90deg,var(--bgc),rgba(15,19,34,.92) 55%);flex:1}
.rc h3{font:900 italic 44px 'Barlow Condensed';text-transform:uppercase;line-height:1;margin-bottom:6px}
.rc .nt{font:600 21px 'Barlow Condensed';letter-spacing:.05em;color:var(--mute);margin-top:8px;text-transform:uppercase;line-height:1.1}
.rc .is{display:flex;gap:6px;flex-wrap:nowrap}
.rc .ic{--s:64px}
.rc .cell .lab{font-size:15px;width:100px;margin-top:9px;letter-spacing:.02em}
.rc.skip-card{opacity:.92}
</style>'''
    RAC_SLUG = {'Gnome': 'gnome', 'Night Elf': 'night-elf', 'Human': 'human', 'Dwarf': 'dwarf', 'Orc': 'orc',
                'Forsaken': 'undead', 'Troll': 'troll'}
    RAC_NAME = {'Eureka!': 'Eureka!', '105 energy': 'Expansive Mind', 'Escape Artist': 'Escape Artist', 'crit CD': "Elune's Light",
                'Quickness': 'Quickness', 'Shadowmeld': 'Shadowmeld', '+2% crit swords': 'Sword Specialization',
                'Will to Survive': 'Will to Survive', 'Perception': 'Perception', 'Mace Spec': 'Mace Specialization',
                'Stoneform': 'Stoneform', '+1% haste': 'Wind Blessed', 'Walk on Air': 'Walk on Air', 'Ley Line': 'Read Ley Line',
                'Skysight': 'Skysight', 'Blood Fury': 'Blood Fury', 'Axe Spec': 'Axe Specialization', 'short stuns': 'Hardiness',
                'Shatter Curse': 'Shatter Curse', 'WotF': 'Will of the Forsaken', 'Touch of Grave': 'Touch of the Grave',
                'Cannibalize': 'Cannibalize', 'Berserking': 'Berserking', 'Rapid Regen': 'Rapid Regeneration',
                'Beast Slaying': 'Beast Slaying'}

    def racial(race, label):
        if race == 'Skyborne':
            slug = 'high-order-skyborne' if label in ('Ley Line',) or getattr(racial, 'ally', False) else 'windshaper-skyborne'
        else:
            slug = RAC_SLUG[race]
        return 'ra:%s:%s' % (slug, RAC_NAME[label])

    def card(n, bt, bc, ic_list, note, c):
        bgc = {'#7be08e': 'rgba(18,60,34,.7)', '#6db6ff': 'rgba(16,40,76,.7)', '#d9b26a': 'rgba(60,46,18,.7)', '#ef5e48': 'rgba(70,24,18,.7)', '#f5b941': 'rgba(60,42,12,.7)', '#a39b86': 'rgba(40,38,32,.7)'}[c]
        racial.ally = any(l == 'Ley Line' for _, l in ic_list)
        icons = ''.join(cell(h, nm, 'md', w=100, tt=racial(n, nm)) for h, nm in ic_list)
        nt = f'<div class="nt">{note}</div>' if note else ''
        return f'<div class="rc" style="--c:{c};--bgc:{bgc}"><div><h3>{n}</h3><span class="chip {bc}">{bt}</span>{nt}</div><div class="is">{icons}</div></div>'
    ally = f'<div class="fac"><div class="fh" style="color:#4a9dff">ALLIANCE</div>{"".join(card(*r) for r in A)}</div>'
    hord = f'<div class="fac"><div class="fh" style="color:#ef5e48">HORDE</div>{"".join(card(*r) for r in Hh)}<div class="panel" style="padding:14px 22px;--c:16px"><div style="display:flex;align-items:center;gap:16px"><span class="disp x3d" style="font-size:44px">NO TAUREN</span><span class="mut" style="font:600 21px \'Barlow Condensed\';letter-spacing:.1em;text-transform:uppercase">Tauren can\'t roll Rogue</span></div></div></div>'
    return frame(7, 'RACES', 'no Tauren &middot; ranked for rogues', css + f'<div class="g">{ally}{hord}</div>')

# =================================================================== 08 PROFESSIONS
def professions():
    P = [('S', 'First Aid', 'bandage after CC &middot; potions', 'camp: Stamina', 'e9a2'), ('A', 'Skinning', 'skin as you kill', 'camp: +2% crit', 'eaf3'),
         ('A', 'Leatherworking', 'early leather gear', 'camp: rested XP tent', '4b66'), ('B', 'Mining', 'stealth to ore &middot; gold', 'camp: Attack Power', '417f'),
         ('B', 'Herbalism', 'Fadeleaf for Blind', 'camp: Int (useless)', '88ca'), ('B', 'Cooking', '+5% XP food &middot; campfires', 'camp: enables camps', 'a8e1'),
         ('C', 'Alchemy', 'Agility / Strength elixirs', 'camp: useless', '9331'), ('C', 'Fishing', 'chill &middot; ninja fish', 'camp: % all stats', '5310'),
         ('C', 'Enchanting', 'pricey &middot; anyone can enchant', 'camp: stats + resists', '0aa1'), ('C', 'Engineering', 'PVP bombs &middot; pricey', 'camp: no poisons', '27ea'),
         ('D', 'Tailoring', 'cloth &middot; not for us', 'camp: Spirit', '58f1'), ('D', 'Blacksmithing', 'mail/plate &middot; not for us', 'camp: Strength', 'ee21')]
    css = '''<style>
.flow{display:flex;align-items:center;justify-content:center;gap:24px;padding:6px 0 4px}
.pgrid{display:grid;grid-template-columns:1fr 1fr;grid-auto-flow:row;gap:9px;margin-top:6px}
.pr{display:flex;align-items:center;gap:20px;padding:6px 18px;height:98px;border-radius:12px;border-left:10px solid var(--c);background:linear-gradient(90deg,var(--bgc),rgba(15,19,34,.92) 60%)}
.pr.S{--c:#fff56a;--bgc:rgba(70,62,12,.75)}.pr.A{--c:#7be08e;--bgc:rgba(18,60,34,.7)}.pr.B{--c:#6db6ff;--bgc:rgba(16,40,76,.7)}.pr.C{--c:#f5b941;--bgc:rgba(60,42,12,.7)}.pr.D{--c:#ef5e48;--bgc:rgba(70,24,18,.7)}
.pr .ic{--s:76px}
.pr h3{font:900 italic 35px 'Barlow Condensed';text-transform:uppercase;display:flex;align-items:center;gap:12px;line-height:1}
.pr .d{font:500 19px Inter;color:#cfc9b4;margin-top:3px}
.pr .cp{font:800 19px 'Barlow Condensed';letter-spacing:.08em;text-transform:uppercase;color:var(--cyan);margin-top:2px}
.tent{width:84px;height:84px;border-radius:7px;border:3px solid var(--gold-d);background:linear-gradient(160deg,#10281f,#08140f);display:flex;align-items:center;justify-content:center;box-shadow:0 0 0 2px #04060d,4px 4px 0 2px var(--brown)}
.gear4{display:flex;gap:6px}
.big .lab{font-size:22px}
.tiers{display:flex;gap:10px;margin-left:auto;align-items:center}
</style>'''
    tent = '<div class="tent"><svg viewBox="0 0 64 64" width="56" height="56"><path d="M32 8 6 54h52z" fill="#f2703a"/><path d="M32 8 58 54H40z" fill="#c84a22"/><path d="M32 30 22 54h20z" fill="#2b0f06"/><path d="M32 8v-4" stroke="#fff56a" stroke-width="3"/></svg></div>'
    flow = f'''<div class="flow big">{cell('eaf3','Skinning','lg',w=170)}{ARROW}{cell('4b66','Leatherwork','lg',w=190)}{ARROW}
<div class="cell" style="width:420px"><div class="gear4">{ic('5551','md')}{ic('9f09','md')}{ic('955f','md')}{ic('3762','md')}</div><div class="lab">early gear</div></div>{ARROW}
<div class="cell" style="width:190px">{tent.replace('width:84px;height:84px','')}<div class="lab">Camp Tents</div></div></div>'''
    tiers = '<div class="tiers"><span class="legend">tier</span>' + ''.join(f'<span class="badge t-{t}">{t}</span>' for t in 'SABCD') + '</div>'
    rows = ''.join(f'<div class="pr {t}">{ic(h,"md")}<div><h3><span class="badge t-{t}">{t}</span>{n}</h3><div class="d">{d}</div><div class="cp">{c}</div></div></div>' for t, n, d, c, h in P)
    body = css + f'''<div class="panel" style="height:100%;padding-top:14px"><div class="ph" style="margin-bottom:0"><span class="tag" style="font-size:28px">2 main + all 3 secondary</span>{tiers}</div>
{flow}<div class="pgrid">{rows}</div></div>'''
    return frame(8, 'PROFESSIONS', 'tier list &middot; camp bonuses', body)

# =================================================================== 09 MACROS + TRAINERS
def macros():
    M = [(['f7b4', '7ac9'], 'main button', ['#showtooltip Sinister Strike', '/cast Riposte', '/cast Sinister Strike']),
         (['2097', '0819'], 'loot + open', ['#showtooltip Cheap Shot', '/cast Pick Pocket', '/cast Cheap Shot']),
         (['2097', 'a1e7'], 'loot + open', ['#showtooltip Garrote', '/cast Pick Pocket', '/cast Garrote']),
         (['2097', '18a1'], 'loot + open', ['#showtooltip Ambush', '/cast Pick Pocket', '/cast Ambush']),
         (['7abb'], 'PVP: find stealthers', ['#showtooltip Sap', '/cleartarget', '/targetenemyplayer', '/cast [harm, nodead] sap', '/cast Pick Pocket', '/stopattack'])]
    def colr(line):
        e = esc(line)
        if line.startswith('#'): return f'<span style="color:#b79cff">{e}</span>'
        if line.startswith('/cast'):
            a, b = e.split(' ', 1)
            return f'<span style="color:#7be08e">{a}</span> <span style="color:var(--cream)">{b}</span>'
        return f'<span style="color:var(--cyan)">{e}</span>'
    css = '''<style>
.g{display:grid;grid-template-columns:1fr 700px;gap:22px;height:100%}
.mc{display:grid;grid-template-columns:150px 1fr;gap:16px;align-items:center;margin-bottom:11px}
.mi{display:flex;flex-direction:column;align-items:center}
.mi .ics{display:flex;gap:10px}
.mi .ic{--s:60px}
code{display:block;font:500 21px/1.35 'JetBrains Mono',monospace;background:#03050b;border:1px solid rgba(227,175,74,.35);border-radius:10px;padding:10px 18px;white-space:pre;box-shadow:inset 0 0 24px rgba(0,0,0,.6)}
.steps{display:flex;gap:10px;align-items:center;margin:2px 0 12px}
.st{display:flex;align-items:center;gap:12px;padding:8px 16px;border-radius:8px;background:rgba(255,245,106,.1);border:1px solid rgba(255,245,106,.5);font:800 22px 'Barlow Condensed';letter-spacing:.08em;text-transform:uppercase}
.st b{display:inline-flex;width:32px;height:32px;align-items:center;justify-content:center;border-radius:50%;background:var(--rogue);color:#0a0c14;font:900 italic 22px 'Barlow Condensed'}
.tb{width:100%;border-collapse:collapse;margin-top:6px}
.tb th{font:800 21px 'Barlow Condensed';letter-spacing:.12em;text-transform:uppercase;color:var(--mute);padding:0 0 10px;text-align:center}
.tb th:first-child{text-align:left}
.tb td{height:98px;border-top:1px solid rgba(227,175,74,.22);text-align:center}
.tb td:first-child{text-align:left;font:700 30px 'Barlow Condensed';letter-spacing:.03em;text-transform:uppercase;white-space:nowrap}
.tb td:first-child small{display:block;font:500 17px 'JetBrains Mono';color:var(--mute);letter-spacing:0;text-transform:none}
.f{display:inline-block;width:14px;height:14px;border-radius:50%;margin-right:10px}
.dt{display:inline-block;width:38px;height:38px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#fffbb8,var(--rogue) 55%,#c4a812);box-shadow:0 0 16px rgba(255,245,106,.7)}
</style>'''
    mac = ''
    for icons, lab, lines in M:
        ics = ''.join(ic(h, 'md') for h in icons)
        mac += f'<div class="mc"><div class="mi"><div class="ics">{ics}</div><div class="lab">{lab}</div></div><code>{chr(10).join(colr(l) for l in lines)}</code></div>'
    T = [('Ironforge', '61.6, 89.6', 'a', 'axe mace fist xbow gun'), ('Stormwind', '63.8, 69', 'a', 'sword xbow'), ('Darnassus', '57.6, 46.6', 'a', 'fist bow'),
         ('Orgrimmar', '81.6, 19.6', 'h', 'axe fist bow'), ('Undercity', '57, 32.8', 'h', 'sword xbow'), ('Thunder Bluff', '41.2, 61.4', 'h', 'mace gun')]
    cols = ['sword', 'axe', 'mace', 'fist', 'bow', 'xbow', 'gun']
    tb = '<table class="tb"><tr><th></th>' + ''.join(f'<th>{c.title()}</th>' for c in cols) + '</tr>'
    for n, co, f, w in T:
        fc = '#4a9dff' if f == 'a' else '#ef5e48'
        tb += f'<tr><td><span class="f" style="background:{fc}"></span>{n}<small>{co}</small></td>' + ''.join(f'<td>{"<span class=dt></span>" if c in w.split() else ""}</td>' for c in cols) + '</tr>'
    tb += '</table>'
    body = css + f'''<div class="g"><div class="panel" style="height:100%"><div class="ph" style="margin-bottom:8px"><h2 class="disp x3d">MACROS</h2><span class="tag">copy &middot; paste &middot; play</span></div>
<div class="steps"><div class="st"><b>1</b>type /macro</div><span class="arr" style="font-size:36px">&#10132;</span><div class="st"><b>2</b>New</div><span class="arr" style="font-size:36px">&#10132;</span><div class="st"><b>3</b>paste</div></div>{mac}</div>
<div class="panel" style="height:100%"><div class="ph"><h2 class="disp x3d">WEAPON TRAINERS</h2></div>{tb}
<div class="legend" style="margin-top:22px"><span><i style="background:#4a9dff"></i>Alliance</span><span><i style="background:#ef5e48"></i>Horde</span><span class="yel">&#9679; = trains it</span></div></div></div>'''
    return frame(9, 'MACROS &amp; TRAINERS', 'one-button rogue', body)

# =================================================================== 10 AFTER 30
def after30():
    d = CLS['9']
    L = [32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60]
    P = ['good', 'must', 'skip', 'good', 'mount', 'good', 'skip', 'good', 'skip', 'good', 'skip', 'good', 'skip', 'skip', 'rogue']
    cells = {l: [] for l in L}
    for a in d:
        x, y = a['bbox'][0], a['bbox'][1]
        if y < 190 or y > 700: continue
        col = 0 if x < 500 else (1 if x < 900 else 2)
        if y < 260: row = 0
        elif y < 340: row = 1
        elif y < 420: row = 2
        elif y < 500: row = 3
        else: row = 4
        cells[L[row * 3 + col]].append(a)
    for l in L: cells[l].sort(key=lambda a: (a['bbox'][1] // 40, a['bbox'][0]))
    css = '''<style>
.g3{display:grid;grid-template-columns:repeat(3,1fr);grid-auto-rows:136px;gap:14px}
.lc{display:flex;align-items:center;gap:14px;padding:0 14px 0 0;border-radius:12px;border-left:10px solid var(--c);background:linear-gradient(90deg,var(--bgc),rgba(15,19,34,.92) 62%)}
.lc.must{--c:var(--must);--bgc:rgba(70,24,18,.9)}.lc.good{--c:var(--good);--bgc:rgba(58,40,12,.85)}.lc.skip{--c:var(--skip);--bgc:rgba(34,32,28,.9)}
.lc.mount{--c:var(--mount);--bgc:rgba(48,32,78,.85)}.lc.rogue{--c:var(--rogue);--bgc:rgba(70,62,12,.8)}
.lc .lv{font:900 italic 56px 'Barlow Condensed';color:var(--rogue);width:96px;text-align:center;text-shadow:3px 3px 0 var(--brown),4px 4px 0 #04060d;flex:none}
.lc .is{display:flex;flex-wrap:wrap;gap:12px;align-content:center}
.lc .ic{--s:68px}
.lc.rogue{align-items:center}
.lc.rogue .is{max-width:300px;gap:8px}
.lc.rogue .ic{--s:54px}
.lc .mt{position:absolute;right:12px;top:8px;font:800 15px 'Barlow Condensed';letter-spacing:.14em;color:var(--mount);text-transform:uppercase}
.lc{position:relative}
.cred{margin-top:16px;padding:14px 22px;border-radius:10px;background:rgba(5,8,18,.7);border:1px solid rgba(227,175,74,.25);font:500 18px/1.4 Inter;color:var(--mute)}
.cred b{color:var(--gold)}
</style>'''
    cards = ''
    for i, l in enumerate(L):
        p = P[i]
        # 60 is the big card: lay out in grid-row span handled by order
        icons = ''.join(ic(a['h'], 'md', 'new' if a['cls'] else '', tt=(abil(a['h'], l) or False)) for a in cells[l])
        mt = '<span class="mt">buy mount first</span>' if p == 'mount' else ''
        cards += f'<div class="lc {p}"><div class="lv">{l}</div><div class="is">{icons}</div>{mt}</div>'
    leg = '<div class="legend" style="margin-left:auto"><span><i style="background:var(--must)"></i>must</span><span><i style="background:var(--good)"></i>good</span><span><i style="background:var(--mount)"></i>40: buy mount first</span><span><i class="ol"></i>new ability</span></div>'
    body = css + f'''<div class="panel" style="padding-bottom:18px"><div class="ph" style="margin-bottom:12px"><span class="tag" style="font-size:26px">class trainer abilities &middot; 32 &rarr; 60</span>{leg}</div><div class="g3">{cards}</div></div>
'''
    return frame(10, 'AFTER 30', 'level 32 &rarr; 60', body)

# =================================================================== write
save(1, 'cover', cover())
save(2, 'talent-builds', builds())
save(3, 'rotation', rotation())
save(4, 'level-plan', levelplan())
save(5, 'poisons-weapons-stats', gear())
save(6, 'dungeon-weapons', dungeons())
save(7, 'races', races())
save(8, 'professions', professions())
save(9, 'macros-trainers', macros())
save(10, 'after-30', after30())
print('built', len(glob.glob('slides/*.html')), 'slides')
