#!/usr/bin/env python3
"""Genera la web estática de Clínica Dental Ontiveros a partir de src/content.json.

Uso:  python3 build.py           -> genera ./dist

Ajustes clave en content.json:
  url_publica  dirección donde vive la web (pruebas: https://clinicadentalontiveros.es/web/,
               al pasar a la raíz: https://clinicadentalontiveros.es/). De aquí salen los
               enlaces internos, canonical, sitemap y redirecciones.
  recursos     dominio de donde se toman las imágenes que aún no estén copiadas en src/img/.
  noindex      true mientras sea una web de pruebas.
"""
import json, shutil, html, re, hashlib, datetime, os
from pathlib import Path
from urllib.parse import urlparse, quote
from zoneinfo import ZoneInfo
from PIL import Image

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
C = json.loads((SRC / "content.json").read_text(encoding="utf-8"))
S = C["site"]
URL_PUB = C["url_publica"].rstrip("/") + "/"
_u = urlparse(URL_PUB)
ORIGIN = f"{_u.scheme}://{_u.netloc}"
PREFIX = _u.path if _u.path.endswith("/") else _u.path + "/"     # "/web/" o "/"
RES = C["recursos"].rstrip("/")
NOINDEX = bool(C.get("noindex"))
HOY = datetime.datetime.now(ZoneInfo("Europe/Madrid")).date()
TODAY = HOY.isoformat()

# Páginas: mismas URLs que la web WordPress para conservar el posicionamiento
PAGES = {
    "home": "",
    "quienes": "quienes-somos/",
    "equipo": "equipo-medico/",
    "instalaciones": "instalaciones/",
    "tratamientos": "tratamientos/",
    "contacto": "contacto/",
    "aviso": "aviso-legal/",
    "privacidad": "politica-de-privacidad/",
    "cookies": "politica-de-cookies/",
}
# URLs de WordPress que no se migran -> redirección 301 (solo en la raíz)
OLD_WP = {"hello-world/": "home", "category/uncategorized/": "home", "home/": "home"}

def L(key):            # enlace interno
    return PREFIX + PAGES[key]
def ABS(key):          # URL absoluta (canonical, sitemap)
    return ORIGIN + L(key)

WP = "/wp-content/uploads/"
IMG_SRC = SRC / "img"
DIMS = {}              # url -> (ancho, alto)
MAXW = 1600

def u(path, maxw=MAXW):
    """URL de una imagen.
    - Con copia en src/img/ (la descarga fetch_images.py en GitHub): se optimiza a WebP y se
      sirve desde la propia web (img/...), sin depender de WordPress.
    - Sin copia: URL absoluta al dominio de recursos (solo útil para vistas previas).
    """
    if not path:
        return ""
    if path.startswith("http"):
        return path
    if path.startswith("/img/"):
        path = WP + path[len("/img/"):]
    if path.startswith(WP):
        rel = path[len(WP):]
        local = IMG_SRC / rel
        if local.exists():
            if local.suffix.lower() == ".svg":
                dest = DIST / "img" / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(local, dest)
                return PREFIX + "img/" + rel
            relw = str(Path(rel).with_suffix(".webp"))
            url = PREFIX + "img/" + relw
            dest = DIST / "img" / relw
            if not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                im = Image.open(local)
                im = im.convert("RGBA") if (im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)) else im.convert("RGB")
                if im.width > maxw:
                    im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
                im.save(dest, "WEBP", quality=80, method=6)
            with Image.open(dest) as im:
                DIMS[url] = im.size
            return url
    return RES + path

def absu(url):
    return url if url.startswith("http") else ORIGIN + url

e = html.escape

def vhash(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:10]

def slug(t):
    import unicodedata
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")

