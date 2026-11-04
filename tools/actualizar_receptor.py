#!/usr/bin/env python3
"""Uso único: sustituye en el servidor el receptor deploy.php v1 por la v2 (reforzada).
El v1 no permite sobrescribir deploy.php, así que se sube un script temporal (_upd.php)
protegido con el mismo token, que hace el cambio y se borra a sí mismo."""
import hashlib, io, json, os, sys, urllib.request, zipfile, secrets
from pathlib import Path

URL = os.environ["DEPLOY_URL"].strip(); TOKEN = os.environ["DEPLOY_TOKEN"].strip()
H = hashlib.sha256(TOKEN.encode()).hexdigest()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0 Safari/537.36"
v2 = (Path(__file__).parent.parent / "receptor/deploy.php").read_text(encoding="utf-8").replace("__TOKEN_SHA256__", H)
name = f"_upd_{secrets.token_hex(6)}.php"
upd = f"""<?php
header('Content-Type: application/json');
if (!hash_equals('{H}', hash('sha256', $_SERVER['HTTP_X_DEPLOY_TOKEN'] ?? ''))) {{ http_response_code(403); @unlink(__FILE__); exit('{{"ok":false}}'); }}
$ok = file_put_contents(__DIR__ . '/deploy.php', base64_decode('{__import__('base64').b64encode(v2.encode()).decode()}'), LOCK_EX) !== false;
@unlink(__FILE__);
echo json_encode(['ok' => $ok]);
"""

def req(url, data=None, ctype="application/octet-stream"):
    r = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET",
                               headers={"X-Deploy-Token": TOKEN, "Content-Type": ctype, "User-Agent": UA})
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return x.status, x.read().decode()
    except urllib.error.HTTPError as ex:
        return ex.code, ex.read().decode()[:300]

st, body = req(URL + "?action=manifest")
v = json.loads(body).get("version", 1) if st == 200 else None
print(f"::notice::Receptor actual: versión {v}")
if v == 2:
    sys.exit(0)
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w") as z:
    z.writestr(name, upd)
print("subida:", req(URL + "?action=upload", buf.getvalue(), "application/zip"))
base = URL.rsplit("/", 1)[0] + "/"
print("cambio:", req(base + name, b"{}", "application/json"))
st, body = req(URL + "?action=manifest")
v = json.loads(body).get("version", 1) if st == 200 else None
print(f"::notice::Receptor tras el cambio: versión {v}")
st2, _ = req(base + name)
print(f"::notice::Script temporal borrado: {'sí' if st2 == 404 else 'NO (código ' + str(st2) + ')'}")
sys.exit(0 if v == 2 else 1)
