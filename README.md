# Digital Ranger

Site-ul proiectului-concept **Digital Ranger**: pregătire pentru incendiu și monitorizare digitală într-un pilot de trei ani (2027–2029) în zona Domogled, Parcul Național Domogled–Valea Cernei.

Publicat la: https://ranger-digital.netlify.app

> Digital Ranger este un proiect-concept independent. Nu reprezintă poziția oficială a administrației Parcului Național Domogled–Valea Cernei, a Romsilva, a IGSU sau a Ministerului Mediului.

## Structura

- `site/`: site-ul static, exact cum se publică. Netlify publică acest folder (vezi `netlify.toml`), fără pas de build.
- `site-src/`: generatorul paginilor și scripturile hărților.
  - `build.py`: generează paginile din `site-src/pagini/` (meniul, subsolul, link-ul spre ordinul PMI 2025). Când apare ordinul, se completează `ORDIN_PMI_URL`.
  - `harta_parcele.py`, `harti.py`, `relief3d.py`, `media.py`: hărțile, straturile hărții de consultare și modelul 3D.

Scripturile din `site-src/` (în afară de `build.py`) au nevoie de datele GIS ale proiectului, care nu sunt în acest repo. De aceea `site/` se generează local și se publică așa cum e.

## Actualizare

```
python3 site-src/build.py     # din rădăcina proiectului local
```

Apoi se copiază `site/` și `site-src/` aici, se face commit și push. Netlify publică automat la fiecare push pe `main`.

## Surse de date

Copernicus Sentinel-2, NASA FIRMS, EFFIS, prelucrare proprie; zonarea: Planul de management integrat 2025 (baza GIS 10.11.2023); fonduri de hartă: © OpenStreetMap contributors, OpenTopoMap (CC-BY-SA), Esri World Imagery; relief: SRTM.