# ---------- Iconos ----------
def _svg(d, sw="1.8"):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d}</svg>')
I = {
 "phone": _svg('<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>'),
 "callback": _svg('<path d="M15 3h6v6M21 3l-7 7"/><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>'),
 "mail": _svg('<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>'),
 "pin": _svg('<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>'),
 "clock": _svg('<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>'),
 "cal": _svg('<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18M9 15l2 2 4-4"/>'),
 "arrow": _svg('<path d="M5 12h14M13 5l7 7-7 7"/>', "2"),
 "check": _svg('<path d="M20 6 9 17l-5-5"/>', "2.4"),
 "plus": _svg('<path d="M12 5v14M5 12h14"/>', "2"),
 "close": _svg('<path d="M18 6 6 18M6 6l12 12"/>', "2"),
 "award": _svg('<circle cx="12" cy="8" r="6"/><path d="M15.5 13 17 22l-5-3-5 3 1.5-9"/>'),
 "hand": _svg('<path d="m11 17 2 2a1 1 0 1 0 3-3"/><path d="m14 14 2.5 2.5a1 1 0 1 0 3-3l-3.9-3.9a3 3 0 0 0-4.2 0l-.9.9a1 1 0 1 1-3-3l2.8-2.8a5.8 5.8 0 0 1 7.1-.9l.5.3a2 2 0 0 0 1.4.3L21 4"/><path d="m21 3 1 11h-2M3 3 2 14l6.5 6.5a1 1 0 1 0 3-3M3 4h8"/>'),
 "bolt": _svg('<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>'),
 "smile": _svg('<circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01"/>'),
 "sofa": _svg('<path d="M20 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v3"/><path d="M2 11v5a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5a2 2 0 0 0-4 0v2H6v-2a2 2 0 0 0-4 0zM4 18v2M20 18v2"/>'),
 "chair": _svg('<path d="M7 3v8a3 3 0 0 0 3 3h7l3 4M7 11h9M9 14l-2 7M17 14v7M4 7h3"/>'),
 "shield": _svg('<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>'),
 "xray": _svg('<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 9c1-1 2-1 2 1s-1 4 0 5 2-1 2-3 1-4 2-4 2 2 1 4"/>'),
 "tooth": _svg('<path d="M12 5.5C10.5 4 8.5 3 6.5 3.5 3.5 4.3 3 7.5 4 11c.6 2 1 4 1.3 6 .3 2.3 1 4 2.2 4 1.5 0 1.6-2.5 2-4.5.3-1.5.8-2.5 2.5-2.5s2.2 1 2.5 2.5c.4 2 .5 4.5 2 4.5 1.2 0 1.9-1.7 2.2-4 .3-2 .7-4 1.3-6 1-3.5.5-6.7-2.5-7.5-2-.5-4 .5-5.5 2z"/>'),
 "quote": '<svg viewBox="0 0 32 32" fill="currentColor" aria-hidden="true"><path d="M13 8C7.5 9.6 4 13.8 4 19.5 4 23 6.3 25 9 25c2.6 0 4.6-2 4.6-4.6 0-2.5-1.8-4.3-4.1-4.5.6-2.8 2.6-4.9 5.2-5.8zm14 0c-5.5 1.6-9 5.8-9 11.5 0 3.5 2.3 5.5 5 5.5 2.6 0 4.6-2 4.6-4.6 0-2.5-1.8-4.3-4.1-4.5.6-2.8 2.6-4.9 5.2-5.8z"/></svg>',
 "star": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8-6.2-3.2L5.8 21 7 14.2 2 9.3l6.9-1z"/></svg>',
 "wa": '<svg viewBox="0 0 32 32" fill="currentColor" aria-hidden="true"><path d="M16 3a13 13 0 0 0-11.2 19.6L3 29l6.6-1.7A13 13 0 1 0 16 3zm0 23.7a10.7 10.7 0 0 1-5.5-1.5l-.4-.2-3.9 1 1-3.8-.2-.4A10.7 10.7 0 1 1 16 26.7zm5.9-8c-.3-.2-1.9-1-2.2-1s-.5-.2-.7.2-.8 1-1 1.2-.4.2-.7 0a8.8 8.8 0 0 1-4.4-3.8c-.3-.6.3-.5.9-1.6.1-.2 0-.4 0-.5l-1-2.4c-.3-.6-.5-.5-.7-.5h-.6a1.2 1.2 0 0 0-.9.4 3.6 3.6 0 0 0-1.1 2.7 6.3 6.3 0 0 0 1.3 3.3 14.4 14.4 0 0 0 5.5 4.9c2 .9 2.8 1 3.9.8a3.3 3.3 0 0 0 2.1-1.5 2.7 2.7 0 0 0 .2-1.5c-.1-.1-.3-.2-.6-.4z"/></svg>',
}

WA_URL = S["whatsapp"] + "?text=" + quote(S.get("whatsapp_texto", ""))
CITA = L("contacto") + "#cita"

NAV = [("home", "Inicio"), ("quienes", "Quiénes somos"), ("instalaciones", "Instalaciones"),
       ("tratamientos", "Tratamientos"), ("contacto", "Contacto")]
LEGAL = [("aviso", "Aviso legal", "aviso-legal.html"),
         ("privacidad", "Política de privacidad", "politica-de-privacidad.html"),
         ("cookies", "Política de cookies", "politica-de-cookies.html")]

def nav_html(active):
    out = []
    for key, label in NAV:
        cur = ' aria-current="page"' if key == active or (active == "equipo" and key == "quienes") else ''
        out.append(f'<a href="{L(key)}"{cur}>{label}</a>')
    return "\n".join(out)

def clinic_jsonld():
    d = {
        "@context": "https://schema.org",
        "@type": "Dentist",
        "@id": ORIGIN + "/#clinica",
        "name": S["name"],
        "url": ORIGIN + "/",
        "logo": absu(u(S["logo"])),
        "image": absu(u(C["home"]["hero_img"])),
        "telephone": S["tel1_href"],
        "email": S["email"],
        "foundingDate": S.get("fundacion", ""),
        "address": {"@type": "PostalAddress", "streetAddress": S["calle"], "postalCode": S["cp"],
                    "addressLocality": S["ciudad"], "addressRegion": S["provincia"], "addressCountry": "ES"},
        "areaServed": {"@type": "City", "name": "Marbella"},
        "medicalSpecialty": "Dentistry",
        "availableService": [{"@type": "MedicalProcedure", "name": t["titulo"]} for t in C["tratamientos"]["lista"]],
        "contactPoint": [{"@type": "ContactPoint", "telephone": S["tel1_href"], "contactType": "customer service",
                          "availableLanguage": "es"}],
    }
    if S.get("horario"):
        d["openingHoursSpecification"] = [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": h["dias"], "opens": h["abre"], "closes": h["cierra"]}
            for h in S["horario"] if h.get("abre")]
    return d

def faq_jsonld(items):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in items]}

def horario_html(cls="hor"):
    h = S.get("horario") or []
    if not h:
        return ""
    rows = "".join(f'<li><span>{e(x["texto_dias"])}</span><span>{e(x["texto_horas"])}</span></li>' for x in h)
    return f'<ul class="{cls}">{rows}</ul>'

