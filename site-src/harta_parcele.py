"""Harta parcelarului silvic din zona Domogled, colorată după zonarea PMI 2025.
Rulare din rădăcina proiectului:  python3 site-src/harta_parcele.py   (necesită: pip install shapely pillow)
Intrări: GIS/zona-de-lucru/Digital-Ranger_zona_harta-topo.jpg (fond, EPSG:3857, lon 22.393–22.51, lat 44.8475–44.936),
         GIS/zona-de-lucru/Digital-Ranger_zona_parcele-silvice.geojson (u.a., amenajament 2022),
         GIS/PNDVC_zonare_WGS84.geojson (baza GIS de zonare 10.11.2023 = PMI 2025), GIS/zona-de-lucru/Digital-Ranger_zona.geojson.
Ieșiri:  GIS/zona-de-lucru/Digital-Ranger_zona_parcele-silvice_PMI2025.jpg (rezoluție completă)
         site/assets/img/zona/parcele-silvice.jpg (2000 px, pentru site)
Harta veche (zonarea planului anterior) rămâne neatinsă: GIS/zona-de-lucru/Digital-Ranger_zona_parcele-silvice.jpg
"""
import os, json, math
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import shape, box
from shapely.ops import unary_union
ROOT='.'; G=os.path.join(ROOT,'GIS')
LON0,LON1,LAT0,LAT1=22.393,22.51,44.8475,44.936
base=Image.open(G+'/zona-de-lucru/Digital-Ranger_zona_harta-topo.jpg').convert('RGBA'); W,H=base.size
def my(lat): return math.log(math.tan(math.pi/4+math.radians(lat)/2))
def px(lon,lat): return ((lon-LON0)/(LON1-LON0)*W,(my(LAT1)-my(lat))/(my(LAT1)-my(LAT0))*H)
def ring(c): return [px(*p[:2]) for p in c]
def polys(g): return [p for p in getattr(g,'geoms',[g]) if p.geom_type=='Polygon']
F='/usr/share/fonts/truetype/dejavu/'
fb=lambda s: ImageFont.truetype(F+'DejaVuSans-Bold.ttf',s); fr=lambda s: ImageFont.truetype(F+'DejaVuSans.ttf',s)
# culorile hărții de consultare (harta-interactiva.html)
ZC={'Protecție strictă':'#e08a6a','Protecție integrală':'#9c7bb0','Conservare durabilă':'#f2e27a',
    'Conservare durabilă – parcele limitrofe':'#f0b860','Dezvoltare durabilă':'#7aa6d8'}
CAT={'zonă de protecţie integrală':'Protecție integrală','zonă de protecţie strictă':'Protecție strictă',
     'zonă de conservare durabilă-parcele limitrofe':'Conservare durabilă – parcele limitrofe',
     'zonă de conservare durabilă':'Conservare durabilă','zonă de dezvoltare durabilă':'Dezvoltare durabilă'}
hexrgb=lambda h,a: tuple(int(h[i:i+2],16) for i in (1,3,5))+(a,)
z=json.load(open(G+'/zona-de-lucru/Digital-Ranger_zona.geojson'))
zone=[shape(f['geometry']) for f in z['features'] if f['geometry']['type']=='Polygon'][0]
# 1. zonarea PMI 2025, decupată pe zonă
groups={}
for f in json.load(open(G+'/PNDVC_zonare_WGS84.geojson'))['features']:
    g=shape(f['geometry'])
    if not g.intersects(zone.envelope): continue
    g=g if g.is_valid else g.buffer(0)
    if g.intersects(zone): groups.setdefault(CAT[f['properties']['zonare']],[]).append(g.intersection(zone))
fill=Image.new('RGBA',base.size,(0,0,0,0)); fd=ImageDraw.Draw(fill)
fd.polygon(ring(zone.exterior.coords),fill=(255,255,255,150))   # fâșia din afara parcului: albită
for k,v in groups.items():
    for p in polys(unary_union(v)):
        fd.polygon(ring(p.exterior.coords),fill=hexrgb(ZC[k],200))
        for i in p.interiors: fd.polygon(ring(i.coords),fill=(255,255,255,150))
img=Image.alpha_composite(base,fill); d=ImageDraw.Draw(img)
# 2. parcelarul: u.a. subțire, parcelele groase, etichete u.a.
pr=json.load(open(G+'/zona-de-lucru/Digital-Ranger_zona_parcele-silvice.geojson'))['features']
for f in pr:
    for p in polys(shape(f['geometry'])): d.line(ring(p.exterior.coords),fill=(60,60,60,200),width=2)
