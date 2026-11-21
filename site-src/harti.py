"""Hărțile porțiunii „Monitorizare digitală”. Rulare din rădăcina proiectului:  python3 site-src/harti.py
Necesită: pip install shapely pillow lxml
1) site/assets/img/monitorizare/harta-echipamente.jpg — amplasamente candidate peste harta topo din GIS/zona-de-lucru
   (georeferință: PDF-ul _geo, EPSG:3857, lon 22.393–22.51, lat 44.8475–44.936). Pozițiile zonelor sunt în coordonate
   de imagine la scara 1000 px (P(x,y)); se mută editând listele de mai jos.
2) site/assets/date/harta/straturi.js — straturile hărții de consultare (contur, zonare PMI 2025, trasee, pante, incendiu 2026).
"""
import os
ROOT='.'; G=os.path.join(ROOT,'GIS')
import math, json
W,H=2727,2911
LON0,LON1,LAT0,LAT1=22.393,22.51,44.8475,44.936
def my(lat): return math.log(math.tan(math.pi/4+math.radians(lat)/2))
def px(lon,lat):
    x=(lon-LON0)/(LON1-LON0)*W
    y=(my(LAT1)-my(lat))/(my(LAT1)-my(LAT0))*H
    return x,y

import json, math
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import shape
from shapely.ops import unary_union
S=2.727  # 1000-scale -> full res
base=Image.open(G+'/zona-de-lucru/Digital-Ranger_zona_harta-topo.jpg').convert('RGBA')
W,H=base.size
ov=Image.new('RGBA',base.size,(0,0,0,0)); d=ImageDraw.Draw(ov)
F='/usr/share/fonts/truetype/dejavu/'
f_b=lambda s: ImageFont.truetype(F+'DejaVuSans-Bold.ttf',s)
f_r=lambda s: ImageFont.truetype(F+'DejaVuSans.ttf',s)
def P(x,y): return (x*S,y*S)
def ring(coords): return [px(*c) for c in coords]
def polys(g):
    for p in getattr(g,'geoms',[g]): yield p

# 1. urma incendiului 2026 (context)
p=json.load(open(G+'/incendiu-2026/Digital-Ranger_incendiu-2026_progresie.geojson'))
fire=unary_union([shape(f['geometry']) for f in p['features']])
hatch=Image.new('RGBA',base.size,(0,0,0,0)); hd=ImageDraw.Draw(hatch)
for g in polys(fire):
    hd.polygon(ring(g.exterior.coords),fill=(205,35,25,95))
    for i in g.interiors: hd.polygon(ring(i.coords),fill=(0,0,0,0))
ov=Image.alpha_composite(ov,hatch); d=ImageDraw.Draw(ov)
for g in polys(fire): d.line(ring(g.exterior.coords),fill=(170,25,15,230),width=3)

# 2. drumuri vechi (unități DD din parcelar)
pr=json.load(open(G+'/zona-de-lucru/Digital-Ranger_zona_parcele-silvice.geojson'))
for f in pr['features']:
    if f['properties']['ua'].endswith('DD'):
        for g in polys(shape(f['geometry'])):
            d.line(ring(g.exterior.coords),fill=(80,45,10,255),width=8,joint='curve')

COL={'H':(30,70,35),'C':(31,95,170),'N':(110,50,140),'A':(110,50,140),'G':(200,110,0),'M':(0,125,125),'R':(20,120,200)}
def dashed_circle(cx,cy,r,col,fill_a=45,w=5,dash=10):
    x,y=P(cx,cy); rr=r*S
    d.ellipse([x-rr,y-rr,x+rr,y+rr],fill=col+(fill_a,))
    n=int(2*math.pi*rr/(dash*2.2))
    for i in range(n):
        a0=2*math.pi*i/n; a1=a0+math.pi/n
        d.arc([x-rr,y-rr,x+rr,y+rr],math.degrees(a0),math.degrees(a1),fill=col+(255,),width=w)
def dashed_ellipse(cx,cy,rx,ry,col,fill_a=40,w=5):
    x,y=P(cx,cy); a,b=rx*S,ry*S
    d.ellipse([x-a,y-b,x+a,y+b],fill=col+(fill_a,))
    for i in range(48):
        a0=360*i/48; d.arc([x-a,y-b,x+a,y+b],a0,a0+3.75,fill=col+(255,),width=w)
def badge(cx,cy,txt,col,shape_='circle',r=19):
    x,y=P(cx,cy); rr=r*S/2.0*1.0
    rr=r*1.6
    if shape_=='square': d.rectangle([x-rr,y-rr,x+rr,y+rr],fill=col+(255,),outline=(255,255,255,255),width=4)
    elif shape_=='tri': d.polygon([(x,y-rr*1.25),(x-rr*1.15,y+rr*0.85),(x+rr*1.15,y+rr*0.85)],fill=col+(255,),outline=(255,255,255,255))
    else: d.ellipse([x-rr,y-rr,x+rr,y+rr],fill=col+(255,),outline=(255,255,255,255),width=4)
    fnt=f_b(int(rr*0.95 if len(txt)<3 else rr*0.8))
    d.text((x,y+(rr*0.18 if shape_=='tri' else 0)),txt,font=fnt,fill='white',anchor='mm')