def page(key, title, body, desc, h1=None, og_img=None, extra_ld=None):
    v_css, v_js = vhash(DIST / "assets/styles.css"), vhash(DIST / "assets/main.js")
    canonical = ABS(key) if key in PAGES else ""
    og_img = absu(og_img or u(C["home"]["hero_img"]))
    ld = [clinic_jsonld()] if key == "home" else []
    if key == "home":
        ld.append({"@context": "https://schema.org", "@type": "WebSite", "name": S["name"], "url": ORIGIN + "/",
                   "inLanguage": "es-ES", "publisher": {"@id": ORIGIN + "/#clinica"}})
    elif key in PAGES:
        ld.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": ABS("home")},
            {"@type": "ListItem", "position": 2, "name": h1 or title, "item": canonical}]})
    ld += extra_ld or []
    ld_html = "\n".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    robots = "noindex, nofollow" if (NOINDEX or key == "404") else "index, follow, max-image-preview:large, max-snippet:-1"
    fav = u(S["favicon"], 192)
    canon = f'<link rel="canonical" href="{canonical}">\n<meta property="og:url" content="{canonical}">\n' if canonical else ""
    doc = f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{robots}">
{canon}<meta name="theme-color" content="#0b3a6e">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_ES">
<meta property="og:site_name" content="{e(S["name"])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{og_img}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{fav}">
<link rel="apple-touch-icon" href="{fav}">
<link rel="preload" href="{PREFIX}assets/fonts/inter-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{PREFIX}assets/fonts/fraunces-latin-500-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{PREFIX}assets/styles.css?v={v_css}">
<script src="{PREFIX}assets/main.js?v={v_js}" defer></script>
{ld_html}
</head>
<body class="p-{key}">
<a class="skip" href="#contenido">Saltar al contenido</a>
<header class="header"><div class="wrap">
  <a class="logo" href="{L("home")}" aria-label="{e(S["name"])}, inicio"><img src="{u(S["logo"])}" alt="{e(S["name"])}" width="218" height="50"></a>
  <nav class="nav" id="menu" aria-label="Principal">
{nav_html(key)}
    <a class="nav-tel" href="tel:{S["tel1_href"]}">{I["phone"]} {S["tel1"]}</a>
  </nav>
  <a class="btn btn-cita hdr-cita" href="{CITA}">Pide cita</a>
  <button class="burger" type="button" aria-label="Abrir menú" aria-expanded="false" aria-controls="menu"><span></span></button>
</div></header>
<main id="contenido">
{body}
</main>
<footer class="footer">
  <div class="wrap">
    <div class="f-top">
      <div class="f-brand">
        <a class="f-logo" href="{L("home")}"><img src="{u(S["logo"])}" alt="{e(S["name"])}" loading="lazy" width="218" height="50"></a>
        <p>Clínica dental en Marbella desde {S.get("fundacion", "2001")}.</p>
      </div>
      <div>
        <p class="f-h">Contacto</p>
        <p><a href="tel:{S["tel1_href"]}">+34 {S["tel1"]}</a><br><a href="tel:{S["tel2_href"]}">+34 {S["tel2"]}</a><br><a href="mailto:{S["email"]}">{S["email"]}</a></p>
      </div>
      <div>
        <p class="f-h">Dónde estamos</p>
        <p>{e(S["address"])}</p>
        {horario_html("hor f-hor")}
      </div>
      <nav aria-label="Pie">
        <p class="f-h">La clínica</p>
        <ul>
          <li><a href="{L("quienes")}">Quiénes somos</a></li>
          <li><a href="{L("equipo")}">Equipo médico</a></li>
          <li><a href="{L("instalaciones")}">Instalaciones</a></li>
          <li><a href="{L("tratamientos")}">Tratamientos</a></li>
          <li><a href="{L("contacto")}">Contacto</a></li>
        </ul>
      </nav>
    </div>
    <div class="f-bottom">
      <span>© {TODAY[:4]} {e(S["name"])}</span>
      <ul>{"".join(f'<li><a href="{L(k)}">{t}</a></li>' for k, t, _ in LEGAL)}</ul>
    </div>
  </div>
</footer>
<nav class="mbar" aria-label="Contacto rápido">
  <a href="tel:{S["tel1_href"]}">{I["phone"]}<span>Llamar</span></a>
  <a href="{WA_URL}" target="_blank" rel="noopener noreferrer">{I["wa"]}<span>WhatsApp</span></a>
  <a class="mbar-cita" href="{CITA}">{I["cal"]}<span>Pide cita</span></a>
</nav>
<a class="wa-float" href="{WA_URL}" target="_blank" rel="noopener noreferrer" aria-label="Escribir por WhatsApp">{I["wa"]}</a>
</body>
</html>
'''
    doc = add_dims(doc)
    out = DIST / PAGES[key] / "index.html" if key in PAGES else DIST / "404.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")

def add_dims(doc):
    def rep(m):
        tag = m.group(0)
        if " width=" in tag:
            return tag
        src = re.search(r'src="([^"]+)"', tag)
        if src and src.group(1) in DIMS:
            w, h = DIMS[src.group(1)]
            return tag[:-1] + f' width="{w}" height="{h}">'
        return tag
    return re.sub(r"<img\b[^>]*>", rep, doc)

# ---------- Piezas comunes ----------
def bloques(items):
    """Bloques de texto de content.json: "texto" (párrafo), {"lista": [...]}, {"h": "..."}, {"h3": "..."}.
    Los textos se escriben tal cual (pueden llevar <strong>)."""
    out = []
    for b in items:
        if isinstance(b, str):
            out.append(f"<p>{b}</p>")
        elif "lista" in b:
            out.append("<ul class=\"ticks\">" + "".join(f"<li>{x}</li>" for x in b["lista"]) + "</ul>")
        elif "h" in b:
            out.append(f"<h3>{b['h']}</h3>")
        elif "h3" in b:
            out.append(f"<h4>{b['h3']}</h4>")
    return "\n".join(out)

def page_hero(title, lead="", bg="", eyebrow=""):
    lead_p = f'<p class="lead">{lead}</p>' if lead else ''
    img = f'<img class="ph-bg" src="{u(bg)}" alt="" fetchpriority="high">' if bg else ''
    eb = f'<p class="ph-eyebrow">{eyebrow}</p>' if eyebrow else ''
    return f'''<section class="page-hero{' has-img' if bg else ''}">{img}<div class="wrap">
  <nav class="crumbs" aria-label="Migas de pan"><a href="{L("home")}">Inicio</a><span aria-hidden="true">/</span><span aria-current="page">{e(title)}</span></nav>
  {eb}<h1>{e(title)}</h1>{lead_p}
