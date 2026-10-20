<?php
// Minimal router for PHP built-in server:
// /jsonrpc -> proxy to aria2c RPC on 127.0.0.1:6800, everything else -> static files

$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

if ($path === '/jsonrpc' || $path === '/jsonrpc/') {
    $body = file_get_contents('php://input');
    $ch = curl_init('http://127.0.0.1:6800/jsonrpc');
    curl_setopt_array($ch, array(
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $body,
        CURLOPT_HTTPHEADER     => array('Content-Type: application/json'),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 60,
    ));
    $resp = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    http_response_code($code ? $code : 502);
    header('Content-Type: application/json');
    echo $resp;
    exit;
}

return false;
