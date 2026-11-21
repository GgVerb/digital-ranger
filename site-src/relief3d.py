"""Datele vederii 3D rotibile (pagina Zona Domogled). Rulare din rădăcina proiectului: python3 site-src/relief3d.py
Necesită: pip install numpy shapely pyproj pillow; acces la rețea pentru dalele de fond (Esri World Imagery, OpenTopoMap).
Relieful vine din modelul de imprimare GIS/zona-de-lucru/Digital-Ranger_zona_relief-3D-print_test-mic_scara-1-45000.stl
(grilă ≈ 27 m, exagerare verticală 1,5 inclusă, construit în EPSG:3857, centrat pe zonă cu ≈ 400 m margine).
Ieșiri: site/assets/date/relief/relief.json, site/assets/img/relief/textura-satelit.jpg, textura-topo.jpg
"""
import json, math, struct, base64, io, os, time, urllib.request
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import shape
from pyproj import Transformer
G='GIS/zona-de-lucru'; O='site/assets'
STL=G+'/Digital-Ranger_zona_relief-3D-print_test-mic_scara-1-45000.stl'; SCALE=45000; VEX=1.5; BASE_MM=3.0
z=json.load(open(G+'/Digital-Ranger_zona.geojson'))
zone=[shape(f['geometry']) for f in z['features'] if f['geometry']['type']=='Polygon'][0]
to3857=Transformer.from_crs(4326,3857,always_xy=True); to4326=Transformer.from_crs(3857,4326,always_xy=True)
zx,zy=zip(*[to3857.transform(*c) for c in zone.exterior.coords])
# 1. grila de relief din fața superioară a STL
b=open(STL,'rb').read(); n=struct.unpack('<I',b[80:84])[0]
a=np.frombuffer(b[84:84+50*n],dtype=np.dtype([('n','<3f4'),('v','<9f4'),('a','<u2')]))
top=a['v'].reshape(-1,3,3)[a['n'][:,2]>0.3].reshape(-1,3)
sx,sy=top[:,0].max(),top[:,1].max()
k=1/math.cos(math.radians((min(zone.bounds[1::2])+max(zone.bounds[1::2]))/2))
Wm,Hm=sx*SCALE/1000*k,sy*SCALE/1000*k          # dimensiunea în unități 3857
cx,cy=(min(zx)+max(zx))/2,(min(zy)+max(zy))/2
X0,X1,Y0,Y1=cx-Wm/2,cx+Wm/2,cy-Hm/2,cy+Hm/2
NX=len(np.unique(np.round(top[:,0],2))); NY=len(np.unique(np.round(top[:,1],2)))
ix=np.round(top[:,0]/sx*(NX-1)).astype(int); iy=np.round(top[:,1]/sy*(NY-1)).astype(int)
hm=np.zeros((NY,NX),np.float32); hm[iy,ix]=np.maximum(hm[iy,ix],top[:,2])
hm=np.flipud(hm)                                   # rândul 0 = nord
elev=(hm-BASE_MM)/VEX*SCALE/1000                   # metri relativi, fără exagerare
q=np.clip(np.round(elev/elev.max()*65535),0,65535).astype('<u2')
def zone_lonlat(): return [list(map(lambda v: round(v,6),c[:2])) for c in zone.exterior.coords]
rep=[]
for f in z['features']:
    if f['geometry']['type']!='Point': continue
    x,y=to3857.transform(*f['geometry']['coordinates'][:2]); u=(x-X0)/(X1-X0); v=(Y1-y)/(Y1-Y0)
    rep.append([f['properties']['name'],round(float((u-0.5)*float(sx)*SCALE/1000),1),round(float((v-0.5)*float(sy)*SCALE/1000),1),round(float(elev[int(v*(NY-1)),int(u*(NX-1))]),1)])
meta={'repere':rep,'nx':NX,'ny':NY,'latime_m':round(float(sx)*SCALE/1000),'inaltime_m':round(float(sy)*SCALE/1000),'dif_nivel_m':round(float(elev.max())),
      'bbox_3857':[float(v) for v in (X0,Y0,X1,Y1)],'h':base64.b64encode(q.tobytes()).decode()}
json.dump(meta,open(O+'/date/relief/relief.json','w'),separators=(',',':'))
# control: înălțimi relative în câteva repere (Domogledul Mare trebuie să fie sus, valea Cernei jos)
def at(lon,lat):
    x,y=to3857.transform(lon,lat); c=int((x-X0)/(X1-X0)*(NX-1)); r=int((Y1-y)/(Y1-Y0)*(NY-1)); return round(float(elev[r,c]))
for f in z['features']:
    if f['geometry']['type']=='Point': print('reper',f['properties']['name'],at(*f['geometry']['coordinates'][:2]),'m relativ')
# 2. texturi din dale, decupate exact pe cadrul modelului
def lon(x): return x/6378137*180/math.pi
def tile_xy(x,y,zm):
    R=2*math.pi*6378137; return (x+R/2)/R*2**zm,(R/2-y)/R*2**zm
def mosaic(url,zm,ext):
    tx0,ty0=tile_xy(X0,Y1,zm); tx1,ty1=tile_xy(X1,Y0,zm)
    im=Image.new('RGB',((int(tx1)-int(tx0)+1)*256,(int(ty1)-int(ty0)+1)*256))
    for tx in range(int(tx0),int(tx1)+1):
        for ty in range(int(ty0),int(ty1)+1):
            req=urllib.request.Request(url.format(z=zm,x=tx,y=ty),headers={'User-Agent':'DigitalRanger-site-build/1.0'})
            for t in range(3):
                try: im.paste(Image.open(io.BytesIO(urllib.request.urlopen(req,timeout=20).read())).convert('RGB'),((tx-int(tx0))*256,(ty-int(ty0))*256)); break
                except Exception as e: time.sleep(1)
    crop=(round((tx0-int(tx0))*256),round((ty0-int(ty0))*256),round((tx1-int(tx0))*256),round((ty1-int(ty0))*256))
    return im.crop(crop)