</div></section>'''

def faq_html(items, cls=""):
    return f'<div class="faq {cls}">' + "".join(
        f'<details><summary><span>{e(f["q"])}</span><i>{I["plus"]}</i></summary><div class="faq-a"><p>{e(f["a"])}</p></div></details>'
        for f in items) + '</div>'

def cta_band(title="¿Hablamos de tu sonrisa?", sub="Primera visita gratuita, con plan de tratamiento y presupuesto detallado."):
    return f'''<section class="cta-band"><div class="wrap">
  <div><h2>{title}</h2><p>{sub}</p></div>
  <div class="cta-actions">
    <a class="btn btn-cita" href="{CITA}">{I["cal"]} Pide cita</a>
    <a class="btn btn-light" href="tel:{S["tel1_href"]}">{I["phone"]} {S["tel1"]}</a>
    <a class="btn btn-light" href="{WA_URL}" target="_blank" rel="noopener noreferrer">{I["wa"]} WhatsApp</a>
  </div>
</div></section>'''

def gallery(imgs, cls="gal"):
    items = "".join(f'<a href="{u(p)}" class="g-item" data-lb><img src="{u(p, 1000)}" alt="Clínica Dental Ontiveros, Marbella" loading="lazy" decoding="async"></a>' for p in imgs)
    return f'<div class="{cls}">{items}</div>'

def appt_form(idp="cita", title=None):
    c = C["contacto"]
    motivos = ["Primera visita gratuita"] + [t["titulo"] for t in C["tratamientos"]["lista"]] + ["Otro motivo"]
    opts = "".join(f"<option>{e(m)}</option>" for m in motivos)
    rgpd = f'<p class="rgpd">{e(c["rgpd"])}</p>' if c.get("rgpd") else ""
    return f'''<form class="form" id="{idp}" action="{PREFIX}contact.php" method="post" novalidate data-form>
  <h2 class="form-title">{title or c["form_title"]}</h2>
  <p class="form-sub">Te respondemos lo antes posible para confirmar día y hora.</p>
  <div class="form-msg" role="status" aria-live="polite"></div>
  <input type="hidden" name="tipo" value="cita">
  <div class="row2">
    <div class="field"><label for="{idp}-nombre">Nombre *</label><input id="{idp}-nombre" name="nombre" required maxlength="80" autocomplete="name"></div>
    <div class="field"><label for="{idp}-tel">Teléfono *</label><input id="{idp}-tel" name="telefono" type="tel" required maxlength="30" autocomplete="tel"></div>
  </div>
  <div class="field"><label for="{idp}-email">E-mail *</label><input id="{idp}-email" name="email" type="email" required maxlength="160" autocomplete="email"></div>
  <div class="field"><label for="{idp}-motivo">Motivo de la consulta *</label><select id="{idp}-motivo" name="motivo" required>{opts}</select></div>
  <div class="field"><label for="{idp}-msg">Mensaje *</label><textarea id="{idp}-msg" name="mensaje" required maxlength="5000" rows="4"></textarea></div>
  <div class="hp" aria-hidden="true"><label for="{idp}-web">No rellenar</label><input id="{idp}-web" type="text" name="website" tabindex="-1" autocomplete="off"></div>
  <label class="check"><input type="checkbox" name="acepto" value="1" required><span>{e(c["acepto"]).replace("términos y condiciones", f'<a href="{L("privacidad")}" target="_blank">términos y condiciones</a>')}</span></label>
  <div class="captcha"><label for="{idp}-cap">Comprobación: <span data-captcha-q>… + … =</span></label><input id="{idp}-cap" name="captcha" inputmode="numeric" maxlength="3" required autocomplete="off"></div>
  <input type="hidden" name="token" value="">
  <button class="btn btn-cita btn-block" type="submit">Enviar solicitud {I["arrow"]}</button>
  {rgpd}
</form>'''

def callback_form():
    return f'''<form class="form form-mini" id="te-llamamos" action="{PREFIX}contact.php" method="post" novalidate data-form>
  <div class="form-msg" role="status" aria-live="polite"></div>
  <input type="hidden" name="tipo" value="llamada">
  <div class="field"><label for="cb-nombre">Nombre</label><input id="cb-nombre" name="nombre" required maxlength="80" autocomplete="name"></div>
  <div class="field"><label for="cb-tel">Teléfono</label><input id="cb-tel" name="telefono" type="tel" required maxlength="30" autocomplete="tel"></div>
  <div class="hp" aria-hidden="true"><label for="cb-web">No rellenar</label><input id="cb-web" type="text" name="website" tabindex="-1" autocomplete="off"></div>
  <label class="check"><input type="checkbox" name="acepto" value="1" required><span>{e(C["contacto"]["acepto"]).replace("términos y condiciones", f'<a href="{L("privacidad")}" target="_blank">términos y condiciones</a>')}</span></label>
  <div class="captcha"><label for="cb-cap">Comprobación: <span data-captcha-q>… + … =</span></label><input id="cb-cap" name="captcha" inputmode="numeric" maxlength="3" required autocomplete="off"></div>
  <input type="hidden" name="token" value="">
  <button class="btn btn-cita btn-block" type="submit">Que me llamen {I["arrow"]}</button>
</form>'''

def map_box():
    q = quote(S["maps_q"])
    return f'''<div class="map" data-map="https://maps.google.com/maps?q={q}&amp;z=17&amp;output=embed">
  <div class="map-ph">
    {I["pin"]}
    <p class="map-addr">{e(S["address"])}</p>
    <p class="map-note">El mapa lo sirve Google y puede usar cookies de terceros.</p>
    <div class="map-actions">
      <button class="btn btn-primary btn-sm" type="button" data-map-load>Ver mapa</button>
      <a class="btn btn-ghost btn-sm" href="https://www.google.com/maps/search/?api=1&amp;query={q}" target="_blank" rel="noopener noreferrer">Cómo llegar</a>
    </div>
  </div>