byp={}
for f in pr: byp.setdefault(f['properties']['parcela'],[]).append(shape(f['geometry']).buffer(0))
for k,v in byp.items():
    for p in polys(unary_union([x.buffer(0.00001) for x in v]).buffer(-0.00001)): d.line(ring(p.exterior.coords),fill=(20,20,20,255),width=5)
for f in pr:
    g=shape(f['geometry'])
    if g.area<2e-6: continue
    x,y=px(*g.representative_point().coords[0])
    d.text((x,y),f['properties']['ua'],font=fb(19),fill=(25,25,25),anchor='mm',stroke_width=3,stroke_fill=(255,255,255))
d.line(ring(zone.exterior.coords)+[ring(zone.exterior.coords)[0]],fill=(200,20,30,255),width=7)
for f in z['features']:   # toponimele zonei, deasupra culorilor
    if f['geometry']['type']!='Point': continue
    x,y=px(*f['geometry']['coordinates'][:2]); t=f['properties']['name']
    d.ellipse([x-8,y-8,x+8,y+8],fill=(20,20,20),outline='white',width=3)
    bb=d.textbbox((x+16,y),t,font=fb(26),anchor='lm'); d.rounded_rectangle([bb[0]-6,bb[1]-4,bb[2]+6,bb[3]+4],radius=6,fill=(255,255,255,235))
    d.text((x+16,y),t,font=fb(26),fill=(20,20,20),anchor='lm')
# 3. legenda (acoperă legenda fondului)
ha={k:sum(x.area for x in v) for k,v in groups.items()}
LX,LY,LW=24,24,1180
items=[k for k in ['Protecție strictă','Protecție integrală','Conservare durabilă','Conservare durabilă – parcele limitrofe','Dezvoltare durabilă'] if k in groups]
lh=52; boxh=230+len(items)*lh+150
d.rounded_rectangle([LX,LY,LX+LW,LY+boxh],radius=14,fill=(255,255,255,245),outline=(60,80,60,255),width=3)
d.text((LX+28,LY+24),'Digital Ranger — parcelarul silvic al zonei Domogled',font=fb(38),fill=(25,60,30))
d.text((LX+28,LY+76),'colorat după zonarea Planului de management integrat 2025',font=fb(27),fill=(25,60,30))
d.text((LX+28,LY+116),'Zonare: baza GIS PNDVC, versiunea 10.11.2023. PMI 2025 e în curs de aprobare prin ordin de ministru;',font=fr(23),fill=(150,60,20))
d.text((LX+28,LY+146),'până atunci se aplică zonarea planului anterior.',font=fr(23),fill=(150,60,20))
d.text((LX+28,LY+180),'Parcelar: O.S. Băile Herculane, U.P. VI, amenajament 2022 · 279 u.a. în 100 de parcele',font=fr(23),fill=(70,70,70))
top=LY+232
for i,k in enumerate(items):
    y=top+i*lh+18
    d.rectangle([LX+30,y-16,LX+80,y+16],fill=hexrgb(ZC[k],255),outline=(60,60,60),width=2)
    d.text((LX+100,y),k,font=fr(27),fill=(30,30,30),anchor='lm')
y=top+len(items)*lh+18
d.rectangle([LX+30,y-16,LX+80,y+16],fill=(240,240,236),outline=(60,60,60),width=2); d.text((LX+100,y),'în afara parcului (fâșia de lângă DN67D)',font=fr(27),fill=(30,30,30),anchor='lm'); y+=lh
d.line([LX+30,y,LX+80,y],fill=(20,20,20),width=5); d.text((LX+100,y),'limită de parcelă   ·   linie subțire: limită de u.a.; eticheta = u.a.',font=fr(27),fill=(30,30,30),anchor='lm'); y+=lh
d.line([LX+30,y,LX+80,y],fill=(200,20,30),width=7); d.text((LX+100,y),'limita zonei Domogled (≈ 3.305 ha)',font=fr(27),fill=(30,30,30),anchor='lm')
out=img.convert('RGB')
out.save(G+'/zona-de-lucru/Digital-Ranger_zona_parcele-silvice_PMI2025.jpg',quality=88,optimize=True)
w=2000; out.resize((w,int(w*H/W)),Image.LANCZOS).save(ROOT+'/site/assets/img/zona/parcele-silvice.jpg',quality=82,optimize=True,progressive=True)
print('suprafețe din geometrie (grade², relativ):',{k:round(v/sum(ha.values())*100,1) for k,v in ha.items()})
print('harta parcelarului PMI 2025 generată',out.size)
