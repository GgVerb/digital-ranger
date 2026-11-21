"""Optimizează imaginile din GIS/ pentru site. Harta parcelarului (zonarea PMI 2025) NU se face aici: python3 site-src/harta_parcele.py. Rulare: python3 site-src/media.py (din rădăcina proiectului)."""
import os, subprocess
from PIL import Image
G="GIS"; O="site/assets"
JPG=[("zona-de-lucru/Digital-Ranger_zona_harta-topo.jpg","img/zona/harta-topo.jpg",1600),
     ("zona-de-lucru/Digital-Ranger_zona_satelit.jpg","img/zona/harta-satelit.jpg",1600),
          ("zona-de-lucru/Digital-Ranger_zona_3D_dinspre-SE.jpg","img/zona/3d-dinspre-se.jpg",1600),
     ("zona-de-lucru/Digital-Ranger_zona_3D_dinspre-SV.jpg","img/zona/3d-dinspre-sv.jpg",1600),
     ("incendiu-2026/Digital-Ranger_incendiu-2026_harta-progresie.jpg","img/incendiu/harta-progresie.jpg",1600),
     ("incendiu-2026/Digital-Ranger_incendiu-2026_grafic.png","img/incendiu/grafic-detectii.png",1400)]
for src,dst,w in JPG:
    im=Image.open(os.path.join(G,src))
    if im.width>w: im=im.resize((w,round(im.height*w/im.width)),Image.LANCZOS)
    p=os.path.join(O,dst)
    if dst.endswith(".png"):
        im.convert("RGBA").save(p,optimize=True)
    else:
        im.convert("RGB").save(p,quality=74,optimize=True,progressive=True)
    print(dst, os.path.getsize(p)//1024,"KB")
for src,dst,fps in [("incendiu-2026/Digital-Ranger_incendiu-2026_toate-imaginile-Sentinel2.gif","media/sentinel2-toate",1/0.9),
                    ("incendiu-2026/Digital-Ranger_incendiu-2026_momente-cheie.gif","media/momente-cheie",1/1.8)]:
    s=os.path.join(G,src); d=os.path.join(O,dst)
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",s,"-movflags","+faststart","-pix_fmt","yuv420p",
                    "-vf","scale=trunc(iw/2)*2:trunc(ih/2)*2","-c:v","libx264","-preset","veryfast","-crf","28","-r","10",d+".mp4"],check=True)
    im=Image.open(s); im.seek(im.n_frames-1); im.convert("RGB").save(d+"-poster.jpg",quality=80,optimize=True)
    print(dst, os.path.getsize(d+".mp4")//1024,"KB mp4")
