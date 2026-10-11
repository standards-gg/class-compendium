"""Build the landing page (index.html), the slide viewer (viewer.html) and data/decks.json.

  python build_site.py

Needs: slides/<class>/*.html and thumbs/<class>/*.jpg for the generated classes (build_decks.py + render_decks.py),
the hand-made Combat Rogue deck (slides/01-*.html ... + png/*.png) and data/classes.json.
"""
import glob
import html
import json
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
E = lambda s: html.escape(str(s), quote=False)

D = json.load(open('data/classes.json', encoding='utf-8'))['classes']
GEN = json.load(open('data/decks_generated.json', encoding='utf-8'))
ORDER = ['warrior', 'paladin', 'hunter', 'rogue', 'priest', 'shaman', 'mage', 'warlock', 'druid']

ROGUE = {
    'spec': 'Combat', 'author': 'DonTheCrown', 'name': 'Mobalytics WoW Forever · Rogue Leveling guide',
    'url': 'https://mobalytics.gg/wow-forever/classes/rogue-leveling-donthecrown',
    'slides': sorted(glob.glob('slides/[0-9][0-9]-*.html')),
}

# thumbnails for the hand-made rogue deck
os.makedirs('thumbs/rogue', exist_ok=True)
for f in sorted(glob.glob('png/[0-9][0-9]-*.png')):
    n = os.path.basename(f)[:2]
    out = f'thumbs/rogue/{n}.jpg'
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(f):
        Image.open(f).convert('RGB').resize((480, 270), Image.LANCZOS).save(out, quality=82, optimize=True)

decks = {}
for slug in ORDER:
    c = D[slug]
    if slug == 'rogue':
        slides, spec, src = ROGUE['slides'], ROGUE['spec'], {'author': ROGUE['author'], 'name': ROGUE['name'], 'url': ROGUE['url']}
    elif slug in GEN:
        slides, spec, src = GEN[slug]['files'], GEN[slug]['spec'], GEN[slug]['source']
    else:
        continue
    decks[slug] = {'name': c['name'], 'color': c['color'], 'spec': spec, 'source': src,
                   'trees': [t['name'] for t in c['trees']],
                   'slides': [s.replace('\\', '/') for s in slides],
                   'thumbs': [f'thumbs/{slug}/{i+1:02d}.jpg' for i in range(len(slides))]}
