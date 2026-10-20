<?php
// Router & Auth for yt-dlp Web UI on NAS542
$auth_user = 'admin';
$auth_pass = '12345678';

// Try to read credentials from secrets file if available
$secrets_file = '/i-data/45f1aca1/Apps/secrets.env';
if (file_exists($secrets_file)) {
    $lines = file($secrets_file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos($line, '=') !== false && strpos($line, '#') !== 0) {
            list($k, $v) = explode('=', $line, 2);
            $k = trim($k);
            $v = trim($v, " \t\n\r\0\x0B\"'");
            if ($k === 'NAS_ADMIN_USER') $auth_user = $v;
            if ($k === 'NAS_ADMIN_PASS') $auth_pass = $v;
        }
    }
}

// HTTP Basic Authentication
$user = isset($_SERVER['PHP_AUTH_USER']) ? $_SERVER['PHP_AUTH_USER'] : null;
$pass = isset($_SERVER['PHP_AUTH_PW']) ? $_SERVER['PHP_AUTH_PW'] : null;

// Also support Authorization header passed from Apache proxy
if (!$user && isset($_SERVER['HTTP_AUTHORIZATION'])) {
    if (strpos(strtolower($_SERVER['HTTP_AUTHORIZATION']), 'basic ') === 0) {
        $creds = explode(':', base64_decode(substr($_SERVER['HTTP_AUTHORIZATION'], 6)), 2);
        if (count($creds) === 2) {
            $user = $creds[0];
            $pass = $creds[1];
        }
    }
}

if ($user !== $auth_user || $pass !== $auth_pass) {
    header('WWW-Authenticate: Basic realm="NAS542 yt-dlp"');
    header('HTTP/1.0 401 Unauthorized');
    echo 'Unauthorized: please enter your NAS credentials.';
    exit;
}

$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

// Normalize path when accessed via proxy
$path = preg_replace('#^/apps/ytdl/#', '/', $path);
$path = preg_replace('#^/apps/ytdl$#', '/', $path);

if ($path === '/' || $path === '') {
    require __DIR__ . '/index.html';
    exit;
}

if ($path === '/api.php' || strpos($path, '/api.php') === 0) {
    require __DIR__ . '/api.php';
    exit;
}

$file = __DIR__ . $path;
if (file_exists($file) && !is_dir($file)) {
    return false; // let built-in server handle static asset
}

require __DIR__ . '/index.html';
exit;
