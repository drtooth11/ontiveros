<?php
/**
 * Clínica Dental Ontiveros — receptor de despliegues desde GitHub (v2, reforzado).
 * Se sube UNA vez a mano a la carpeta de la web. GitHub le envía por HTTPS
 * los archivos que han cambiado (en bloques .zip) y este script los coloca aquí.
 *
 * Seguridad:
 *  - Solo con el token correcto (se guarda solo su huella SHA-256; comparación en tiempo constante).
 *  - Lista blanca de tipos de archivo: solo estáticos (html, css, js, imágenes, fuentes, xml, txt).
 *    El único PHP que puede escribir es contact.php; nunca puede sobrescribirse a sí mismo.
 *  - Sin rutas con "..", absolutas ni barras invertidas.
 *  - Tamaño máximo por envío.
 */
const TOKEN_SHA256 = '__TOKEN_SHA256__';
const MANIFEST = __DIR__ . '/.deploy-manifest.php';
const MAX_BYTES = 8 * 1024 * 1024;

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Robots-Tag: noindex, nofollow');
function out($code, $data) { http_response_code($code); echo json_encode($data); exit; }

$token = $_SERVER['HTTP_X_DEPLOY_TOKEN'] ?? '';
if ($token === '' || !hash_equals(TOKEN_SHA256, hash('sha256', $token))) { usleep(400000); out(403, ['ok' => false, 'error' => 'token']); }

function permitido($name) {
    if ($name === '' || strlen($name) > 200) return false;
    if (strpos($name, '..') !== false || $name[0] === '/' || strpos($name, '\\') !== false || strpos($name, "\0") !== false) return false;
    if (!preg_match('#^[A-Za-z0-9._/-]+$#', $name)) return false;
    $base = basename($name);
    if ($base === 'deploy.php' || $base === '.deploy-manifest.php' || $base === '.contact-secret.php') return false;
    if ($name === 'contact.php') return true;
    if ($base === '.htaccess') return in_array($name, ['.htaccess', 'img/.htaccess', 'assets/.htaccess'], true);
    if ($base[0] === '.') return false;
    return (bool)preg_match('/\.(html|css|js|webp|jpe?g|png|gif|svg|ico|woff2|xml|txt|pdf)$/i', $base);
}

function leer_manifest() {
    if (!is_file(MANIFEST)) return [];
    $raw = substr(file_get_contents(MANIFEST), strlen('<?php exit; ?>'));
    return json_decode($raw, true) ?: [];
}

$action = $_GET['action'] ?? '';
$method = $_SERVER['REQUEST_METHOD'];

if ($action === 'manifest') {
    out(200, ['ok' => true, 'manifest' => (object)leer_manifest(), 'zip' => class_exists('ZipArchive'), 'version' => 2]);
}

if ($method !== 'POST') out(405, ['ok' => false, 'error' => 'método']);
$len = (int)($_SERVER['CONTENT_LENGTH'] ?? 0);
if ($len <= 0 || $len > MAX_BYTES) out(413, ['ok' => false, 'error' => 'tamaño']);

if ($action === 'upload') {
    if (!class_exists('ZipArchive')) out(500, ['ok' => false, 'error' => 'ZipArchive no disponible en el servidor']);
    $tmp = tempnam(sys_get_temp_dir(), 'cdo');
    file_put_contents($tmp, file_get_contents('php://input', false, null, 0, MAX_BYTES));
    $zip = new ZipArchive();
    if ($zip->open($tmp) !== true) { @unlink($tmp); out(400, ['ok' => false, 'error' => 'zip no válido']); }
    $n = 0; $rechazados = [];
    for ($i = 0; $i < $zip->numFiles; $i++) {
        $name = $zip->getNameIndex($i);
        if ($name === '' || substr($name, -1) === '/') continue;
        if (!permitido($name)) { $rechazados[] = $name; continue; }
        $dest = __DIR__ . '/' . $name;
        if (!is_dir(dirname($dest))) mkdir(dirname($dest), 0755, true);
        $data = $zip->getFromIndex($i);
        if ($data === false || file_put_contents($dest, $data, LOCK_EX) === false) {
            $zip->close(); @unlink($tmp); out(500, ['ok' => false, 'error' => "no se pudo escribir $name"]);
        }
        @chmod($dest, 0644);
        $n++;
    }
    $zip->close(); @unlink($tmp);
    out(200, ['ok' => true, 'files' => $n, 'rechazados' => $rechazados]);
}

if ($action === 'delete') {
    $lista = json_decode(file_get_contents('php://input'), true);
    if (!is_array($lista)) out(400, ['ok' => false, 'error' => 'lista no válida']);
    $conocidos = leer_manifest();
    $n = 0;
    foreach ($lista as $name) {
        // solo borra archivos que este receptor publicó antes y que son de tipo permitido
        if (!is_string($name) || !isset($conocidos[$name]) || !permitido($name)) continue;
        $f = __DIR__ . '/' . $name;
        if (is_file($f) && @unlink($f)) $n++;
        $d = dirname($f);
        while ($d !== __DIR__ && is_dir($d) && count(scandir($d)) === 2) { @rmdir($d); $d = dirname($d); }
    }
    out(200, ['ok' => true, 'deleted' => $n]);
}

if ($action === 'commit') {
    $m = json_decode(file_get_contents('php://input'), true);
    if (!is_array($m)) out(400, ['ok' => false, 'error' => 'manifest no válido']);
    file_put_contents(MANIFEST, '<?php exit; ?>' . json_encode($m), LOCK_EX);
    out(200, ['ok' => true]);
}

out(400, ['ok' => false, 'error' => 'acción desconocida']);
