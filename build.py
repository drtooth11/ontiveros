#!/usr/bin/env python3
"""Genera la web estática de Clínica Dental Ontiveros (español + inglés).

Uso:  python3 build.py           -> genera ./dist

Contenido:
  src/content.json      contenido en español y ajustes generales
  src/content.en.json   textos en inglés. Se superpone al español: lo que no aparece (imágenes,
                        enlaces, ids) se toma de content.json. Las listas se emparejan por posición.
  src/legal/*.html      textos legales en español; src/legal/en/*.html en inglés.

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
LANGS = ("es", "en")

def merge(a, b):
    """Superpone la traducción (b) sobre el contenido base (a)."""
    if isinstance(a, dict) and isinstance(b, dict):
        r = dict(a)
        for k, v in b.items():
            r[k] = merge(a[k], v) if k in a else v
        return r
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [merge(x, y) for x, y in zip(a, b)]
    return b

BASE = json.loads((SRC / "content.json").read_text(encoding="utf-8"))
CONTENT = {"es": BASE, "en": merge(BASE, json.loads((SRC / "content.en.json").read_text(encoding="utf-8")))}

URL_PUB = BASE["url_publica"].rstrip("/") + "/"
_u = urlparse(URL_PUB)
ORIGIN = f"{_u.scheme}://{_u.netloc}"
PREFIX = _u.path if _u.path.endswith("/") else _u.path + "/"     # "/web/" o "/"
RES = BASE["recursos"].rstrip("/")
NOINDEX = bool(BASE.get("noindex"))
HOY = datetime.datetime.now(ZoneInfo("Europe/Madrid")).date()
TODAY = HOY.isoformat()

# Páginas: en español, mismas URLs que la web WordPress para conservar el posicionamiento
PAGES = {
    "es": {"home": "", "quienes": "quienes-somos/", "equipo": "equipo-medico/", "instalaciones": "instalaciones/",
           "tratamientos": "tratamientos/", "contacto": "contacto/", "aviso": "aviso-legal/",
           "privacidad": "politica-de-privacidad/", "cookies": "politica-de-cookies/"},
    "en": {"home": "en/", "quienes": "en/about-us/", "equipo": "en/medical-team/", "instalaciones": "en/facilities/",
           "tratamientos": "en/treatments/", "contacto": "en/contact/", "aviso": "en/legal-notice/",
           "privacidad": "en/privacy-policy/", "cookies": "en/cookie-policy/"},
}
# URLs de WordPress que no se migran -> redirección 301 (solo en la raíz)
OLD_WP = {"hello-world/": "home", "category/uncategorized/": "home", "home/": "home"}

# Textos de la interfaz en cada idioma
UI = {
 "es": {
  "skip": "Saltar al contenido", "home_aria": "inicio", "menu": "Abrir menú", "nav_aria": "Principal",
  "nav": {"home": "Inicio", "quienes": "Quiénes somos", "instalaciones": "Instalaciones", "tratamientos": "Tratamientos", "contacto": "Contacto"},
  "cita": "Pide cita", "lang_name": "Español", "lang_switch": "Ver en español",
  "foot_desc": "Clínica dental en Marbella desde {y}.", "foot_contact": "Contacto", "foot_where": "Dónde estamos",
  "foot_clinic": "La clínica", "foot_aria": "Pie", "equipo_link": "Equipo médico",
  "legal": {"aviso": "Aviso legal", "privacidad": "Política de privacidad", "cookies": "Política de cookies"},
  "quick_aria": "Contacto rápido", "call": "Llamar", "wa_aria": "Escribir por WhatsApp",
  "crumbs_aria": "Migas de pan", "crumb_home": "Inicio",
  "cta_title": "¿Hablamos de tu sonrisa?", "cta_sub": "Primera visita gratuita, con plan de tratamiento y presupuesto detallado.",
  "img_alt": "Clínica Dental Ontiveros, Marbella",
  "motivo_first": "Primera visita gratuita", "motivo_other": "Otro motivo",
  "form_sub": "Te respondemos lo antes posible para confirmar día y hora.",
  "f_name": "Nombre", "f_tel": "Teléfono", "f_email": "E-mail", "f_motivo": "Motivo de la consulta", "f_msg": "Mensaje",
  "f_hp": "No rellenar", "f_check": "Comprobación:", "f_send": "Enviar solicitud", "f_callme": "Que me llamen",
  "terms": "términos y condiciones",
  "map_title": "Mapa: Clínica Dental Ontiveros en Marbella", "map_route": "Cómo llegar", "map_ficha": "Ver en Google Maps",
  "since": "en Marbella desde", "hero_wa": "O escríbenos por WhatsApp", "hero_alt": "Clínica Dental Ontiveros en Marbella",
  "badge1": "1ª visita", "badge2": "gratuita",
  "q_call": "Llámanos", "q_cb": "Te llamamos", "q_cb_txt": "Déjanos tu teléfono y nos pondremos en contacto contigo.",
  "q_mail": "Escríbenos", "q_visit": "Visítanos",
  "intro_alt": "Equipo de Clínica Dental Ontiveros", "conocenos": "Conócenos", "mas_servicios": "Más servicios",
  "visita_alt": "Gabinete de Clínica Dental Ontiveros", "op_cap": "Paciente de Clínica Dental Ontiveros",
  "op_google": "Ver opiniones en Google",
  "c_title": "Contáctanos", "c_txt": "Solicita tu cita online ahora o, si lo prefieres, te llamamos sin coste.",
  "quienes_h1": "Quiénes somos", "cv": "Ver currículum", "ver_equipo": "Ver el equipo médico", "clinic_alt": "Clínica Dental Ontiveros en Marbella",
  "doctores_aria": "Doctores", "inst_h1": "Instalaciones",
  "tr_h1": "Tratamientos", "tr_pick": "Tratamiento", "tr_choose": "Elige uno de los {n}", "tr_aria": "Tratamientos",
  "tr_alt": "{t} en Marbella, Clínica Dental Ontiveros", "tr_btn": "Pide cita para {t}",
  "ct_lead": "Pide tu cita online, llámanos o escríbenos por WhatsApp.", "ct_call": "Llámanos", "ct_mobile": "Móvil",
  "ct_wa_txt": "Escríbenos y te respondemos", "ct_mail": "Escríbenos", "ct_visit": "Visítanos", "ct_hours": "Horario",
  "legal_desc": "{t} del sitio web de {n} (Marbella).",
  "cookie_cfg": "Configurar cookies", "cookie_decl": "Cookies que utiliza esta web",
  "map_consent": "Para ver el mapa de Google hay que aceptar sus cookies.", "map_show": "Mostrar mapa",
 },
 "en": {
  "skip": "Skip to content", "home_aria": "home", "menu": "Open menu", "nav_aria": "Main",
  "nav": {"home": "Home", "quienes": "About us", "instalaciones": "Facilities", "tratamientos": "Treatments", "contacto": "Contact"},
  "cita": "Book an appointment", "lang_name": "English", "lang_switch": "View in English",
  "foot_desc": "Dental clinic in Marbella since {y}.", "foot_contact": "Contact", "foot_where": "Find us",
  "foot_clinic": "The clinic", "foot_aria": "Footer", "equipo_link": "Medical team",
  "legal": {"aviso": "Legal notice", "privacidad": "Privacy policy", "cookies": "Cookie policy"},
  "quick_aria": "Quick contact", "call": "Call", "wa_aria": "Message us on WhatsApp",
  "crumbs_aria": "Breadcrumb", "crumb_home": "Home",
  "cta_title": "Shall we talk about your smile?", "cta_sub": "Free first visit, with a treatment plan and a detailed quote.",
  "img_alt": "Clínica Dental Ontiveros, Marbella",
  "motivo_first": "Free first visit", "motivo_other": "Other",
  "form_sub": "We will get back to you as soon as possible to confirm the day and time.",
  "f_name": "Name", "f_tel": "Phone", "f_email": "Email", "f_motivo": "Reason for your visit", "f_msg": "Message",
  "f_hp": "Leave empty", "f_check": "Check:", "f_send": "Send request", "f_callme": "Call me back",
  "terms": "terms and conditions",
  "map_title": "Map: Clínica Dental Ontiveros in Marbella", "map_route": "Get directions", "map_ficha": "View on Google Maps",
  "since": "in Marbella since", "hero_wa": "Or message us on WhatsApp", "hero_alt": "Clínica Dental Ontiveros in Marbella",
  "badge1": "1st visit", "badge2": "free",
  "q_call": "Call us", "q_cb": "We call you", "q_cb_txt": "Leave us your phone number and we will get in touch with you.",
  "q_mail": "Email us", "q_visit": "Visit us",
  "intro_alt": "The Clínica Dental Ontiveros team", "conocenos": "About us", "mas_servicios": "More treatments",
  "visita_alt": "Treatment room at Clínica Dental Ontiveros", "op_cap": "Patient of Clínica Dental Ontiveros",
  "op_google": "Read our Google reviews",
  "c_title": "Contact us", "c_txt": "Book your appointment online now or, if you prefer, we will call you free of charge.",
  "quienes_h1": "About us", "cv": "View CV", "ver_equipo": "Meet the medical team", "clinic_alt": "Clínica Dental Ontiveros in Marbella",
  "doctores_aria": "Dentists", "inst_h1": "Facilities",
  "tr_h1": "Treatments", "tr_pick": "Treatment", "tr_choose": "Choose one of {n}", "tr_aria": "Treatments",
  "tr_alt": "{t} in Marbella, Clínica Dental Ontiveros", "tr_btn": "Book an appointment: {t}",
  "ct_lead": "Book online, call us or message us on WhatsApp.", "ct_call": "Call us", "ct_mobile": "Mobile",
  "ct_wa_txt": "Message us and we will reply", "ct_mail": "Email us", "ct_visit": "Visit us", "ct_hours": "Opening hours",
  "legal_desc": "{t} of the {n} website (Marbella).",
  "cookie_cfg": "Cookie settings", "cookie_decl": "Cookies used on this website",
  "map_consent": "To view the Google map you need to accept its cookies.", "map_show": "Show map",
 },
}

# Estado del idioma que se está generando (lo fija set_lang)
LANG = "es"
C = BASE
S = BASE["site"]
T = UI["es"]

def set_lang(lang):
    global LANG, C, S, T, WA_URL, CITA
    LANG, C, T = lang, CONTENT[lang], UI[lang]
    S = C["site"]
    WA_URL = S["whatsapp"] + "?text=" + quote(S.get("whatsapp_texto", ""))
    CITA = L("contacto") + "#cita"

def L(key, lang=None):  # enlace interno
    return PREFIX + PAGES[lang or LANG][key]
def ABS(key, lang=None):  # URL absoluta (canonical, sitemap)
    return ORIGIN + L(key, lang)

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

# ---------- Iconos ----------
def _svg(d, sw="1.8"):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d}</svg>')
I = {
 "phone": _svg('<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>'),
 "callback": _svg('<path d="M15 3h6v6M21 3l-7 7"/><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>'),
 "mail": _svg('<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>'),
 "pin": _svg('<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>'),
 "route": _svg('<path d="m3 11 19-9-9 19-2-8-8-2z"/>'),
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
 "quote": '<svg viewBox="0 0 32 32" fill="currentColor" aria-hidden="true"><path d="M13 8C7.5 9.6 4 13.8 4 19.5 4 23 6.3 25 9 25c2.6 0 4.6-2 4.6-4.6 0-2.5-1.8-4.3-4.1-4.5.6-2.8 2.6-4.9 5.2-5.8zm14 0c-5.5 1.6-9 5.8-9 11.5 0 3.5 2.3 5.5 5 5.5 2.6 0 4.6-2 4.6-4.6 0-2.5-1.8-4.3-4.1-4.5.6-2.8 2.6-4.9 5.2-5.8z"/></svg>',
 "wa": '<svg viewBox="0 0 32 32" fill="currentColor" aria-hidden="true"><path d="M16 3a13 13 0 0 0-11.2 19.6L3 29l6.6-1.7A13 13 0 1 0 16 3zm0 23.7a10.7 10.7 0 0 1-5.5-1.5l-.4-.2-3.9 1 1-3.8-.2-.4A10.7 10.7 0 1 1 16 26.7zm5.9-8c-.3-.2-1.9-1-2.2-1s-.5-.2-.7.2-.8 1-1 1.2-.4.2-.7 0a8.8 8.8 0 0 1-4.4-3.8c-.3-.6.3-.5.9-1.6.1-.2 0-.4 0-.5l-1-2.4c-.3-.6-.5-.5-.7-.5h-.6a1.2 1.2 0 0 0-.9.4 3.6 3.6 0 0 0-1.1 2.7 6.3 6.3 0 0 0 1.3 3.3 14.4 14.4 0 0 0 5.5 4.9c2 .9 2.8 1 3.9.8a3.3 3.3 0 0 0 2.1-1.5 2.7 2.7 0 0 0 .2-1.5c-.1-.1-.3-.2-.6-.4z"/></svg>',
}

# Google Maps: ficha de la clínica (place_id) y mapa incrustado buscando por su nombre en Google
_MQ = quote(BASE["site"]["maps_nombre"])
_PID = BASE["site"]["maps_place_id"]
MAPS_FICHA = f"https://www.google.com/maps/search/?api=1&amp;query={_MQ}&amp;query_place_id={_PID}"
MAPS_RUTA = f"https://www.google.com/maps/dir/?api=1&amp;destination={_MQ}&amp;destination_place_id={_PID}"
def maps_embed():
    s = BASE["site"]
    return f"https://maps.google.com/maps?q={_MQ}&amp;ll={s['lat']},{s['lng']}&amp;z=17&amp;hl={LANG}&amp;output=embed"

NAV = ["home", "quienes", "instalaciones", "tratamientos", "contacto"]
LEGAL = [("aviso", "aviso-legal.html"), ("privacidad", "politica-de-privacidad.html"), ("cookies", "politica-de-cookies.html")]

def nav_html(active):
    out = []
    for key in NAV:
        cur = ' aria-current="page"' if key == active or (active == "equipo" and key == "quienes") else ''
        out.append(f'<a href="{L(key)}"{cur}>{T["nav"][key]}</a>')
    return "\n".join(out)

def lang_switch(key):
    other = "en" if LANG == "es" else "es"
    target = key if key in PAGES[other] else "home"
    return (f'<a class="lang-sw" href="{L(target, other)}" hreflang="{other}" lang="{other}" '
            f'title="{UI[other]["lang_switch"]}">{other.upper()}</a>')

def cookiebot_tag():
    cb = BASE["site"].get("cookiebot_id")
    if not cb:
        return ""
    return (f'<script id="Cookiebot" src="https://consent.cookiebot.com/uc.js" data-cbid="{cb}" '
            f'data-blockingmode="auto" data-culture="{LANG.upper()}" type="text/javascript"></script>\n')

def clinic_jsonld():
    d = {
        "@context": "https://schema.org",
        "@type": "Dentist",
        "@id": ORIGIN + PREFIX + "#clinica",
        "name": S["name"],
        "url": ABS("home"),
        "logo": absu(u(S["logo"])),
        "image": absu(u(C["home"]["hero_img"])),
        "telephone": S["tel1_href"],
        "email": S["email"],
        "foundingDate": S.get("fundacion", ""),
        "address": {"@type": "PostalAddress", "streetAddress": S["calle"], "postalCode": S["cp"],
                    "addressLocality": S["ciudad"], "addressRegion": S["provincia"], "addressCountry": "ES"},
        "geo": {"@type": "GeoCoordinates", "latitude": S["lat"], "longitude": S["lng"]},
        "hasMap": MAPS_FICHA.replace("&amp;", "&"),
        "areaServed": {"@type": "City", "name": "Marbella"},
        "medicalSpecialty": "Dentistry",
        "knowsLanguage": ["es", "en"],
        "availableService": [{"@type": "MedicalProcedure", "name": t["titulo"]} for t in C["tratamientos"]["lista"]],
        "contactPoint": [{"@type": "ContactPoint", "telephone": S["tel1_href"], "contactType": "customer service",
                          "availableLanguage": ["Spanish", "English"]}],
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

def out_path(key):
    return DIST / PAGES[LANG][key] / "index.html" if key in PAGES[LANG] else DIST / "404.html"

def page(key, title, body, desc, h1=None, og_img=None, extra_ld=None):
    v_css, v_js = vhash(DIST / "assets/styles.css"), vhash(DIST / "assets/main.js")
    is_page = key in PAGES[LANG]
    canonical = ABS(key) if is_page else ""
    og_img = absu(og_img or u(C["home"]["hero_img"]))
    ld = []
    if key == "home":
        ld = [clinic_jsonld(), {"@context": "https://schema.org", "@type": "WebSite", "name": S["name"], "url": ABS("home"),
                                "inLanguage": "es-ES" if LANG == "es" else "en", "publisher": {"@id": ORIGIN + PREFIX + "#clinica"}}]
    elif is_page:
        ld.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": T["crumb_home"], "item": ABS("home")},
            {"@type": "ListItem", "position": 2, "name": h1 or title, "item": canonical}]})
    ld += extra_ld or []
    ld_html = "\n".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    robots = "noindex, nofollow" if (NOINDEX or not is_page) else "index, follow, max-image-preview:large, max-snippet:-1"
    fav = u(S["favicon"], 192)
    head_links = ""
    if is_page:
        head_links = (f'<link rel="canonical" href="{canonical}">\n<meta property="og:url" content="{canonical}">\n'
                      + "".join(f'<link rel="alternate" hreflang="{lg}" href="{ABS(key, lg)}">\n' for lg in LANGS)
                      + f'<link rel="alternate" hreflang="x-default" href="{ABS(key, "es")}">\n')
    locale = "es_ES" if LANG == "es" else "en_GB"
    alt_locale = "en_GB" if LANG == "es" else "es_ES"
    switch = lang_switch(key)
    doc = f'''<!doctype html>
<html lang="{LANG}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{cookiebot_tag()}<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{robots}">
{head_links}<meta name="theme-color" content="#0b3a6e">
<meta property="og:type" content="website">
<meta property="og:locale" content="{locale}">
<meta property="og:locale:alternate" content="{alt_locale}">
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
<a class="skip" href="#contenido">{T["skip"]}</a>
<header class="header"><div class="wrap">
  <a class="logo" href="{L("home")}" aria-label="{e(S["name"])}, {T["home_aria"]}"><img src="{u(S["logo"])}" alt="{e(S["name"])}" width="218" height="50"></a>
  <nav class="nav" id="menu" aria-label="{T["nav_aria"]}">
{nav_html(key)}
    <a class="nav-tel" href="tel:{S["tel1_href"]}">{I["phone"]} {S["tel1"]}</a>
  </nav>
  {switch}
  <a class="btn btn-cita hdr-cita" href="{CITA}">{T["cita"]}</a>
  <button class="burger" type="button" aria-label="{T["menu"]}" aria-expanded="false" aria-controls="menu"><span></span></button>
</div></header>
<main id="contenido">
{body}
</main>
<footer class="footer">
  <div class="wrap">
    <div class="f-top">
      <div class="f-brand">
        <a class="f-logo" href="{L("home")}"><img src="{u(S["logo"])}" alt="{e(S["name"])}" loading="lazy" width="218" height="50"></a>
        <p>{T["foot_desc"].format(y=S.get("fundacion", "2001"))}</p>
      </div>
      <div>
        <p class="f-h">{T["foot_contact"]}</p>
        <p><a href="tel:{S["tel1_href"]}">+34 {S["tel1"]}</a><br><a href="tel:{S["tel2_href"]}">+34 {S["tel2"]}</a><br><a href="mailto:{S["email"]}">{S["email"]}</a></p>
      </div>
      <div>
        <p class="f-h">{T["foot_where"]}</p>
        <p>{e(S["address"])}</p>
        {horario_html("hor f-hor")}
      </div>
      <nav aria-label="{T["foot_aria"]}">
        <p class="f-h">{T["foot_clinic"]}</p>
        <ul>
          <li><a href="{L("quienes")}">{T["nav"]["quienes"]}</a></li>
          <li><a href="{L("equipo")}">{T["equipo_link"]}</a></li>
          <li><a href="{L("instalaciones")}">{T["nav"]["instalaciones"]}</a></li>
          <li><a href="{L("tratamientos")}">{T["nav"]["tratamientos"]}</a></li>
          <li><a href="{L("contacto")}">{T["nav"]["contacto"]}</a></li>
        </ul>
      </nav>
    </div>
    <div class="f-bottom">
      <span>© {TODAY[:4]} {e(S["name"])}</span>
      <ul>{"".join(f'<li><a href="{L(k)}">{T["legal"][k]}</a></li>' for k, _ in LEGAL)}<li><a href="#" data-cookie-settings>{T["cookie_cfg"]}</a></li><li><a href="{L(key if is_page else "home", "en" if LANG == "es" else "es")}" hreflang="{"en" if LANG == "es" else "es"}">{UI["en" if LANG == "es" else "es"]["lang_name"]}</a></li></ul>
    </div>
  </div>
</footer>
<nav class="mbar" aria-label="{T["quick_aria"]}">
  <a href="tel:{S["tel1_href"]}">{I["phone"]}<span>{T["call"]}</span></a>
  <a href="{WA_URL}" target="_blank" rel="noopener noreferrer">{I["wa"]}<span>WhatsApp</span></a>
  <a class="mbar-cita" href="{CITA}">{I["cal"]}<span>{T["cita"] if LANG == "es" else "Book"}</span></a>
</nav>
<a class="wa-float" href="{WA_URL}" target="_blank" rel="noopener noreferrer" aria-label="{T["wa_aria"]}">{I["wa"]}</a>
</body>
</html>
'''
    doc = add_dims(doc)
    out = out_path(key)
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
  <nav class="crumbs" aria-label="{T["crumbs_aria"]}"><a href="{L("home")}">{T["crumb_home"]}</a><span aria-hidden="true">/</span><span aria-current="page">{e(title)}</span></nav>
  {eb}<h1>{e(title)}</h1>{lead_p}
</div></section>'''

def faq_html(items, cls=""):
    return f'<div class="faq {cls}">' + "".join(
        f'<details><summary><span>{e(f["q"])}</span><i>{I["plus"]}</i></summary><div class="faq-a"><p>{e(f["a"])}</p></div></details>'
        for f in items) + '</div>'

def cta_band(title=None, sub=None):
    return f'''<section class="cta-band"><div class="wrap">
  <div><h2>{title or T["cta_title"]}</h2><p>{sub or T["cta_sub"]}</p></div>
  <div class="cta-actions">
    <a class="btn btn-cita" href="{CITA}">{I["cal"]} {T["cita"]}</a>
    <a class="btn btn-light" href="tel:{S["tel1_href"]}">{I["phone"]} {S["tel1"]}</a>
    <a class="btn btn-light" href="{WA_URL}" target="_blank" rel="noopener noreferrer">{I["wa"]} WhatsApp</a>
  </div>
</div></section>'''

def gallery(imgs, cls="gal"):
    items = "".join(f'<a href="{u(p)}" class="g-item" data-lb><img src="{u(p, 1000)}" alt="{T["img_alt"]}" loading="lazy" decoding="async"></a>' for p in imgs)
    return f'<div class="{cls}">{items}</div>'

def acepto_html():
    terms = T["terms"]
    return e(C["contacto"]["acepto"]).replace(terms, f'<a href="{L("privacidad")}" target="_blank">{terms}</a>')

def appt_form(idp="cita", title=None):
    c = C["contacto"]
    motivos = [T["motivo_first"]] + [t["titulo"] for t in C["tratamientos"]["lista"]] + [T["motivo_other"]]
    opts = "".join(f"<option>{e(m)}</option>" for m in motivos)
    rgpd = f'<p class="rgpd">{e(c["rgpd"])}</p>' if c.get("rgpd") else ""
    return f'''<form class="form" id="{idp}" action="{PREFIX}contact.php" method="post" novalidate data-form>
  <h2 class="form-title">{title or c["form_title"]}</h2>
  <p class="form-sub">{T["form_sub"]}</p>
  <div class="form-msg" role="status" aria-live="polite"></div>
  <input type="hidden" name="tipo" value="cita">
  <input type="hidden" name="lang" value="{LANG}">
  <div class="row2">
    <div class="field"><label for="{idp}-nombre">{T["f_name"]} *</label><input id="{idp}-nombre" name="nombre" required maxlength="80" autocomplete="name"></div>
    <div class="field"><label for="{idp}-tel">{T["f_tel"]} *</label><input id="{idp}-tel" name="telefono" type="tel" required maxlength="30" autocomplete="tel"></div>
  </div>
  <div class="field"><label for="{idp}-email">{T["f_email"]} *</label><input id="{idp}-email" name="email" type="email" required maxlength="160" autocomplete="email"></div>
  <div class="field"><label for="{idp}-motivo">{T["f_motivo"]} *</label><select id="{idp}-motivo" name="motivo" required>{opts}</select></div>
  <div class="field"><label for="{idp}-msg">{T["f_msg"]} *</label><textarea id="{idp}-msg" name="mensaje" required maxlength="5000" rows="4"></textarea></div>
  <div class="hp" aria-hidden="true"><label for="{idp}-web">{T["f_hp"]}</label><input id="{idp}-web" type="text" name="website" tabindex="-1" autocomplete="off"></div>
  <label class="check"><input type="checkbox" name="acepto" value="1" required><span>{acepto_html()}</span></label>
  <div class="captcha"><label for="{idp}-cap">{T["f_check"]} <span data-captcha-q>… + … =</span></label><input id="{idp}-cap" name="captcha" inputmode="numeric" maxlength="3" required autocomplete="off"></div>
  <input type="hidden" name="token" value="">
  <button class="btn btn-cita btn-block" type="submit">{T["f_send"]} {I["arrow"]}</button>
  {rgpd}
</form>'''

def callback_form():
    return f'''<form class="form form-mini" id="te-llamamos" action="{PREFIX}contact.php" method="post" novalidate data-form>
  <div class="form-msg" role="status" aria-live="polite"></div>
  <input type="hidden" name="tipo" value="llamada">
  <input type="hidden" name="lang" value="{LANG}">
  <div class="field"><label for="cb-nombre">{T["f_name"]}</label><input id="cb-nombre" name="nombre" required maxlength="80" autocomplete="name"></div>
  <div class="field"><label for="cb-tel">{T["f_tel"]}</label><input id="cb-tel" name="telefono" type="tel" required maxlength="30" autocomplete="tel"></div>
  <div class="hp" aria-hidden="true"><label for="cb-web">{T["f_hp"]}</label><input id="cb-web" type="text" name="website" tabindex="-1" autocomplete="off"></div>
  <label class="check"><input type="checkbox" name="acepto" value="1" required><span>{acepto_html()}</span></label>
  <div class="captcha"><label for="cb-cap">{T["f_check"]} <span data-captcha-q>… + … =</span></label><input id="cb-cap" name="captcha" inputmode="numeric" maxlength="3" required autocomplete="off"></div>
  <input type="hidden" name="token" value="">
  <button class="btn btn-cita btn-block" type="submit">{T["f_callme"]} {I["arrow"]}</button>
</form>'''

def map_box():
    """Mapa de Google siempre visible, con los botones de ruta y ficha debajo."""
    return f'''<div class="map">
  <div class="map-frame">
    <iframe data-src="{maps_embed()}" data-cookieconsent="marketing" title="{T["map_title"]}" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen hidden></iframe>
    <div class="map-ph" data-map-ph>{I["pin"]}<p>{T["map_consent"]}</p><button class="btn btn-primary btn-sm" type="button" data-map-consent>{T["map_show"]}</button></div>
  </div>
  <div class="map-bar">
    <p class="map-addr">{I["pin"]}<span>{e(S["address"])}</span></p>
    <div class="map-actions">
      <a class="btn btn-primary btn-sm" href="{MAPS_RUTA}" target="_blank" rel="noopener noreferrer">{I["route"]} {T["map_route"]}</a>
      <a class="btn btn-ghost btn-sm" href="{MAPS_FICHA}" target="_blank" rel="noopener noreferrer">{I["pin"]} {T["map_ficha"]}</a>
    </div>
  </div>
</div>'''

# ---------- INICIO ----------
def build_home():
    H = C["home"]
    servicios = "".join(f'''<li><a href="{L("tratamientos")}#{s["ancla"]}">
  <span class="sv-name">{e(s["titulo"])}</span><span class="sv-text">{e(s["texto"])}</span><span class="sv-go">{I["arrow"]}</span></a></li>''' for s in H["servicios"])
    cifras = "".join(f'<li><strong>{c["prefijo"]}{c["valor"]}</strong><span>{e(c["texto"])}</span></li>' for c in C["quienes"]["cifras"])
    opiniones = "".join(f'<figure class="op"><span class="op-q">{I["quote"]}</span><blockquote><p>{e(o)}</p></blockquote><figcaption>{T["op_cap"]}</figcaption></figure>' for o in H["opiniones"])
    reviews = (f'<a class="btn btn-ghost" href="{S["google_reviews"]}" target="_blank" rel="noopener noreferrer">{T["op_google"]}</a>'
               if S.get("google_reviews") else "")
    body = f'''<section class="hero">
  <div class="hero-text">
    <p class="hero-eyebrow">{e(H["hero_eyebrow"])} <span>{T["since"]} {S["fundacion"]}</span></p>
    <h1>{e(H["hero_title"])}</h1>
    <p class="hero-lead">{e(H["intro"][0])}</p>
    <div class="hero-actions">
      <a class="btn btn-cita btn-lg" href="{CITA}">{I["cal"]} {T["cita"]}</a>
      <a class="btn btn-outline-light btn-lg" href="tel:{S["tel1_href"]}">{I["phone"]} {S["tel1"]}</a>
    </div>
    <a class="hero-wa" href="{WA_URL}" target="_blank" rel="noopener noreferrer">{I["wa"]} {T["hero_wa"]}</a>
  </div>
  <div class="hero-media">
    <img src="{u(H["hero_img"])}" alt="{T["hero_alt"]}" fetchpriority="high">
    <svg class="hero-arc" viewBox="0 0 400 120" aria-hidden="true"><path d="M10 20 Q200 150 390 20" fill="none" stroke="currentColor" stroke-width="14" stroke-linecap="round"/></svg>
    <a class="hero-badge" href="#primera-visita"><strong>{T["badge1"]}</strong><span>{T["badge2"]}</span></a>
  </div>
</section>

<section class="quick" aria-label="{T["quick_aria"]}"><div class="wrap">
  <a class="qk" href="tel:{S["tel1_href"]}"><i>{I["phone"]}</i><span><strong>{T["q_call"]}</strong>{S["tel1"]}</span></a>
  <button class="qk" type="button" data-open-callback aria-expanded="false" aria-controls="cb-panel"><i>{I["callback"]}</i><span><strong>{T["q_cb"]}</strong>{T["q_cb_txt"]}</span></button>
  <a class="qk" href="mailto:{S["email"]}"><i>{I["mail"]}</i><span><strong>{T["q_mail"]}</strong>{S["email"]}</span></a>
  <a class="qk" href="{MAPS_FICHA}" target="_blank" rel="noopener noreferrer"><i>{I["pin"]}</i><span><strong>{T["q_visit"]}</strong>{e(S["address"])}</span></a>
  <div class="cb-panel" id="cb-panel" hidden>{callback_form()}</div>
</div></section>

<section class="sec intro"><div class="wrap split">
  <div class="split-media"><img src="{u(H["intro_img"], 1200)}" alt="{T["intro_alt"]}" loading="lazy"></div>
  <div class="split-text">
    <p class="kicker">{e(H["intro_eyebrow"])}</p>
    <h2>{e(H["intro_title"])}</h2>
    {"".join(f"<p>{e(p)}</p>" for p in H["intro"])}
    <ul class="stats">{cifras}</ul>
    <a class="link-more" href="{L("quienes")}">{T["conocenos"]} {I["arrow"]}</a>
  </div>
</div></section>

<section class="sec services"><div class="wrap">
  <div class="sec-head"><h2>{e(H["servicios_title"])}</h2><p>{e(H["servicios_sub"])}</p></div>
  <ul class="sv-list">{servicios}</ul>
  <p class="center"><a class="btn btn-primary" href="{L("tratamientos")}">{T["mas_servicios"]} {I["arrow"]}</a></p>
</div></section>

<section class="visit" id="primera-visita"><div class="wrap split">
  <div class="split-text">
    <h2>{e(H["visita_title"])}</h2>
    {"".join(f"<p>{e(p)}</p>" for p in H["visita"])}
    <div class="cta-actions"><a class="btn btn-cita btn-lg" href="{CITA}">{I["cal"]} {T["cita"]}</a>
    <a class="btn btn-light btn-lg" href="{WA_URL}" target="_blank" rel="noopener noreferrer">{I["wa"]} WhatsApp</a></div>
  </div>
  <div class="split-media"><img src="{u(H["visita_img"], 1200)}" alt="{T["visita_alt"]}" loading="lazy"></div>
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
    <h2>{T["c_title"]}</h2>
    <p>{T["c_txt"]}</p>
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
        cv = f'<a class="link-more" href="{L("equipo")}#{m["cv"]}">{T["cv"]} {I["arrow"]}</a>' if m.get("cv") else ''
        alt = m.get("nombre") or m["cargo"]
        out.append(f'''<article class="tm"><div class="tm-img"><img src="{u(m["img"], 800)}" alt="{e(alt)}, {e(m["cargo"])}" loading="lazy"></div>
  <div class="tm-body">{name}<p class="tm-role">{e(m["cargo"])}</p>{res}{cv}</div></article>''')
    return "".join(out)

def build_quienes():
    Q = C["quienes"]
    cifras = "".join(f'<li><strong>{c["prefijo"]}{c["valor"]}</strong><span>{e(c["texto"])}</span></li>' for c in Q["cifras"])
    valores = "".join(f'<li><i>{I[v["icono"]]}</i><h3>{e(v["titulo"])}</h3><p>{e(v["texto"])}</p></li>' for v in Q["valores"])
    queremos = "".join(f'<li>{I["check"]}<span>{e(q)}</span></li>' for q in Q["queremos"])
    body = f'''{page_hero(T["quienes_h1"], "", Q["hero_img"], Q["eyebrow"])}
<section class="sec"><div class="wrap split">
  <div class="split-text">
    <h2>{e(Q["titulo"])}</h2>
    {"".join(f"<p>{e(p)}</p>" for p in Q["texto"])}
    <ul class="stats">{cifras}</ul>
  </div>
  <div class="split-media"><img src="{u(Q["img"], 1200)}" alt="{T["clinic_alt"]}" loading="lazy"></div>
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
  <p class="center"><a class="btn btn-primary" href="{L("equipo")}">{T["ver_equipo"]} {I["arrow"]}</a></p>
</div></section>

<section class="sec"><div class="wrap">
  {gallery(Q["galeria"])}
</div></section>
{cta_band(e(Q["cta_title"]), e(Q["cta_sub"]))}'''
    page("quienes", Q["seo_title"], body, Q["seo_desc"], h1=T["quienes_h1"], og_img=u(Q["img"]))

# ---------- EQUIPO MÉDICO ----------
def build_equipo():
    Q = C["equipo_medico"]
    idx = "".join(f'<a href="#{d["id"]}">{e(d["nombre"])}</a>' for d in Q["doctores"])
    docs = []
    for d in Q["doctores"]:
        role = f'<p class="tm-role">{e(d["cargo"])}</p>' if d.get("cargo") else ''
        docs.append(f'''<article class="doc" id="{d["id"]}">
  <div class="doc-side"><img src="{u(d["img"], 800)}" alt="{e(d["nombre"])}" loading="lazy"><h2>{e(d["nombre"])}</h2>{role}
  <a class="btn btn-cita btn-sm" href="{CITA}">{T["cita"]}</a></div>
  <div class="doc-cv">{bloques(d["bloques"])}</div>
</article>''')
    body = f'''{page_hero(Q["titulo"], "", Q["hero_img"])}
<section class="sec"><div class="wrap">
  <nav class="chips" aria-label="{T["doctores_aria"]}">{idx}</nav>
  {"".join(docs)}
</div></section>
{cta_band()}'''
    page("equipo", Q["seo_title"], body, Q["seo_desc"], h1=Q["titulo"])

# ---------- INSTALACIONES ----------
def build_instalaciones():
    Q = C["instalaciones"]
    dest = "".join(f'<li><i>{I[d["icono"]]}</i><strong>{e(d["titulo"])}</strong><span>{e(d["texto"])}</span></li>' for d in Q["destacados"])
    body = f'''{page_hero(T["inst_h1"], "", Q["hero_img"], Q["eyebrow"])}
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
    page("instalaciones", Q["seo_title"], body, Q["seo_desc"], h1=T["inst_h1"], og_img=u(Q["galeria"][0]))

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
        nombre_btn = t["menu"] if t["menu"].isupper() else t["menu"].lower()
        secs.append(f'''<article class="tr{' tr-rev' if i % 2 else ''}" id="{t["id"]}">
  <div class="tr-media"><img src="{u(t["img"], 1000)}" alt="{e(T["tr_alt"].format(t=t["titulo"]))}" loading="lazy">{gal}</div>
  <div class="tr-text">
    <h2>{e(t["titulo"])}</h2>{sub}
    {bloques(t["bloques"])}
    {fq}
    <a class="btn btn-cita" href="{CITA}" data-motivo="{e(t["titulo"])}">{e(T["tr_btn"].format(t=nombre_btn))}</a>
  </div>
</article>''')
    body = f'''{page_hero(Q["titulo"], e(Q["intro"]), Q["hero_img"], Q["eyebrow"])}
<div class="chips-bar"><div class="wrap">
  <button class="tr-pick" type="button" aria-expanded="false" aria-controls="tr-menu"><span class="tr-pick-l">{T["tr_pick"]}</span><span class="tr-pick-v" data-tr-current>{T["tr_choose"].format(n=len(Q["lista"]))}</span><i>{I["plus"]}</i></button>
  <nav class="chips" id="tr-menu" aria-label="{T["tr_aria"]}">{chips}</nav>
</div></div>
<section class="sec trs"><div class="wrap">
{"".join(secs)}
</div></section>
{cta_band()}'''
    page("tratamientos", Q["seo_title"], body, Q["seo_desc"], h1=Q["titulo"], extra_ld=[faq_jsonld(faqs)] if faqs else None)

# ---------- CONTACTO ----------
def build_contacto():
    Q = C["contacto"]
    hor = horario_html()
    hor_card = f'<div class="ci"><i>{I["clock"]}</i><div><p class="ci-h">{T["ct_hours"]}</p>{hor}</div></div>' if hor else ''
    body = f'''{page_hero(Q["titulo"], T["ct_lead"], Q["hero_img"])}
<section class="sec"><div class="wrap contact-grid">
  <div class="contact-info">
    <a class="ci" href="tel:{S["tel1_href"]}"><i>{I["phone"]}</i><div><p class="ci-h">{T["ct_call"]}</p><p>+34 {S["tel1"]}</p></div></a>
    <a class="ci" href="tel:{S["tel2_href"]}"><i>{I["phone"]}</i><div><p class="ci-h">{T["ct_mobile"]}</p><p>+34 {S["tel2"]}</p></div></a>
    <a class="ci" href="{WA_URL}" target="_blank" rel="noopener noreferrer"><i>{I["wa"]}</i><div><p class="ci-h">WhatsApp</p><p>{T["ct_wa_txt"]}</p></div></a>
    <a class="ci" href="mailto:{S["email"]}"><i>{I["mail"]}</i><div><p class="ci-h">{T["ct_mail"]}</p><p>{S["email"]}</p></div></a>
    <a class="ci" href="{MAPS_FICHA}" target="_blank" rel="noopener noreferrer"><i>{I["pin"]}</i><div><p class="ci-h">{T["ct_visit"]}</p><p>{e(S["address"])}</p></div></a>
    {hor_card}
  </div>
  {appt_form("cita")}
</div>
<div class="wrap">{map_box()}</div></section>'''
    page("contacto", Q["seo_title"], body, Q["seo_desc"], h1=Q["titulo"])

# ---------- LEGALES ----------
def build_legal():
    folder = SRC / "legal" if LANG == "es" else SRC / "legal" / LANG
    for key, src in LEGAL:
        title = T["legal"][key]
        content = (folder / src).read_text(encoding="utf-8")
        cb = BASE["site"].get("cookiebot_id")
        if key == "cookies" and cb:
            content += (f'\n<h2>{T["cookie_decl"]}</h2>\n<script id="CookieDeclaration" '
                        f'src="https://consent.cookiebot.com/{cb}/cd.js" data-culture="{LANG.upper()}" type="text/javascript" async></script>\n')
        body = f'''{page_hero(title)}
<section class="sec"><div class="wrap narrow"><article class="legal">
{content}
</article></div></section>'''
        page(key, f"{title} | {S['name']}", body, T["legal_desc"].format(t=title, n=S["name"]), h1=title)

# ---------- 404 (bilingüe) ----------
def build_404():
    body = f'''{page_hero("Página no encontrada · Page not found")}
<section class="sec"><div class="wrap narrow center">
  <p>La página que busca no existe o ha cambiado de dirección.<br><span lang="en">The page you are looking for does not exist or has moved.</span></p>
  <p class="cta-actions center-actions"><a class="btn btn-primary" href="{L("home", "es")}">Ir al inicio</a> <a class="btn btn-ghost" href="{L("home", "en")}" lang="en">Go to home page</a> <a class="btn btn-cita" href="{CITA}">Pide cita</a></p>
</div></section>'''
    page("404", f"Página no encontrada | {S['name']}", body, "La página solicitada no existe.", h1="Página no encontrada")

# ---------- SEO / servidor ----------
def build_sitemap():
    prio = {"home": "1.0", "tratamientos": "0.9", "contacto": "0.8", "quienes": "0.7", "equipo": "0.6", "instalaciones": "0.6"}
    urls = []
    for lg in LANGS:
        for k in PAGES[lg]:
            alts = "".join(f'<xhtml:link rel="alternate" hreflang="{a}" href="{ABS(k, a)}"/>' for a in LANGS)
            alts += f'<xhtml:link rel="alternate" hreflang="x-default" href="{ABS(k, "es")}"/>'
            urls.append(f"<url><loc>{ABS(k, lg)}</loc><lastmod>{TODAY}</lastmod><priority>{prio.get(k, '0.3')}</priority>{alts}</url>")
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        f'xmlns:xhtml="http://www.w3.org/1999/xhtml">{"".join(urls)}</urlset>\n', encoding="utf-8")
    robots = ("User-agent: *\nDisallow: /\n" if NOINDEX else
              "User-agent: *\nAllow: /\nDisallow: /contact.php\n") + f"\nSitemap: {URL_PUB}sitemap.xml\n"
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")

def build_htaccess():
    CBD = "https://consent.cookiebot.com https://consentcdn.cookiebot.com"
    csp = (f"default-src 'self'; script-src 'self' {CBD}; style-src 'self' 'unsafe-inline'; "
           f"img-src 'self' data: {RES} https://imgsct.cookiebot.com; font-src 'self'; connect-src 'self' {CBD}; "
           "frame-src https://maps.google.com https://www.google.com https://consentcdn.cookiebot.com; form-action 'self'; "
           "base-uri 'self'; object-src 'none'; frame-ancestors 'self'; upgrade-insecure-requests")
    root_rules = ""
    if PREFIX == "/":
        host = _u.netloc.replace(".", "\\.")
        redirects = "\n".join(f"RewriteRule ^{re.escape(old)}?$ {PREFIX + PAGES['es'][k]} [R=301,L]" for old, k in OLD_WP.items())
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
    for lang in LANGS:
        set_lang(lang)
        for fn in (build_home, build_quienes, build_equipo, build_instalaciones, build_tratamientos,
                   build_contacto, build_legal):
            fn()
    set_lang("es")
    build_404()
    build_sitemap()
    build_htaccess()
    faltan = sum(1 for p in DIST.rglob("*.html") for _ in re.finditer(re.escape(RES) + WP, p.read_text(encoding="utf-8")))
    n = sum(1 for p in DIST.rglob("*") if p.is_file())
    print(f"OK -> {DIST} ({n} archivos, prefijo {PREFIX})" + (f" · aviso: {faltan} referencias a imágenes aún sin copiar en src/img/ (las descarga fetch_images.py)" if faltan else ""))

if __name__ == "__main__":
    main()