</div>'''

# ---------- INICIO ----------
def build_home():
    H = C["home"]
    servicios = "".join(f'''<li><a href="{L("tratamientos")}#{s["ancla"]}">
  <span class="sv-name">{e(s["titulo"])}</span><span class="sv-text">{e(s["texto"])}</span><span class="sv-go">{I["arrow"]}</span></a></li>''' for s in H["servicios"])
    cifras = "".join(f'<li><strong>{c["prefijo"]}{c["valor"]}</strong><span>{e(c["texto"])}</span></li>' for c in C["quienes"]["cifras"])
    opiniones = "".join(f'<figure class="op"><span class="op-q">{I["quote"]}</span><blockquote><p>{e(o)}</p></blockquote><figcaption>Paciente de Clínica Dental Ontiveros</figcaption></figure>' for o in H["opiniones"])
    reviews = (f'<a class="btn btn-ghost" href="{S["google_reviews"]}" target="_blank" rel="noopener noreferrer">Ver opiniones en Google</a>'
               if S.get("google_reviews") else "")
    body = f'''<section class="hero">
  <div class="hero-text">
    <p class="hero-eyebrow">{e(H["hero_eyebrow"])} <span>en Marbella desde {S["fundacion"]}</span></p>
    <h1>{e(H["hero_title"])}</h1>
    <p class="hero-lead">{e(H["intro"][0])}</p>
    <div class="hero-actions">
      <a class="btn btn-cita btn-lg" href="{CITA}">{I["cal"]} Pide cita</a>
      <a class="btn btn-outline-light btn-lg" href="tel:{S["tel1_href"]}">{I["phone"]} {S["tel1"]}</a>
    </div>
    <a class="hero-wa" href="{WA_URL}" target="_blank" rel="noopener noreferrer">{I["wa"]} O escríbenos por WhatsApp</a>
  </div>
  <div class="hero-media">
    <img src="{u(H["hero_img"])}" alt="Clínica Dental Ontiveros en Marbella" fetchpriority="high">
    <svg class="hero-arc" viewBox="0 0 400 120" aria-hidden="true"><path d="M10 20 Q200 150 390 20" fill="none" stroke="currentColor" stroke-width="14" stroke-linecap="round"/></svg>
    <a class="hero-badge" href="#primera-visita"><strong>1ª visita</strong><span>gratuita</span></a>
  </div>
</section>

<section class="quick" aria-label="Contacto rápido"><div class="wrap">
  <a class="qk" href="tel:{S["tel1_href"]}"><i>{I["phone"]}</i><span><strong>Llámanos</strong>{S["tel1"]}</span></a>
  <button class="qk" type="button" data-open-callback aria-expanded="false" aria-controls="cb-panel"><i>{I["callback"]}</i><span><strong>Te llamamos</strong>Déjanos tu teléfono y nos pondremos en contacto contigo.</span></button>
  <a class="qk" href="mailto:{S["email"]}"><i>{I["mail"]}</i><span><strong>Escríbenos</strong>{S["email"]}</span></a>
  <a class="qk" href="https://www.google.com/maps/search/?api=1&amp;query={quote(S["maps_q"])}" target="_blank" rel="noopener noreferrer"><i>{I["pin"]}</i><span><strong>Visítanos</strong>{e(S["address"])}</span></a>
  <div class="cb-panel" id="cb-panel" hidden>{callback_form()}</div>
</div></section>

<section class="sec intro"><div class="wrap split">
  <div class="split-media"><img src="{u(H["intro_img"], 1200)}" alt="Equipo de Clínica Dental Ontiveros" loading="lazy"></div>
  <div class="split-text">
    <p class="kicker">{e(H["intro_eyebrow"])}</p>
    <h2>{e(H["intro_title"])}</h2>
    {"".join(f"<p>{e(p)}</p>" for p in H["intro"])}
    <ul class="stats">{cifras}</ul>
    <a class="link-more" href="{L("quienes")}">Conócenos {I["arrow"]}</a>
  </div>
</div></section>

<section class="sec services"><div class="wrap">
  <div class="sec-head"><h2>{e(H["servicios_title"])}</h2><p>{e(H["servicios_sub"])}</p></div>
  <ul class="sv-list">{servicios}</ul>
  <p class="center"><a class="btn btn-primary" href="{L("tratamientos")}">Más servicios {I["arrow"]}</a></p>
</div></section>

<section class="visit" id="primera-visita"><div class="wrap split">
  <div class="split-text">
    <h2>{e(H["visita_title"])}</h2>
    {"".join(f"<p>{e(p)}</p>" for p in H["visita"])}
    <div class="cta-actions"><a class="btn btn-cita btn-lg" href="{CITA}">{I["cal"]} Pide cita</a>
    <a class="btn btn-light btn-lg" href="{WA_URL}" target="_blank" rel="noopener noreferrer">{I["wa"]} WhatsApp</a></div>
  </div>
  <div class="split-media"><img src="{u(H["visita_img"], 1200)}" alt="Gabinete de Clínica Dental Ontiveros" loading="lazy"></div>
</div></section>

<section class="sec opinions"><div class="wrap">
  <div class="sec-head"><h2>{e(H["opiniones_title"])}</h2></div>
  <div class="op-grid">{opiniones}</div>
  <p class="center">{reviews}</p>
</div></section>

<section class="sec faq-sec"><div class="wrap narrow">
  <div class="sec-head"><h2>{e(H["faq_title"])}</h2></div>
  {faq_html(H["faq"])}
</div></section>

<section class="sec contact-home"><div class="wrap split">
  <div class="split-text">
    <h2>Contáctanos</h2>
    <p>Solicita tu cita online ahora o, si lo prefieres, te llamamos sin coste.</p>
    <ul class="c-list">
      <li>{I["phone"]}<a href="tel:{S["tel1_href"]}">+34 {S["tel1"]}</a></li>
      <li>{I["wa"]}<a href="{WA_URL}" target="_blank" rel="noopener noreferrer">+34 {S["tel2"]}</a></li>
      <li>{I["mail"]}<a href="mailto:{S["email"]}">{S["email"]}</a></li>
      <li>{I["pin"]}<span>{e(S["address"])}</span></li>
    </ul>
    {horario_html()}
    {map_box()}
  </div>
  <div>{appt_form("cita-home")}</div>
