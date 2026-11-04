# Web Clínica Dental Ontiveros — HTML estático

Mismo sistema que la web de Hispadent (`drtooth11/hispadent-web`, solo de referencia: no se toca).

## Estructura
- `src/content.json` → TODO el contenido editable (textos, servicios, equipo, tratamientos, opiniones, FAQ, contacto) y los ajustes:
  - `url_publica`: dónde vive la web. Pruebas: `https://clinicadentalontiveros.es/web/`. Producción: `https://clinicadentalontiveros.es/`.
    La publicación va a `<url_publica>/deploy.php`.
  - `noindex`: `true` mientras sea la web de pruebas.
  - `site.horario`: vacío = no se muestra. Formato: `{"dias": ["Monday",…], "abre": "09:00", "cierra": "14:00", "texto_dias": "Lunes a viernes", "texto_horas": "9:00 – 14:00"}`.
  - `site.google_reviews`: enlace a las opiniones de Google (vacío = no se muestra el botón).
- `src/legal/` → textos legales. `src/img/` → imágenes (las copia `fetch_images.py`). `src/fonts/` → Fraunces + Inter autoalojadas.
- `build.py` → genera la web en `dist/` (WebP, sitemap, robots, .htaccess, datos estructurados `Dentist`, FAQPage, 404 propia).
- `deploy.py` + `receptor/deploy.php` → publicación automática por HTTPS desde GitHub.
- `src/contact.php` → formulario de cita y "Te llamamos". Llega a `m.musso@celdas.com` (se cambia en `$DESTINO`).

## Actualizar
Editar `src/content.json` (o pedírselo a Claude), `python3 build.py`, commit y push a `main`.
GitHub copia las imágenes que falten, genera la web y publica solo lo que cambia. Hay que esperar a que el workflow quede en verde.

## Imágenes
Las rutas siguen siendo las de WordPress (`/wp-content/uploads/...`) en `content.json`. `fetch_images.py` (se ejecuta en
GitHub) las descarga a `src/img/` y las guarda en el repo; `build.py` las convierte a WebP y las sirve desde `img/`.
Si una imagen no está copiada, la web la enlaza a clinicadentalontiveros.es (build.py avisa).
**Antes de mover WordPress** comprobar que `src/img/` tiene todas (build.py no debe avisar de imágenes sin copiar).

## Secretos de GitHub (Settings → Secrets and variables → Actions)
- `DEPLOY_TOKEN`: el token (en el repo solo está su huella SHA-256, dentro del deploy.php del servidor).
- `DEPLOY_URL`: `https://clinicadentalontiveros.es/web/deploy.php` (referencia; deploy.py usa `url_publica`).
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`: buzón para enviar el formulario. Sin ellos se usa `mail()` de PHP.
Sin `DEPLOY_TOKEN` el workflow genera la web pero no publica (deja un aviso).

## Receptor (deploy.php)
- Se sube UNA vez a mano. `receptor/deploy.php` del repo lleva `__TOKEN_SHA256__`; el que se sube lleva la huella real.
- ANTES de subirlo: cPanel → Imunify360 → Malware Scanner → Ignore list → `/home/USUARIO/public_html/web/deploy.php`
  (y luego la ruta de la raíz). Si no, Imunify lo recorta y el despliegue responde vacío. Debe pesar unos 4-5 KB.
- Seguridad: token (comparación en tiempo constante), lista blanca de tipos, solo `contact.php` como PHP, no puede sobrescribirse.

## Si el despliegue falla o responde vacío
1. Espacio en disco del hosting. 2. Que Imunify no haya recortado `deploy.php` (tamaño 4-5 KB).
Desde la sesión de Claude no se llega al dominio: las comprobaciones se hacen con un workflow temporal de GitHub Actions.

## Workflows manuales
- `Comprobar enlaces e imágenes`: revisa todos los enlaces e imágenes de la web publicada (el servidor distingue mayúsculas).
- `Probar formulario`: envía un mensaje de prueba.

## URLs
Mismas URLs que WordPress: `/quienes-somos/`, `/equipo-medico/`, `/instalaciones/`, `/tratamientos/`, `/contacto/`,
`/aviso-legal/`, `/politica-de-privacidad/`, `/politica-de-cookies/`. En la raíz, `/hello-world/` y `/category/uncategorized/`
redirigen (301) a la portada.

## Pasar a la raíz (checklist)
1. `url_publica` → `https://clinicadentalontiveros.es/`, `noindex` → `false`.
2. Ignore list de Imunify para `/home/USUARIO/public_html/deploy.php`, subir `deploy.php` (con la huella) a la raíz y cambiar `DEPLOY_URL`.
3. Mover WordPress a una carpeta bloqueada (`wp_old/`, ya bloqueada por el .htaccess) conservando `wp-content/uploads/` si alguna imagen no está en `src/img/`.
4. Push → workflow verde → ejecutar `Comprobar enlaces e imágenes`.
5. Dar de alta `https://clinicadentalontiveros.es/sitemap.xml` en Google Search Console.
