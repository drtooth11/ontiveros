#!/usr/bin/env python3
"""Copia a src/img/ todas las imágenes de WordPress que usa la web.

Busca las rutas /wp-content/uploads/... en content.json y build.py y descarga
las que falten desde clinicadentalontiveros.es. Una vez copiadas, la web deja de depender
de WordPress para las imágenes.
"""
import re, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
DEST = ROOT / "src" / "img"
BASE = "https://clinicadentalontiveros.es"
PAT = re.compile(r"/wp-content/uploads/[^\"'\s)<>]+\.(?:jpg|jpeg|png|gif|webp|svg)", re.I)

paths = set()
for f in (ROOT / "src" / "content.json", ROOT / "build.py"):
    paths.update(PAT.findall(f.read_text(encoding="utf-8")))

DEST.mkdir(parents=True, exist_ok=True)
ok = fail = skip = 0
for p in sorted(paths):
    out = DEST / p[len("/wp-content/uploads/"):]
    if out.exists():
        skip += 1
        continue
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(BASE + p, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            out.write_bytes(r.read())
        ok += 1
    except Exception as ex:
        print("FALLO", p, ex)
        fail += 1
print(f"Descargadas {ok}, ya existían {skip}, fallos {fail} (total {len(paths)})")