</div></section>'''
    page("home", H["seo_title"], body, H["seo_desc"], extra_ld=[faq_jsonld(H["faq"])])

# ---------- QUIÉNES SOMOS ----------
def team_cards(members):
    out = []
    for m in members:
        name = f'<h3>{e(m["nombre"])}</h3>' if m.get("nombre") else ''
        res = f'<p class="tm-res">{e(m["resumen"])}</p>' if m.get("resumen") else ''
        cv = f'<a class="link-more" href="{L("equipo")}#{m["cv"]}">Ver currículum {I["arrow"]}</a>' if m.get("cv") else ''
        alt = m.get("nombre") or m["cargo"]
        out.append(f'''<article class="tm"><div class="tm-img"><img src="{u(m["img"], 800)}" alt="{e(alt)}, {e(m["cargo"])}" loading="lazy"></div>
  <div class="tm-body">{name}<p class="tm-role">{e(m["cargo"])}</p>{res}{cv}</div></article>''')
    return "".join(out)

def build_quienes():
    Q = C["quienes"]
    cifras = "".join(f'<li><strong>{c["prefijo"]}{c["valor"]}</strong><span>{e(c["texto"])}</span></li>' for c in Q["cifras"])
    valores = "".join(f'<li><i>{I[v["icono"]]}</i><h3>{e(v["titulo"])}</h3><p>{e(v["texto"])}</p></li>' for v in Q["valores"])
    queremos = "".join(f'<li>{I["check"]}<span>{e(q)}</span></li>' for q in Q["queremos"])
    body = f'''{page_hero("Quiénes somos", "", Q["hero_img"], Q["eyebrow"])}
<section class="sec"><div class="wrap split">
  <div class="split-text">
    <h2>{e(Q["titulo"])}</h2>
    {"".join(f"<p>{e(p)}</p>" for p in Q["texto"])}
    <ul class="stats">{cifras}</ul>
  </div>
  <div class="split-media"><img src="{u(Q["img"], 1200)}" alt="Clínica Dental Ontiveros en Marbella" loading="lazy"></div>
</div></section>

<section class="sec tint"><div class="wrap">
  <div class="sec-head"><h2>{e(Q["valores_title"])}</h2><p>{e(Q["valores_sub"])}</p></div>
  <ul class="values">{valores}</ul>
</div></section>

<section class="sec"><div class="wrap narrow">
  <div class="sec-head"><h2>{e(Q["queremos_title"])}</h2></div>
  <ul class="wants">{queremos}</ul>
</div></section>

<section class="sec tint" id="equipo"><div class="wrap">
  <div class="sec-head"><p class="kicker">{e(Q["equipo_eyebrow"])}</p><h2>{e(Q["equipo_title"])}</h2>
  {"".join(f"<p>{e(p)}</p>" for p in Q["equipo_texto"])}</div>
  <div class="team">{team_cards(Q["equipo"])}</div>
  <p class="center"><a class="btn btn-primary" href="{L("equipo")}">Ver el equipo médico {I["arrow"]}</a></p>
</div></section>

<section class="sec"><div class="wrap">
  {gallery(Q["galeria"])}
</div></section>
{cta_band(e(Q["cta_title"]), e(Q["cta_sub"]))}'''
    page("quienes", Q["seo_title"], body, Q["seo_desc"], h1="Quiénes somos", og_img=u(Q["img"]))

# ---------- EQUIPO MÉDICO ----------
def build_equipo():
    Q = C["equipo_medico"]
    idx = "".join(f'<a href="#{d["id"]}">{e(d["nombre"])}</a>' for d in Q["doctores"])
    docs = []
    for d in Q["doctores"]:
        role = f'<p class="tm-role">{e(d["cargo"])}</p>' if d.get("cargo") else ''
        docs.append(f'''<article class="doc" id="{d["id"]}">
  <div class="doc-side"><img src="{u(d["img"], 800)}" alt="{e(d["nombre"])}" loading="lazy"><h2>{e(d["nombre"])}</h2>{role}
  <a class="btn btn-cita btn-sm" href="{CITA}">Pide cita</a></div>
  <div class="doc-cv">{bloques(d["bloques"])}</div>
</article>''')
    body = f'''{page_hero(Q["titulo"], "", Q["hero_img"])}
<section class="sec"><div class="wrap">
  <nav class="chips" aria-label="Doctores">{idx}</nav>
  {"".join(docs)}
</div></section>
{cta_band()}'''
    page("equipo", Q["seo_title"], body, Q["seo_desc"], h1=Q["titulo"])

# ---------- INSTALACIONES ----------
def build_instalaciones():
    Q = C["instalaciones"]
    dest = "".join(f'<li><i>{I[d["icono"]]}</i><strong>{e(d["titulo"])}</strong><span>{e(d["texto"])}</span></li>' for d in Q["destacados"])
    body = f'''{page_hero("Instalaciones", "", Q["hero_img"], Q["eyebrow"])}
<section class="sec"><div class="wrap split split-top">
  <div class="split-text">
    <h2>{e(Q["titulo"])}</h2>
    {bloques(Q["bloques"])}
  </div>
  <ul class="feats">{dest}</ul>
</div></section>
<section class="sec tint"><div class="wrap">
  {gallery(Q["galeria"], "gal gal-big")}