json.dump(decks, open('data/decks.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

# ------------------------------------------------------------------------------------------- landing
cards = ''
for slug in ORDER:
    if slug not in decks:
        continue
    d = decks[slug]
    c = D[slug]
    top = []
    for a in c['abilities']:
        if a['ranks'] and a['first'] <= 12 and len(top) < 4:
            top.append(a['ranks'][0]['img'])
    icons = ''.join(f'<img src="assets/icf/{i}.png" alt="">' for i in top)
    star = ' · full guide' if slug == 'rogue' else ''
    cards += f'''<a class="cls" href="viewer.html?class={slug}" style="--c:{d['color']}">
<div class="emb"><img src="assets/icf/e_{slug}.png" alt=""></div>
<div class="tx"><h2>{E(d['name'])}</h2><div class="spec">{E(d['spec'])} &middot; 1&rarr;30{star}</div>
<div class="trees">{' &middot; '.join(E(t) for t in d['trees'])}</div>
<div class="ics">{icons}</div></div>
<div class="go"><b>10 SLIDES</b><span>OPEN &rarr;</span></div></a>
'''

landing = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>WoW Forever Class Compendium</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Pick your class: a 10-slide WoW Forever leveling guide for every class, with real in-game tooltips.">
<link rel="stylesheet" href="assets/fonts.css">
<style>
:root{{--gold:#e3af4a;--brown:#5a3718;--cream:#f4ecd8;--mute:#a9a490;--rogue:#fff56a}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{background:#04060d}}
body{{min-height:100vh;color:var(--cream);font-family:'Inter',system-ui,sans-serif;background:linear-gradient(180deg,rgba(4,6,13,.72),rgba(4,6,13,.94) 55%),url(assets/banner.jpg) center top/cover fixed no-repeat;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1320px;margin:0 auto;padding:36px 28px 60px}}
.top{{display:flex;align-items:center;gap:26px;flex-wrap:wrap}}
.top img{{width:128px;height:128px;filter:drop-shadow(0 8px 16px rgba(0,0,0,.7))}}
.kick{{font:700 18px 'Barlow Condensed';letter-spacing:.36em;color:var(--gold);text-transform:uppercase}}
h1{{font:900 italic clamp(54px,9vw,128px)/.9 'Barlow Condensed';text-transform:uppercase;color:var(--rogue);
 text-shadow:1px 1px 0 #9a6a1f,2px 2px 0 #8a5c19,3px 3px 0 #6e4614,4px 4px 0 #5a3718,5px 5px 0 #4a2c12,6px 6px 0 #05070f,7px 7px 0 #05070f,0 0 28px rgba(255,245,106,.28);margin-top:6px}}
.lead{{max-width:880px;font:500 19px/1.55 Inter;color:#d8d2bd;margin:22px 0 36px}}
.lead b{{color:var(--rogue)}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}}
.cls{{--c:#fff;position:relative;display:grid;grid-template-columns:auto 1fr;grid-template-rows:1fr auto;gap:8px 20px;padding:22px 24px 18px;text-decoration:none;color:inherit;
 background:linear-gradient(160deg,rgba(18,24,44,.92),rgba(6,9,20,.94));border:2px solid color-mix(in srgb,var(--c) 55%,#1c2036);border-radius:6px;
 clip-path:polygon(26px 0,100% 0,100% calc(100% - 26px),calc(100% - 26px) 100%,0 100%,0 26px);transition:transform .16s,box-shadow .16s,border-color .16s}}
.cls::before{{content:'';position:absolute;inset:0;background:radial-gradient(420px 220px at 12% 0%,color-mix(in srgb,var(--c) 30%,transparent),transparent 70%);pointer-events:none}}
.cls:hover,.cls:focus-visible{{transform:translateY(-6px);border-color:var(--c);box-shadow:0 18px 44px -10px color-mix(in srgb,var(--c) 60%,transparent);outline:none}}
.emb{{grid-row:1/3;width:118px;height:118px;position:relative;display:flex;align-items:center;justify-content:center}}
.emb::before{{content:'';position:absolute;inset:0;background:var(--c);clip-path:polygon(25% 3%,75% 3%,99% 50%,75% 97%,25% 97%,1% 50%)}}
.emb::after{{content:'';position:absolute;inset:5px;background:#05070f;clip-path:polygon(25% 3%,75% 3%,99% 50%,75% 97%,25% 97%,1% 50%)}}
.emb img{{position:relative;z-index:2;width:78px;height:78px;border-radius:9px;border:3px solid var(--gold);box-shadow:0 0 0 2px #04060d,4px 4px 0 2px var(--brown)}}
.tx{{position:relative;min-width:0}}
h2{{font:900 italic 54px/.95 'Barlow Condensed';text-transform:uppercase;color:var(--c);text-shadow:2px 2px 0 var(--brown),3px 3px 0 #04060d}}
.spec{{font:800 italic 21px 'Barlow Condensed';letter-spacing:.08em;text-transform:uppercase;color:var(--cream);margin-top:4px}}
.trees{{font:600 15px 'Barlow Condensed';letter-spacing:.12em;text-transform:uppercase;color:var(--mute);margin-top:4px}}
.ics{{display:flex;gap:7px;margin-top:12px}}
.ics img{{width:34px;height:34px;border-radius:5px;border:2px solid var(--gold);box-shadow:0 0 0 1px #04060d,2px 2px 0 1px var(--brown)}}
.go{{position:relative;grid-column:2;display:flex;justify-content:space-between;align-items:center;border-top:1px solid color-mix(in srgb,var(--c) 40%,transparent);padding-top:10px}}
.go b{{font:900 italic 24px 'Barlow Condensed';letter-spacing:.06em;color:var(--cream)}}
.go span{{font:800 18px 'Barlow Condensed';letter-spacing:.2em;color:var(--c)}}
.foot{{margin-top:44px;padding-top:20px;border-top:1px solid rgba(227,175,74,.25);font:500 14px/1.6 Inter;color:var(--mute);max-width:980px}}
.foot a{{color:var(--gold)}}
@media(max-width:1060px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:700px){{.grid{{grid-template-columns:1fr}}.top img{{width:84px;height:84px}}.emb{{width:92px;height:92px}}.emb img{{width:60px;height:60px}}h2{{font-size:44px}}.lead{{font-size:17px}}}}
</style></head><body><div class="wrap">
<div class="top"><img src="assets/logo.png" alt=""><div><div class="kick">WoW Forever Beta &middot; Class compendium</div><h1>Pick your class</h1></div></div>
<p class="lead">Nine classes, <b>10 slides each</b>: the build and talent order, rotation and panic buttons, a level plan with every trainer rank, stats and gear, dungeons, races, professions and macros. Hover any icon for its in-game tooltip, straight from the WoW Forever client data.</p>
<div class="grid">
{cards}</div>
<div class="foot">Slides condensed from the Mobalytics WoW Forever leveling guides (and the Combat Rogue guide by DonTheCrown) as an editable starting point: builds, rotations and picks are the guides' opinions, not official knowledge. Tooltips: WoW Forever client data (wago.tools) and <a href="https://talents.standards.gg">talents.standards.gg</a>. Unofficial fan project; game icons and text are property of Blizzard Entertainment.
&nbsp;<a href="https://github.com/standards-gg/rogue-compendium">Source on GitHub</a></div>
</div></body></html>'''
open('index.html', 'w', encoding='utf-8').write(landing)

# ------------------------------------------------------------------------------------------- viewer
viewer = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>WoW Forever Class Compendium</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%;background:#03040a;color:#f4ecd8;font-family:system-ui,sans-serif;overflow:hidden}
  #stage{position:absolute;inset:0 0 74px 0;display:flex;align-items:center;justify-content:center;overflow:hidden}
  #frame{width:1920px;height:1080px;border:0;transform-origin:center center;flex:none;background:#05070f;box-shadow:0 20px 80px rgba(0,0,0,.8)}
  .nav{position:absolute;top:0;bottom:74px;width:12%;display:flex;align-items:center;cursor:pointer;opacity:0;transition:opacity .2s;z-index:5;font:900 64px 'Arial Black',sans-serif;color:var(--c,#fff56a);text-shadow:0 0 20px #000}
  .nav:hover{opacity:1}
  #prev{left:0;justify-content:flex-start;padding-left:24px;background:linear-gradient(90deg,rgba(0,0,0,.5),transparent)}
  #next{right:0;justify-content:flex-end;padding-right:24px;background:linear-gradient(270deg,rgba(0,0,0,.5),transparent)}
  #bar{position:absolute;left:0;right:0;bottom:0;height:74px;background:#070b17;border-top:2px solid var(--c,#5a4a1e);display:flex;align-items:center;gap:10px;padding:0 14px;z-index:6}
  #thumbs{display:flex;gap:8px;flex:1;overflow-x:auto;scrollbar-width:none}
  .t{flex:none;width:92px;height:52px;border:2px solid #3a3320;border-radius:4px;background-size:cover;background-position:center;cursor:pointer;opacity:.55;transition:.15s;position:relative}
  .t:hover{opacity:.9}
  .t.on{border-color:var(--c,#fff56a);opacity:1;box-shadow:0 0 12px var(--c,#fff56a)}
  .t b{position:absolute;left:3px;top:1px;font:800 12px sans-serif;color:#fff;text-shadow:0 0 3px #000}
  button,a.btn{background:var(--c,#fff56a);color:#0a0c14;border:0;font:800 14px sans-serif;letter-spacing:.08em;padding:10px 14px;border-radius:5px;cursor:pointer;text-transform:uppercase;text-decoration:none;white-space:nowrap}
  button:hover,a.btn:hover{background:#fff}
  #ct{font:800 15px sans-serif;letter-spacing:.1em;color:#a9a490;min-width:64px;text-align:center}
  select{background:#0d1222;color:#f4ecd8;border:2px solid var(--c,#5a4a1e);border-radius:5px;font:700 14px sans-serif;padding:8px 10px;letter-spacing:.06em}
  @media(max-width:760px){#thumbs{display:none}#bar{gap:6px}a.btn,button{padding:10px 10px;font-size:12px}}
</style></head><body>
<div id="stage"><iframe id="frame" title="slide"></iframe></div>
<div class="nav" id="prev">&#10094;</div><div class="nav" id="next">&#10095;</div>
<div id="bar"><a class="btn" href="index.html">&#9664; Classes</a><select id="sel" aria-label="Class"></select><button id="b1">&#9664; Prev</button><span id="ct"></span><button id="b2">Next &#9654;</button><div id="thumbs"></div><button id="fs">Fullscreen</button></div>
<script>
const f=document.getElementById('frame'),st=document.getElementById('stage'),th=document.getElementById('thumbs'),ct=document.getElementById('ct'),sel=document.getElementById('sel');
let D={},cls='rogue',S=[],T=[],i=0;
function fit(){const s=Math.min(st.clientWidth/1920,st.clientHeight/1080);f.style.transform=`scale(${s})`;f.style.margin=`${-(1080*(1-s))/2}px ${-(1920*(1-s))/2}px`}
function load(slug,k){
  cls=D[slug]?slug:Object.keys(D)[0]; const d=D[cls]; S=d.slides; T=d.thumbs;
  document.documentElement.style.setProperty('--c',d.color); document.title=d.name+' · WoW Forever Class Compendium';
  sel.value=cls; th.innerHTML='';
  S.forEach((n,j)=>{const e=document.createElement('div');e.className='t';e.style.backgroundImage=`url(${T[j]})`;e.innerHTML=`<b>${j+1}</b>`;e.onclick=()=>go(j);th.appendChild(e)});
  go(k||0);
}
function go(k){
  i=Math.max(0,Math.min(S.length-1,k)); f.src=S[i]+'?v='+Date.now(); ct.textContent=(i+1)+' / '+S.length;
  history.replaceState(null,'','?class='+cls+'#'+(i+1));
  [...th.children].forEach((c,j)=>c.classList.toggle('on',j===i)); th.children[i].scrollIntoView({block:'nearest',inline:'center'});
}
document.getElementById('prev').onclick=document.getElementById('b1').onclick=()=>go(i-1);
document.getElementById('next').onclick=document.getElementById('b2').onclick=()=>go(i+1);
document.getElementById('fs').onclick=()=>document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();
sel.onchange=()=>load(sel.value,0);
addEventListener('keydown',e=>{if(e.target===sel)return;
 if(['ArrowRight','PageDown',' ','Enter'].includes(e.key)){e.preventDefault();go(i+1)}
 else if(['ArrowLeft','PageUp','Backspace'].includes(e.key)){e.preventDefault();go(i-1)}
 else if(e.key==='Home')go(0);else if(e.key==='End')go(S.length-1);else if(e.key==='f'||e.key==='F')document.getElementById('fs').click()});
let x0=null;addEventListener('touchstart',e=>x0=e.touches[0].clientX);addEventListener('touchend',e=>{if(x0==null)return;const d=e.changedTouches[0].clientX-x0;if(Math.abs(d)>50)go(i+(d<0?1:-1));x0=null});
addEventListener('resize',fit);fit();
fetch('data/decks.json').then(r=>r.json()).then(j=>{D=j;
  Object.keys(D).forEach(k=>{const o=document.createElement('option');o.value=k;o.textContent=D[k].name+' · '+D[k].spec;sel.appendChild(o)});
  const q=new URLSearchParams(location.search).get('class')||'rogue'; const h=parseInt(location.hash.slice(1))||1; load(q,h-1);});
</script></body></html>
'''
open('viewer.html', 'w', encoding='utf-8').write(viewer)
print('landing + viewer written;', len(decks), 'decks')