def label(cx,cy,txt,anchor='lm',size=30):
    x,y=P(cx,cy); fnt=f_b(size)
    bb=d.textbbox((x,y),txt,font=fnt,anchor=anchor)
    d.rounded_rectangle([bb[0]-8,bb[1]-5,bb[2]+8,bb[3]+5],radius=6,fill=(255,255,255,225))
    d.text((x,y),txt,font=fnt,fill=(25,40,25),anchor=anchor)

# 3. zone de căutare (desenate întâi, sub simboluri)
dashed_circle(735,390,62,COL['G'],fill_a=30)            # releu LoRa
dashed_circle(475,700,48,COL['M'],fill_a=45)            # stația meteo
for (x,y) in [(455,575),(610,820),(725,565)]: dashed_circle(x,y,40,COL['R'],fill_a=55)  # rezervoare
for (x,y,rx,ry) in [(555,245,85,42),(395,875,95,38),(590,455,72,40)]: dashed_ellipse(x,y,rx,ry,COL['A'])
# camere la intrări (zone mici)
CAM=[('C1',235,625),('C2',317,446),('C3',165,833),('C4',478,162)]
for _,x,y in CAM: dashed_circle(x,y,30,COL['C'],fill_a=50,w=4)

# 4. simboluri
badge(178,712,'H',COL['H'],'square',r=22)
for t,x,y in CAM: badge(x,y,t,COL['C'])
for t,(x,y) in zip(['N1','N2','N3'],[(301,612),(212,860),(540,190)]): badge(x,y,t,COL['N'],'tri')
for t,(x,y) in zip(['A1','A2','A3'],[(600,245),(430,875),(615,455)]): badge(x,y,t,COL['A'])
badge(735,405,'G',COL['G']); badge(475,700,'M',COL['M'])
for t,(x,y) in zip(['R1','R2','R3'],[(455,575),(610,820),(725,565)]): badge(x,y,t,COL['R'])

# 5. etichete scurte pe hartă
label(178,742,'Hub-ul de Sud',anchor='mt',size=28)
label(178,770,'sediul parcului (schematic)',anchor='mt',size=22)
label(290,446,'acces din DN67D',anchor='rm',size=24)
label(190,805,'Cheile Feregari',anchor='rm',size=24) if False else None

ov_img=Image.alpha_composite(base,ov); d=ImageDraw.Draw(ov_img)

# 6. legendă (acoperă legenda veche)
LX,LY,LW=24,24,1010
items=[('H','square',COL['H'],'Hub-ul de Sud: baza dronei, datele, gateway-ul LoRa principal'),
       ('C','circle',COL['C'],'Camere la intrări (3–4): numără treceri; fără recunoaștere facială, fără ANPR'),
       ('N','tri',COL['N'],'Noduri acustice în timp real (2–3), la accesele folosite'),
       ('A','circle',COL['A'],'Zone pentru loggere acustice pasive (6–10), pe versanți'),
       ('G','circle',COL['G'],'Releu LoRa: zonă de căutare, aleasă după testul radio'),
       ('M','circle',COL['M'],'Stația meteo: zonă de căutare la altitudine'),
       ('R','circle',COL['R'],'Rezervoare de apă (3–5), pe culmi și șei (secțiunea A)')]
lh=60; top=LY+150; boxh=150+len(items)*lh+130
d.rounded_rectangle([LX,LY,LX+LW,LY+boxh],radius=14,fill=(255,255,255,245),outline=(60,80,60,255),width=3)
d.text((LX+28,LY+26),'Digital Ranger — monitorizare digitală',font=f_b(40),fill=(25,60,30))
d.text((LX+28,LY+80),'Amplasamente candidate, pilot 2027–2029 · DE VALIDAT ÎN TEREN',font=f_b(25),fill=(150,60,20))
d.text((LX+28,LY+114),'Pozițiile sunt orientative, nu puncte de montaj.',font=f_r(24),fill=(70,70,70))
d2=ImageDraw.Draw(ov_img)
for i,(t,sh,col,txt) in enumerate(items):
    y=top+i*lh+20; x=LX+52; rr=20
    if sh=='square': d2.rectangle([x-rr,y-rr,x+rr,y+rr],fill=col)
    elif sh=='tri': d2.polygon([(x,y-rr*1.2),(x-rr*1.1,y+rr*0.8),(x+rr*1.1,y+rr*0.8)],fill=col)
    else: d2.ellipse([x-rr,y-rr,x+rr,y+rr],fill=col)
    d2.text((x,y+(3 if sh=='tri' else 0)),t,font=f_b(22),fill='white',anchor='mm')
    d2.text((x+40,y),txt,font=f_r(26),fill=(30,30,30),anchor='lm')
