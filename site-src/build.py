"""Generatorul site-ului Digital Ranger.
Rulare din rădăcina proiectului:  python3 site-src/build.py
Conținutul paginilor: site-src/pagini/<cale>.html (antet în comentariu + corpul paginii).
Ieșire: site/<cale>.html. În pagini: {{R}} = calea spre rădăcină, {{ORDIN_PMI}} = link-ul spre ordinul PMI 2025.
"""
import os, re, html
BASE=os.path.dirname(os.path.abspath(__file__)); SITE=os.path.join(BASE,"..","site"); SRC=os.path.join(BASE,"pagini")

# Când ordinul de aprobare a PMI 2025 e publicat, pune aici adresa lui (ex. Monitorul Oficial) și rulează din nou.
ORDIN_PMI_URL = None

NAV=[("incendiu/index.html","Incendiu 2026–2029","incendiu"),
     ("monitorizare/index.html","Monitorizare digitală","monitorizare"),
     ("harta-interactiva.html","Hartă","harta"),
     ("extindere-dupa-2029.html","Extindere după 2029","extindere"),
     ("principii.html","Principii","principii"),
     ("contact.html","Contact","contact")]
SUB={"incendiu":("Incendiu 2026–2029",[("incendiu/index.html","Pe scurt"),("incendiu/zona-domogled.html","Zona Domogled"),
        ("incendiu/incendiul-2026.html","Incendiul din 2026"),("incendiu/pregatire.html","Pregătirea"),("incendiu/calendar-tinte.html","Calendar și ținte")]),
     "monitorizare":("Monitorizare digitală",[("monitorizare/index.html","Pe scurt"),("pilot/index.html","Pilotul 2027–2029"),
        ("tehnologii/index.html","Tehnologii"),("scenarii/index.html","Scenarii"),("pilot/jurnal-si-rezultate.html","Jurnal și rezultate")])}

TPL="""<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="{R}assets/css/site.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Ccircle cx='8' cy='8' r='7' fill='%232C5F2D'/%3E%3C/svg%3E">
</head>
<body>
<a class="skip" href="#continut">Sari la conținut</a>
<div class="topbar">
  <div class="wrap">
    <a class="brand" href="{R}index.html"><span class="dot"></span><span>Digital Ranger<small>Parcul Național Domogled–Valea Cernei · zona Domogled</small></span></a>
    <nav class="nav" aria-label="Meniu principal">
{nav}
    </nav>
  </div>
</div>
{hero}{subnav}
<main id="continut">
{body}
</main>
<footer>
  <div class="wrap">
    <div>
      <h3>Digital Ranger</h3>
      <p>Pregătire pentru incendiu și monitorizare digitală în zona Domogled, Parcul Național Domogled–Valea Cernei. Pilot propus pentru 2027–2029, operat din hub-ul de Sud (sediul parcului, Băile Herculane).</p>
    </div>
    <div>
      <h3>Contact</h3>
      <p><strong>Lungu Gheorghe</strong>, inițiatorul proiectului<br>Telefon: <a href="tel:+40721879347" style="color:var(--moss-light)">+40 721 879 347</a><br><a href="{R}contact.html" style="color:var(--moss-light)">Formular de contact →</a></p>
    </div>
  </div>
  <div class="wrap">
    <p class="disclaimer">Digital Ranger este un proiect-concept independent și o viziune pentru viitor. Nu reprezintă poziția oficială a administrației Parcului Național Domogled–Valea Cernei, a Romsilva, a IGSU sau a Ministerului Mediului. Date: Copernicus Sentinel-2, NASA FIRMS, EFFIS, prelucrare proprie; zonarea: Planul de management integrat 2025 (<a href="{ORDIN}" style="color:#a9bd96;text-decoration:underline">în curs de aprobare prin ordin de ministru</a>).</p>
  </div>
</footer>
</body>
</html>
"""

def meta(txt):
    m=re.match(r"\s*<!--(.*?)-->\s*",txt,re.S); d={}
    for line in m.group(1).strip().splitlines():
        k,_,v=line.partition(":"); d[k.strip()]=v.strip()
    return d, txt[m.end():]

def build(rel):
    d,body=meta(open(os.path.join(SRC,rel),encoding="utf8").read())
    depth=rel.count("/"); R="../"*depth
    sec=d.get("section","")
    nav="\n".join(f'      <a href="{R}{p}"'+(' aria-current="page"' if s==sec else '')+f'>{t}</a>' for p,t,s in NAV)
    hero=""; subnav=""
    if d.get("hero","sub")=="sub":
        crumbs=f'<a href="{R}index.html">Acasă</a>'
        if sec in SUB and rel!=SUB[sec][1][0][0]:
            crumbs+=f' / <a href="{R}{SUB[sec][1][0][0]}">{SUB[sec][0]}</a>'
        lead=f'\n    <p class="sublead">{d["lead"]}</p>' if d.get("lead") else ""
        hero=f'<header class="subhero">\n  <div class="wrap">\n    <div class="crumbs">{crumbs}</div>\n    <h1>{d["h1"]}</h1>{lead}\n  </div>\n</header>\n'
    if sec in SUB:
        items="".join(f'<a href="{R}{p}"'+(' aria-current="page"' if p==rel else '')+f'>{t}</a>' for p,t in SUB[sec][1])
        subnav=f'<nav class="subnav" aria-label="{SUB[sec][0]}"><div class="wrap">{items}</div></nav>\n'
    ordin=ORDIN_PMI_URL or f"{R}ordin-pmi.html"
    title=d["title"] if d.get("hero")=="none" else f'{d["title"]} · Digital Ranger'
    out=TPL.format(title=html.escape(title,quote=False),desc=html.escape(d.get("description",""),quote=True),R=R,nav=nav,hero=hero,subnav=subnav,body=body.strip(),ORDIN=ordin)
    out=out.replace("{{R}}",R).replace("{{ORDIN_PMI}}",ordin)
    dst=os.path.join(SITE,rel); os.makedirs(os.path.dirname(dst),exist_ok=True)
    open(dst,"w",encoding="utf8").write(out); return rel

if __name__=="__main__":
    done=[]
    for root,_,files in os.walk(SRC):
        for f in files:
            if f.endswith(".html"): done.append(build(os.path.relpath(os.path.join(root,f),SRC).replace(os.sep,"/")))
    print(len(done),"pagini:",", ".join(sorted(done)))
