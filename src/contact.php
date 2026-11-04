<?php
/**
 * Clínica Dental Ontiveros — formulario de cita / "te llamamos".
 * Medidas anti-spam / anti-abuso:
 *  - Suma (captcha) generada y firmada en el servidor (HMAC), caduca a los 30 min.
 *  - Tiempo mínimo de relleno (bots envían en milisegundos).
 *  - Campo trampa (honeypot).
 *  - Límite de envíos por IP (5 mensajes enviados cada 15 minutos).
 *  - Solo acepta envíos hechos desde la propia web (cabecera Origin).
 *  - Longitudes máximas y limpieza de saltos de línea en cabeceras (sin inyección de cabeceras).
 */
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

/* ===================== CONFIGURACIÓN ===================== */
// Destinatario(s). Varios: ['uno@dominio.es', 'otro@dominio.es']
$DESTINO      = ['m.musso@celdas.com'];
// Copia oculta de todos los mensajes. Vacío [] = no.
$COPIA_OCULTA = [];
// Webs desde las que se acepta el formulario
$ORIGENES     = ['clinicadentalontiveros.es', 'www.clinicadentalontiveros.es'];
/* ========================================================= */
$REMITENTE = 'web@clinicadentalontiveros.es';            // buzón del propio dominio (si no hay SMTP)

// Envío autenticado (SMTP). Los datos los pone build.py desde los secretos de GitHub;
// en el repositorio solo hay marcadores.
$SMTP_HOST = '__SMTP_HOST__';
$SMTP_PORT = (int)'__SMTP_PORT__';
$SMTP_USER = '__SMTP_USER__';
$SMTP_PASS = '__SMTP_PASS__';
$SMTP_ON   = strpos($SMTP_USER, '__') !== 0 && $SMTP_USER !== '' && strpos($SMTP_PASS, '__') !== 0;
if ($SMTP_ON) $REMITENTE = $SMTP_USER;
$LIMITE    = 5;                             // envíos por IP...
$VENTANA   = 900;                           // ...cada 15 minutos

function out($ok, $msg, $code = 200) { http_response_code($code); echo json_encode(['ok' => $ok, 'message' => $msg]); exit; }

// Clave secreta propia del servidor (se crea sola la primera vez; no está en el repositorio)
$secretFile = __DIR__ . '/.contact-secret.php';
if (!is_file($secretFile)) {
    @file_put_contents($secretFile, '<?php return ' . var_export(bin2hex(random_bytes(32)), true) . ';', LOCK_EX);
}
$SECRET = @include $secretFile;
if (!is_string($SECRET) || strlen($SECRET) < 32) out(false, 'Error de configuración del formulario.', 500);


/** Envío SMTP con autenticación (SSL 465 o STARTTLS 587). Devuelve true o deja el error en $err. */
function smtp_send($host, $port, $user, $pass, $from, array $to, array $bcc, $subject, $body, $replyTo, &$err, $verify = true) {
    $ctx = stream_context_create(['ssl' => ['verify_peer' => $verify, 'verify_peer_name' => $verify, 'allow_self_signed' => !$verify]]);
    $s = @stream_socket_client(($port == 465 ? 'ssl://' : 'tcp://') . "$host:$port", $errno, $errstr, 15, STREAM_CLIENT_CONNECT, $ctx);
    if (!$s) { $err = "conexion: $errstr"; return false; }
    stream_set_timeout($s, 20);
    $read = function () use ($s) { $d = ''; while (($l = fgets($s, 515)) !== false) { $d .= $l; if (isset($l[3]) && $l[3] === ' ') break; } return $d; };
    $cmd = function ($c, $ok) use ($s, $read, &$err) {
        if ($c !== null) fwrite($s, $c . "\r\n");
        $r = $read();
        if ((int)substr($r, 0, 3) !== $ok) { $err = trim(substr($r, 0, 120)) ?: 'sin respuesta'; return false; }
        return true;
    };
    $ehlo = 'EHLO ' . preg_replace('/[^a-z0-9.-]/i', '', $_SERVER['SERVER_NAME'] ?? 'localhost');
    $ok = $cmd(null, 220) && $cmd($ehlo, 250);
    if ($ok && $port == 587) {
        $ok = $cmd('STARTTLS', 220) && stream_socket_enable_crypto($s, true, STREAM_CRYPTO_METHOD_TLS_CLIENT) && $cmd($ehlo, 250);
    }
    $ok = $ok && $cmd('AUTH LOGIN', 334) && $cmd(base64_encode($user), 334) && $cmd(base64_encode($pass), 235)
              && $cmd("MAIL FROM:<$from>", 250);
    foreach (array_merge($to, $bcc) as $r) { $ok = $ok && $cmd("RCPT TO:<$r>", 250); }
    $ok = $ok && $cmd('DATA', 354);
    if ($ok) {
        $h = 'Date: ' . date('r') . "\r\nFrom: Web Clinica Dental Ontiveros <$from>\r\nTo: " . implode(', ', $to) . "\r\nReply-To: $replyTo\r\nSubject: $subject\r\n"
           . 'Message-ID: <' . bin2hex(random_bytes(10)) . "@clinicadentalontiveros.es>\r\nMIME-Version: 1.0\r\n"
           . "Content-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n";
        $ok = $cmd($h . "\r\n" . chunk_split(base64_encode($body)) . "\r\n.", 250);
    }
    @$cmd('QUIT', 221);
    fclose($s);
    return $ok;
}

