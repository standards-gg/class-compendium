import subprocess,glob,os,sys,pathlib
EDGE=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
os.makedirs('png',exist_ok=True)
only=sys.argv[1:]
for f in sorted(glob.glob('slides/*.html')):
    n=os.path.basename(f)[:-5]
    if only and not any(n.startswith(o) for o in only): continue
    out=os.path.abspath(f'png/{n}.png')
    subprocess.run([EDGE,'--headless=new','--disable-gpu','--hide-scrollbars','--force-device-scale-factor=1.3333',
      '--window-size=1920,1080','--virtual-time-budget=4000',f'--screenshot={out}',pathlib.Path(os.path.abspath(f)).as_uri()],
      stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=90)
    print(n,'ok')
