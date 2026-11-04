#!/usr/bin/env python3
"""Publica dist/ en el servidor a través de receptor/deploy.php (HTTPS).

Pide al servidor la lista de archivos que ya tiene (con su huella), y envía
solo los que han cambiado, en bloques .zip de ~1,5 MB para no chocar con los
límites de subida del hosting.

La dirección sale de url_publica (content.json) + deploy.php; el secreto DEPLOY_URL
queda como referencia. Variable de entorno obligatoria: DEPLOY_TOKEN.
"""
import hashlib, io, json, os, sys, urllib.request, zipfile
from pathlib import Path

DIST = Path(__file__).parent / "dist"
def fail(msg):
    print(f"::error::{msg}")
    sys.exit(1)

_cfg = json.loads((Path(__file__).parent / "src" / "content.json").read_text(encoding="utf-8"))
URL = _cfg["url_publica"].rstrip("/") + "/deploy.php"   # se publica donde vive la web
TOKEN = os.environ.get("DEPLOY_TOKEN", "").strip()
if not URL or not TOKEN:
    fail(f"Faltan secretos: DEPLOY_URL={'sí' if URL else 'NO'}, DEPLOY_TOKEN={'sí' if TOKEN else 'NO'}")
LIMIT = 1_500_000

def call(action, data=None, ctype="application/octet-stream"):
    req = urllib.request.Request(f"{URL}?action={action}", data=data, method="POST" if data is not None else "GET",
                                 headers={"X-Deploy-Token": TOKEN, "Content-Type": ctype, "User-Agent": "ontiveros-deploy"})
    import time
    for intento in range(1, 4):   # reintenta fallos momentáneos del hosting
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                cuerpo = r.read()
                try:
                    return json.loads(cuerpo)
                except ValueError:
                    raise RuntimeError(f"respuesta no válida: HTTP {r.status}, URL final {r.geturl()}, "
                                       f"tipo {r.headers.get('Content-Type')}, {len(cuerpo)} bytes: {cuerpo[:300]!r}")
        except urllib.error.HTTPError as ex:
            if ex.code < 500 or intento == 3:
                fail(f"HTTP {ex.code} en '{action}' ({URL}): {ex.read()[:300]!r}")
        except Exception as ex:
            if intento == 3:
                diag = []
                for nombre, url, h in (("sin token", f"{URL}?action=manifest", {"User-Agent": "ontiveros-deploy"}),
                                       ("contact.php", URL.replace("deploy.php", "contact.php"), {"User-Agent": "Mozilla/5.0"})):
                    try:
                        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r2:
                            b = r2.read(); diag.append(f"{nombre}: HTTP {r2.status}, {len(b)} bytes {b[:120]!r}")
                    except urllib.error.HTTPError as e2:
                        b = e2.read(); diag.append(f"{nombre}: HTTP {e2.code}, {len(b)} bytes {b[:120]!r}")
                    except Exception as e2:
                        diag.append(f"{nombre}: {e2!r}")
                print("::warning::Diagnóstico: " + " | ".join(diag))
                fail(f"Fallo en '{action}' ({URL}): {ex!r}")
        print(f"::warning::Reintentando '{action}' ({intento}/3)…")
        time.sleep(10 * intento)

local = {p.relative_to(DIST).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in sorted(DIST.rglob("*")) if p.is_file()}
info = call("manifest")
if not info.get("zip"):
    fail("El servidor no tiene ZipArchive de PHP")
version = info.get("version", 1)
remote = info.get("manifest") or {}
if os.environ.get("COMPLETO") == "1":   # vuelve a subir todo (p. ej. tras copiar carpetas a mano)
    changed = list(local)
else:
    changed = [f for f, h in local.items() if remote.get(f) != h]
print(f"::notice::{len(local)} archivos, {len(changed)} con cambios: {', '.join(changed[:15])}")

batch, size, sent = [], 0, 0
def flush():
    global batch, size, sent
    if not batch:
        return
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in batch:
            z.write(DIST / f, f)
    r = call("upload", buf.getvalue(), "application/zip")
    sent += r.get("files", 0)
    if r.get("rechazados"):
        print(f"::warning::El servidor rechazó por seguridad: {', '.join(r['rechazados'])}")
    print(f"  bloque enviado: {r.get('files')} archivos")
    batch, size = [], 0

for f in changed:
    s = (DIST / f).stat().st_size
    if batch and size + s > LIMIT:
        flush()
    batch.append(f); size += s
flush()

stale = sorted(set(remote) - set(local))
if stale:
    if version >= 2:
        r = call("delete", json.dumps(stale).encode(), "application/json")
        print(f"::notice::Borrados {r.get('deleted')} archivos que ya no se usan: {', '.join(stale[:15])}")
    else:
        print(f"::warning::Hay {len(stale)} archivos antiguos en el servidor; sube el deploy.php nuevo para poder limpiarlos.")
        local = {**{k: remote[k] for k in stale}, **local}   # se recuerdan para borrarlos más adelante
call("commit", json.dumps(local).encode(), "application/json")
# Comprobación final: la web responde. Si el servidor no acepta alguna regla del
# .htaccess (error 500), se sustituye por uno mínimo y se avisa.
SITE = URL.rsplit("/", 1)[0] + "/"
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
def status(path):
    try:
        req = urllib.request.Request(SITE + path, headers={"User-Agent": BROWSER_UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as ex:
        return ex.code
    except Exception:
        return 0
bad = [(p, c) for p in ("", "tratamientos/", "contacto/") if (c := status(p)) >= 500 or c == 0]
if bad:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(".htaccess", "# .htaccess mínimo de emergencia (el completo dio error en este servidor)\nDirectoryIndex index.html\n")
    call("upload", buf.getvalue(), "application/zip")
    again = [(p, status(p)) for p, _ in bad]
    fail(f"La web daba error {bad} con el .htaccess completo; se ha puesto uno mínimo. Tras el cambio: {again}")
# Comprobación de páginas clave: todas deben responder 200
codes = {p: status(p) for p in ("", "quienes-somos/", "tratamientos/", "contacto/", "assets/styles.css")}
if any(c != 200 for c in codes.values()):
    fail(f"La web no responde bien tras publicar: {codes}")
print(f"OK: {sent} archivos publicados, web respondiendo correctamente")