y=top+len(items)*lh+22
d2.line([LX+30,y,LX+74,y],fill=(80,45,10),width=8); d2.text((LX+92,y),'drumuri vechi (unități de drum din parcelarul silvic)',font=f_r(26),fill=(30,30,30),anchor='lm')
y+=48
d2.rectangle([LX+30,y-14,LX+74,y+14],fill=(226,150,120),outline=(170,25,15),width=3); d2.text((LX+92,y),'urma incendiului din 2026 (Sentinel-2, prelucrare proprie)',font=f_r(26),fill=(30,30,30),anchor='lm')
out=ov_img.convert('RGB')
os.makedirs(os.path.join(ROOT,'site/assets/img/monitorizare'),exist_ok=True)
w=1600; out.resize((w,int(w*H/W)),Image.LANCZOS).save(os.path.join(ROOT,'site/assets/img/monitorizare/harta-echipamente.jpg'),quality=82,optimize=True,progressive=True)

# ---------- 2) straturile hărții de consultare ----------
from lxml import etree
from shapely.geometry import mapping, box, Polygon, MultiPolygon, MultiLineString
def rnd(geom, nd=5):
    g=json.loads(json.dumps(mapping(geom)))
    def r(c):
        if isinstance(c[0],(int,float)): return [round(c[0],nd),round(c[1],nd)]
        return [r(x) for x in c]
    g['coordinates']=r(g['coordinates']); return g
out={}
z=json.load(open(G+'/zona-de-lucru/Digital-Ranger_zona.geojson'))
zone=[shape(f['geometry']) for f in z['features'] if f['geometry']['type']=='Polygon'][0]
out['contur']={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'nume':'Zona Domogled (≈ 3.305 ha)'},'geometry':rnd(zone.simplify(0.00003))}]}
out['toponime']={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'nume':f['properties']['name']},'geometry':f['geometry']} for f in z['features'] if f['geometry']['type']=='Point']}
d=json.load(open(G+'/PNDVC_zonare_WGS84.geojson'))
CAT={'zonă de protecţie integrală':'Protecție integrală','zonă de protecţie strictă':'Protecție strictă','zonă de conservare durabilă-parcele limitrofe':'Conservare durabilă – parcele limitrofe','zonă de conservare durabilă':'Conservare durabilă','zonă de dezvoltare durabilă':'Dezvoltare durabilă'}
B=box(22.385,44.835,22.53,44.945); groups={}; allp=[]
for f in d['features']:
    g=shape(f['geometry']); g=g if g.is_valid else g.buffer(0); allp.append(g)
    if g.intersects(B): groups.setdefault(CAT[f['properties']['zonare']],[]).append(g.intersection(B))
out['zonare']={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'zonare':k},'geometry':rnd(unary_union([x.buffer(0.00002) for x in v]).buffer(-0.00002).simplify(0.00006))} for k,v in groups.items()]}
park=unary_union([x.buffer(0.0002) for x in allp]).buffer(-0.0002).simplify(0.0006)
ps=[Polygon(p.exterior) for p in getattr(park,'geoms',[park]) if p.area>1e-6]
out['parc']={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'nume':'Limita parcului'},'geometry':rnd(MultiPolygon(ps) if len(ps)>1 else ps[0],4)}]}
ns={'k':'http://www.opengis.net/kml/2.2'}
t=etree.parse(ROOT+'/Digital-Ranger_trasee-turistice_zona-de-lucru.kml'); tf=[]
for pm in t.iterfind('.//k:Placemark',ns):
    name=pm.findtext('k:name',namespaces=ns)
    lines=[[tuple(map(float,c.split(',')[:2])) for c in ls.text.split()] for ls in pm.iterfind('.//k:LineString/k:coordinates',ns)]
    if 'limită' in name or not lines: continue
    tf.append({'type':'Feature','properties':{'nume':name,'oficial':name.startswith('Nr.')},'geometry':rnd(MultiLineString(lines).simplify(0.00003))})
out['trasee']={'type':'FeatureCollection','features':tf}
t=etree.parse(ROOT+'/Digital-Ranger_zone-inaccesibile_panta-peste-45.kml')
pp=[Polygon([tuple(map(float,c.split(',')[:2])) for c in poly.find('.//k:outerBoundaryIs//k:coordinates',ns).text.split()]) for poly in t.iterfind('.//k:Polygon',ns)]
out['pante']={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'nume':'Pante peste 45° (≈ 223 ha)'},'geometry':rnd(unary_union(pp).simplify(0.00004))}]}
out['incendiu']={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'data':f['properties']['vizibil_prima_data'],'ha':f['properties']['ha']},'geometry':rnd(shape(f['geometry']).simplify(0.00005,preserve_topology=True))} for f in p['features']]}
dst=os.path.join(ROOT,'site/assets/date/harta'); os.makedirs(dst,exist_ok=True)
open(os.path.join(dst,'straturi.js'),'w',encoding='utf8').write('/* Straturile hărții de consultare Digital Ranger. Generat de site-src/harti.py din GIS/ și KML-urile proiectului. */\nwindow.DR_STRATURI='+json.dumps(out,ensure_ascii=False,separators=(',',':'))+';\n')
print('harta-echipamente.jpg și straturi.js generate')