function b64u($s) { return rtrim(strtr(base64_encode($s), '+/', '-_'), '='); }
function b64d($s) { return base64_decode(strtr($s, '-_', '+/')); }

// GET ?captcha=1 -> nueva suma firmada
if ($_SERVER['REQUEST_METHOD'] === 'GET' && isset($_GET['captcha'])) {
    $a = random_int(2, 9); $b = random_int(2, 9);
    $payload = json_encode(['s' => $a + $b, 't' => time(), 'n' => bin2hex(random_bytes(6))]);
    $token = b64u($payload) . '.' . b64u(hash_hmac('sha256', $payload, $SECRET, true));
    echo json_encode(['q' => "$a + $b", 'token' => $token]);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') { header('Allow: POST, GET'); out(false, 'Método no permitido.', 405); }

// Solo desde la propia web
if (!empty($_SERVER['HTTP_ORIGIN'])) {
    $host = strtolower((string)parse_url($_SERVER['HTTP_ORIGIN'], PHP_URL_HOST));
    if (!in_array($host, $ORIGENES, true)) out(false, 'Origen no permitido.', 403);
}

// Honeypot: se responde "ok" para no dar pistas al bot
if (!empty($_POST['website'])) out(true, 'Mensaje enviado. Gracias.');

// Límite de envíos por IP
$ip = $_SERVER['REMOTE_ADDR'] ?? '0';
$rlFile = sys_get_temp_dir() . '/cdo_rl_' . hash('sha256', $ip . $SECRET);
$hits = array_filter(json_decode(@file_get_contents($rlFile) ?: '[]', true) ?: [], fn($t) => $t > time() - $VENTANA);
if (count($hits) >= $LIMITE) out(false, 'Demasiados envíos seguidos. Inténtelo más tarde o llame al 952 92 43 22.', 429);

// Captcha firmado
$parts = explode('.', (string)($_POST['token'] ?? ''));
if (count($parts) !== 2) out(false, 'Recargue la página e inténtelo de nuevo.', 400);
$payload = b64d($parts[0]);
if (!hash_equals(hash_hmac('sha256', $payload, $SECRET, true), b64d($parts[1]))) out(false, 'Recargue la página e inténtelo de nuevo.', 400);
$p = json_decode($payload, true);
$edad = time() - (int)($p['t'] ?? 0);
if ($edad > 1800) out(false, 'El formulario ha caducado. Recargue la página.', 400);
if ($edad < 3) out(false, 'Revise los datos y vuelva a enviar.', 400);
if ((int)($_POST['captcha'] ?? -1) !== (int)$p['s']) out(false, 'La suma no es correcta.', 400);

// Datos
// Recorte seguro en UTF-8 (el servidor puede no tener la extensión mbstring)
function cortar($s, $max) {
    if (function_exists('mb_substr')) return mb_substr($s, 0, $max, 'UTF-8');
    return preg_match('/^.{0,' . (int)$max . '}/su', $s, $m) ? $m[0] : substr($s, 0, $max);
}
$campo = function ($k, $max) { return cortar(trim((string)($_POST[$k] ?? '')), $max); };
$tipo      = ($_POST['tipo'] ?? '') === 'llamada' ? 'llamada' : 'cita';
$nombre    = $campo('nombre', 80);
$email     = $campo('email', 160);
$telefono  = preg_replace('/[^0-9+ ()-]/', '', $campo('telefono', 30));
$motivo    = $campo('motivo', 120);
$mensaje   = $campo('mensaje', 5000);

if ($nombre === '') out(false, 'Indique su nombre.', 400);
if (strlen(preg_replace('/\D/', '', $telefono)) < 9) out(false, 'Indique un teléfono válido.', 400);
if ($tipo === 'cita') {
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) out(false, 'El email no es válido.', 400);
    if ($mensaje === '') out(false, 'Escriba un mensaje.', 400);
}
if (empty($_POST['acepto'])) out(false, 'Debe aceptar los términos y condiciones.', 400);
if (preg_match_all('#https?://#i', $mensaje) > 3) out(false, 'El mensaje contiene demasiados enlaces.', 400);

