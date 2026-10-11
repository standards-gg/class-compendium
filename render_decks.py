"""Render slides/<class>/*.html to PNG with Edge (headless) and write 480x270 JPEG thumbnails to thumbs/<class>/.

  python render_decks.py warrior mage     (no args = all classes except rogue)
Full-size renders go to $RENDER_DIR (default: <temp>/rc-render), not into the repo.
"""
import glob, os, pathlib, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

EDGE = os.environ.get('EDGE', r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
OUT = os.environ.get('RENDER_DIR', os.path.join(os.environ.get('TEMP', '/tmp'), 'rc-render'))
slugs = sys.argv[1:] or sorted(d for d in os.listdir('slides') if os.path.isdir(f'slides/{d}'))
jobs = []
for s in slugs:
    os.makedirs(f'{OUT}/{s}', exist_ok=True)
    os.makedirs(f'thumbs/{s}', exist_ok=True)
    for f in sorted(glob.glob(f'slides/{s}/*.html')):
        jobs.append((s, f))

def run(job):
    s, f = job
    n = os.path.basename(f)[:2]
    png = os.path.abspath(f'{OUT}/{s}/{n}.png')
    prof = os.path.abspath(f'{OUT}/_prof_{os.getpid()}_{n}_{s}')
    subprocess.run([EDGE, '--headless=new', '--disable-gpu', f'--user-data-dir={prof}', '--hide-scrollbars', '--force-device-scale-factor=1',
                    '--window-size=1920,1080', '--virtual-time-budget=4000', f'--screenshot={png}', pathlib.Path(os.path.abspath(f)).as_uri()],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    try:
        Image.open(png).convert('RGB').resize((480, 270), Image.LANCZOS).save(f'thumbs/{s}/{n}.jpg', quality=82, optimize=True)
        return s, n, True
    except Exception as e:
        return s, n, False

with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(run, jobs))
bad = [r for r in res if not r[2]]
print('rendered', len(res) - len(bad), 'failed', bad)