</div></section>
{cta_band()}'''
    page("instalaciones", Q["seo_title"], body, Q["seo_desc"], h1="Instalaciones", og_img=u(Q["galeria"][0]))

# ---------- TRATAMIENTOS ----------
def build_tratamientos():
    Q = C["tratamientos"]
    chips = "".join(f'<a href="#{t["id"]}">{e(t["menu"])}</a>' for t in Q["lista"])
    secs = []
    faqs = []
    for i, t in enumerate(Q["lista"]):
        sub = f'<p class="tr-sub">{e(t["subtitulo"])}</p>' if t.get("subtitulo") else ''
        gal = gallery(t["galeria"], "gal gal-mini") if t.get("galeria") else ''
        fq = faq_html(t["faq"]) if t.get("faq") else ''
        faqs += t.get("faq", [])
        secs.append(f'''<article class="tr{' tr-rev' if i % 2 else ''}" id="{t["id"]}">
  <div class="tr-media"><img src="{u(t["img"], 1000)}" alt="{e(t["titulo"])} en Marbella, Clínica Dental Ontiveros" loading="lazy">{gal}</div>
  <div class="tr-text">
    <h2>{e(t["titulo"])}</h2>{sub}
    {bloques(t["bloques"])}
    {fq}
    <a class="btn btn-cita" href="{CITA}" data-motivo="{e(t["titulo"])}">Pide cita para {e(t["menu"].lower() if t["menu"] != "ATM" else "ATM")}</a>
  </div>
</article>''')
    body = f'''{page_hero(Q["titulo"], e(Q["intro"]), Q["hero_img"], Q["eyebrow"])}
<div class="chips-bar"><div class="wrap">
  <button class="tr-pick" type="button" aria-expanded="false" aria-controls="tr-menu"><span class="tr-pick-l">Tratamiento</span><span class="tr-pick-v" data-tr-current>Elige uno de los {len(Q["lista"])}</span><i>{I["plus"]}</i></button>
  <nav class="chips" id="tr-menu" aria-label="Tratamientos">{chips}</nav>
</div></div>
<section class="sec trs"><div class="wrap">
{"".join(secs)}
</div></section>
{cta_band()}'''
    page("tratamientos", Q["seo_title"], body, Q["seo_desc"], h1="Tratamientos", extra_ld=[faq_jsonld(faqs)] if faqs else None)

# ---------- CONTACTO ----------
def build_contacto():
    Q = C["contacto"]
    hor = horario_html()
    hor_card = f'<div class="ci"><i>{I["clock"]}</i><div><p class="ci-h">Horario</p>{hor}</div></div>' if hor else ''
    body = f'''{page_hero(Q["titulo"], "Pide tu cita online, llámanos o escríbenos por WhatsApp.", Q["hero_img"])}
<section class="sec"><div class="wrap contact-grid">
  <div class="contact-info">
    <a class="ci" href="tel:{S["tel1_href"]}"><i>{I["phone"]}</i><div><p class="ci-h">Llámanos</p><p>+34 {S["tel1"]}</p></div></a>
    <a class="ci" href="tel:{S["tel2_href"]}"><i>{I["phone"]}</i><div><p class="ci-h">Móvil</p><p>+34 {S["tel2"]}</p></div></a>
    <a class="ci" href="{WA_URL}" target="_blank" rel="noopener noreferrer"><i>{I["wa"]}</i><div><p class="ci-h">WhatsApp</p><p>Escríbenos y te respondemos</p></div></a>
    <a class="ci" href="mailto:{S["email"]}"><i>{I["mail"]}</i><div><p class="ci-h">Escríbenos</p><p>{S["email"]}</p></div></a>
    <div class="ci"><i>{I["pin"]}</i><div><p class="ci-h">Visítanos</p><p>{e(S["address"])}</p></div></div>
    {hor_card}
  </div>
  {appt_form("cita")}
</div>
<div class="wrap">{map_box()}</div></section>'''
    page("contacto", Q["seo_title"], body, Q["seo_desc"], h1="Contacto")

# ---------- LEGALES ----------
def build_legal():
    for key, title, src in LEGAL:
        content = (SRC / "legal" / src).read_text(encoding="utf-8")
        body = f'''{page_hero(title)}
<section class="sec"><div class="wrap narrow"><article class="legal">
{content}
</article></div></section>'''
        page(key, f"{title} | {S['name']}", body, f"{title} del sitio web de {S['name']} (Marbella).", h1=title)

# ---------- 404 ----------
def build_404():
    body = f'''{page_hero("Página no encontrada")}
<section class="sec"><div class="wrap narrow center">
  <p>La página que busca no existe o ha cambiado de dirección.</p>
  <p class="cta-actions center-actions"><a class="btn btn-primary" href="{L("home")}">Ir al inicio</a> <a class="btn btn-ghost" href="{L("tratamientos")}">Ver tratamientos</a> <a class="btn btn-cita" href="{CITA}">Pide cita</a></p>
</div></section>'''
    page("404", f"Página no encontrada | {S['name']}", body, "La página solicitada no existe.", h1="Página no encontrada")

# ---------- SEO / servidor ----------
def build_sitemap():
    prio = {"home": "1.0", "tratamientos": "0.9", "contacto": "0.8", "quienes": "0.7", "equipo": "0.6", "instalaciones": "0.6"}
    urls = "".join(f"<url><loc>{ABS(k)}</loc><lastmod>{TODAY}</lastmod><priority>{prio.get(k, '0.3')}</priority></url>" for k in PAGES)
    (DIST / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")
    robots = ("User-agent: *\nDisallow: /\n" if NOINDEX else
              "User-agent: *\nAllow: /\nDisallow: /contact.php\n") + f"\nSitemap: {URL_PUB}sitemap.xml\n"
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")

def build_htaccess():
    csp = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
           f"img-src 'self' data: {RES}; font-src 'self'; connect-src 'self'; "
           "frame-src https://maps.google.com https://www.google.com; form-action 'self'; "
           "base-uri 'self'; object-src 'none'; frame-ancestors 'self'; upgrade-insecure-requests")
    root_rules = ""
    if PREFIX == "/":
        host = _u.netloc.replace(".", "\\.")
        redirects = "\n".join(f"RewriteRule ^{re.escape(old)}?$ {L(k)} [R=301,L]" for old, k in OLD_WP.items())
        root_rules = f'''