def finish(im,name):
    W=2048; H=round(W*(Y1-Y0)/(X1-X0)); im=im.resize((W,H),Image.LANCZOS)
    d=ImageDraw.Draw(im); pts=[((x-X0)/(X1-X0)*W,(Y1-y)/(Y1-Y0)*H) for x,y in zip(zx,zy)]
    d.line(pts+[pts[0]],fill=(255,255,255),width=9,joint='curve'); d.line(pts+[pts[0]],fill=(210,25,35),width=5,joint='curve')
    im.save(O+'/img/relief/'+name,quality=78,optimize=True,progressive=True); print(name,im.size,os.path.getsize(O+'/img/relief/'+name)//1024,'KB')
if os.environ.get('DALE','1')=='1': finish(mosaic('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',15,'jpg'),'textura-satelit.jpg')
if os.environ.get('DALE','1')=='1': finish(mosaic('https://a.tile.opentopomap.org/{z}/{x}/{y}.png',15,'png'),'textura-topo.jpg')
print('relief.json',NX,'x',NY,os.path.getsize(O+'/date/relief/relief.json')//1024,'KB')

# 3. straturile care se pot porni și opri pe modelul 3D (coordonate în pixeli de textură, 2048 × H)
from shapely.geometry import box as sbox, Point
from shapely.ops import unary_union as uu, linemerge
TW=2048; TH=int(round(float(TW*(Y1-Y0)/(X1-X0))))
lo0,la0=to4326.transform(X0,Y0); lo1,la1=to4326.transform(X1,Y1); CLIP=sbox(lo0,la0,lo1,la1)
def P(lon,lat):
    x,y=to3857.transform(lon,lat); return [round(float((x-X0)/(X1-X0)*TW),1),round(float((Y1-y)/(Y1-Y0)*TH),1)]
def flat(coords): return [v for c in coords for v in P(*c[:2])]
def polys(g):
    g=(g if g.is_valid else g.buffer(0)).intersection(CLIP); out=[]
    for p in getattr(g,'geoms',[g]):
        if p.geom_type=='Polygon' and not p.is_empty: out.append([flat(p.exterior.coords)]+[flat(i.coords) for i in p.interiors])
    return out
def lines(g):
    g=(g if g.is_valid or g.geom_type.endswith('String') else g.buffer(0)).intersection(CLIP); out=[]
    for l in getattr(g,'geoms',[g]):
        if l.geom_type=='LineString' and not l.is_empty: out.append(flat(l.coords))
        elif l.geom_type=='Polygon': out.append(flat(l.exterior.coords))
    return out
s=open(O+'/date/harta/straturi.js',encoding='utf8').read(); S=json.loads(s[s.index('{'):s.rstrip().rstrip(';').rindex('}')+1])
L={}
L['contur']=lines(shape(S['contur']['features'][0]['geometry']).boundary)
L['parc']=lines(uu([shape(f['geometry']).buffer(0) for f in S['parc']['features']]).boundary)
L['zonare']={f['properties']['zonare']:polys(shape(f['geometry'])) for f in S['zonare']['features']}
L['trasee']=[{'oficial':f['properties'].get('oficial',False),'nume':f['properties']['nume'],'l':lines(shape(f['geometry']))} for f in S['trasee']['features']]
L['pante']=polys(uu([shape(f['geometry']) for f in S['pante']['features']]))
L['incendiu']=[{'data':f['properties']['data'],'p':polys(shape(f['geometry']))} for f in S['incendiu']['features']]
pr=json.load(open(G+'/Digital-Ranger_zona_parcele-silvice.geojson'))['features']
L['parcele']=lines(linemerge(uu([shape(f['geometry']).buffer(0).simplify(0.00002).boundary for f in pr if not f['properties']['ua'].endswith(('DD','VV'))])))
L['drumuri']=lines(uu([shape(f['geometry']).buffer(0) for f in pr if f['properties']['ua'].endswith('DD')]).boundary)
def pt3(name,lon,lat):
    x,y=to3857.transform(lon,lat); u=(x-X0)/(X1-X0); v=(Y1-y)/(Y1-Y0)
    return [name,round(float((u-0.5)*float(sx)*SCALE/1000),1),round(float((v-0.5)*float(sy)*SCALE/1000),1),round(float(elev[int(v*(NY-1)),int(u*(NX-1))]),1)]
dom=[f['geometry']['coordinates'] for f in z['features'] if f['geometry']['type']=='Point' and f['properties']['name'].startswith('Domogledul')][0]
ELICOPTER=[('Vf. Domogled',dom[0],dom[1]),('Vf. Șușcu (1192 m)',22.44871,44.89190),('Vf. Hurcu',22.44949,44.90386)]   # coordonate de la GG, 21.11.2026
out={'w':TW,'h':TH,'straturi':L,'elicopter':[pt3(*e) for e in ELICOPTER]}
json.dump(out,open(O+'/date/relief/straturi3d.json','w',encoding='utf8'),ensure_ascii=False,separators=(',',':'))
print('straturi3d.json',os.path.getsize(O+'/date/relief/straturi3d.json')//1024,'KB',{k:(len(v) if isinstance(v,list) else len(v)) for k,v in L.items()},out['elicopter'])