$lista = fn($v) => array_values(array_filter(array_map('trim', (array)$v), fn($e) => filter_var($e, FILTER_VALIDATE_EMAIL)));
$PARA = $lista($DESTINO);
$BCC  = array_values(array_diff($lista($COPIA_OCULTA), $PARA));
if (!$PARA) out(false, 'Error de configuración del formulario.', 500);

$una = fn($s) => trim(preg_replace('/[\r\n\t\x00-\x1F\x7F]+/', ' ', $s));
$asunto = ($tipo === 'llamada' ? 'Web: que le llamen - ' : 'Web: solicitud de cita - ') . $una($nombre);
$cuerpo = ($tipo === 'llamada' ? "El paciente pide que le llamen.\n\n" : "Solicitud de cita desde la web.\n\n")
        . "Nombre: " . $una($nombre) . "\nTeléfono: $telefono\n"
        . ($email !== '' ? "Email: " . $una($email) . "\n" : '')
        . ($motivo !== '' ? "Motivo: " . $una($motivo) . "\n" : '')
        . "IP: $ip\n"
        . ($mensaje !== '' ? "\nMensaje:\n" . str_replace("\0", '', $mensaje) . "\n" : '');
$replyTo = filter_var($email, FILTER_VALIDATE_EMAIL) ? $una($email) : $REMITENTE;
$cabeceras = "From: Web Clinica Dental Ontiveros <$REMITENTE>\r\n"
           . "Reply-To: " . $replyTo . "\r\n"
           . "MIME-Version: 1.0\r\n"
           . "Content-Type: text/plain; charset=UTF-8\r\n"
           . ($BCC ? 'Bcc: ' . implode(', ', $BCC) . "\r\n" : '')
           . "Content-Transfer-Encoding: 8bit\r\n";

$asuntoEnc = '=?UTF-8?B?' . base64_encode($asunto) . '?=';
$enviado = false; $codigo = '';
if ($SMTP_ON) {
    $err = '';
    $enviado = smtp_send($SMTP_HOST, $SMTP_PORT ?: 465, $SMTP_USER, $SMTP_PASS, $SMTP_USER, $PARA, $BCC, $asuntoEnc, $cuerpo, $replyTo, $err)
            || (stripos($err, 'conexion') === 0 && smtp_send($SMTP_HOST, $SMTP_PORT ?: 465, $SMTP_USER, $SMTP_PASS, $SMTP_USER, $PARA, $BCC, $asuntoEnc, $cuerpo, $replyTo, $err, false));
    if (!$enviado) $codigo = ' (SMTP: ' . preg_replace('/[^\w :.-]/u', '', substr($err, 0, 60)) . ')';
} else {
    $destStr = implode(', ', $PARA);
    $enviado = @mail($destStr, $asuntoEnc, $cuerpo, $cabeceras, '-f' . $REMITENTE) || @mail($destStr, $asuntoEnc, $cuerpo, $cabeceras);
}
if ($enviado) {
    $hits[] = time();
    @file_put_contents($rlFile, json_encode(array_values($hits)), LOCK_EX);
    out(true, $tipo === 'llamada' ? 'Recibido. Le llamaremos lo antes posible.' : 'Solicitud enviada. Le contactaremos para confirmar la cita.');
}
out(false, 'No se ha podido enviar. Llámenos al 952 92 43 22 o escriba a info@clinicadentalontiveros.es.' . $codigo, 500);