# Forzar HTTPS y dominio sin www
RewriteCond %{{HTTPS}} !=on [OR]
RewriteCond %{{HTTP_HOST}} !^{host}$ [NC]
RewriteRule ^ https://{_u.netloc}%{{REQUEST_URI}} [R=301,L]

# Antigua web de pruebas /web/ -> raíz
RewriteRule ^web(?:/(.*))?$ /$1 [R=301,L]

# Páginas de WordPress que ya no existen
{redirects}
RewriteRule ^(wp-login\\.php|xmlrpc\\.php|wp-admin|wp-includes|wp-json|feed|comments/feed|author/) - [G,L]
RewriteRule ^wp-content/(?!uploads/) - [G,L]
# Copia del WordPress antiguo: no accesible desde fuera
RewriteRule ^(wp[-_]old|web[-_]old|old[-_]wp)(/|$) - [F,L]
'''
    xrobots = '\n  Header always set X-Robots-Tag "noindex, nofollow"' if NOINDEX else ""
    ht = f'''# Clínica Dental Ontiveros — generado por build.py (no editar a mano)
Options -Indexes -MultiViews
DirectoryIndex index.html
ErrorDocument 404 {PREFIX}404.html
AddDefaultCharset UTF-8
AddType image/webp .webp
AddType font/woff2 .woff2

<IfModule mod_rewrite.c>
RewriteEngine On{root_rules}
</IfModule>

# Archivos internos: nunca accesibles desde fuera
<FilesMatch "(^\\.|\\.(md|py|json|yml|yaml|log|bak|old|orig|sql|sh|ini|zip|tar|gz|lock)$)">
  <IfModule mod_authz_core.c>
    Require all denied
  </IfModule>
  <IfModule !mod_authz_core.c>
    Order allow,deny
    Deny from all
  </IfModule>
</FilesMatch>

<IfModule mod_headers.c>
  Header always set X-Content-Type-Options "nosniff"
  Header always set X-Frame-Options "SAMEORIGIN"
  Header always set Referrer-Policy "strict-origin-when-cross-origin"
  Header always set Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()"
  Header always set Cross-Origin-Opener-Policy "same-origin"
  Header always set Strict-Transport-Security "max-age=31536000"
  Header always set Content-Security-Policy "{csp}"{xrobots}
  Header always unset X-Powered-By
  Header unset X-Powered-By
  <FilesMatch "\\.(html)$">
    Header set Cache-Control "no-cache"
  </FilesMatch>
  <FilesMatch "\\.(css|js|webp|jpg|jpeg|png|svg|woff2|ico)$">
    Header set Cache-Control "public, max-age=31536000, immutable"
  </FilesMatch>
</IfModule>

<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css application/javascript text/javascript application/json image/svg+xml application/xml text/xml text/plain
</IfModule>
'''
    (DIST / ".htaccess").write_text(ht, encoding="utf-8")
    # En carpetas de recursos nunca se ejecuta PHP ni nada que no sea estático
    deny_php = '''<FilesMatch "\\.(php|phtml|phar|php\\d|pl|py|cgi|sh|asp|aspx|jsp)$">
  <IfModule mod_authz_core.c>
    Require all denied
  </IfModule>
  <IfModule !mod_authz_core.c>
    Order allow,deny
    Deny from all
  </IfModule>
</FilesMatch>
'''
    for d in ("img", "assets"):
        (DIST / d).mkdir(parents=True, exist_ok=True)
        (DIST / d / ".htaccess").write_text(deny_php, encoding="utf-8")

def build_assets():
    (DIST / "assets/fonts").mkdir(parents=True)
    for f in (SRC / "fonts").glob("*.woff2"):
        shutil.copy(f, DIST / "assets/fonts" / f.name)
    faces = []
    for fam, file, w, st in [("Inter", "inter-latin-400-normal", 400, "normal"), ("Inter", "inter-latin-500-normal", 500, "normal"),
                             ("Inter", "inter-latin-600-normal", 600, "normal"),
                             ("Fraunces", "fraunces-latin-500-normal", 500, "normal"),
                             ("Fraunces", "fraunces-latin-600-normal", 600, "normal"),
                             ("Fraunces", "fraunces-latin-400-italic", 400, "italic")]:
        faces.append(f"@font-face{{font-family:'{fam}';font-style:{st};font-weight:{w};font-display:swap;"
                     f"src:url(fonts/{file}.woff2) format('woff2')}}")
    css = "\n".join(faces) + "\n" + (SRC / "styles.css").read_text(encoding="utf-8")
    (DIST / "assets/styles.css").write_text(css, encoding="utf-8")
    shutil.copy(SRC / "main.js", DIST / "assets/main.js")
    # Datos SMTP desde variables de entorno (secretos de GitHub); nunca se guardan en el repositorio
    php = (SRC / "contact.php").read_text(encoding="utf-8")
    esc = lambda v: v.replace("\\", "\\\\").replace("'", "\\'")
    for k, default in (("SMTP_HOST", "mail.clinicadentalontiveros.es"), ("SMTP_PORT", "465"), ("SMTP_USER", ""), ("SMTP_PASS", "")):
        v = os.environ.get(k, "").strip() or default
        php = php.replace(f"__{k}__", esc(v)) if v else php
    (DIST / "contact.php").write_text(php, encoding="utf-8")

def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    build_assets()
    for fn in (build_home, build_quienes, build_equipo, build_instalaciones, build_tratamientos,
               build_contacto, build_legal, build_404):
        fn()
    build_sitemap()
    build_htaccess()
    faltan = sum(1 for p in DIST.rglob("*.html") for _ in re.finditer(re.escape(RES) + WP, p.read_text(encoding="utf-8")))
    n = sum(1 for p in DIST.rglob("*") if p.is_file())
    print(f"OK -> {DIST} ({n} archivos, prefijo {PREFIX})" + (f" · aviso: {faltan} referencias a imágenes aún sin copiar en src/img/ (las descarga fetch_images.py)" if faltan else ""))

if __name__ == "__main__":
    main()
