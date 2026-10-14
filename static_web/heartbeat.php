<?php
// Receives the checker's heartbeat (HTTPS POST from the Pi) and stores it in heartbeat.json,
// which includes/heartbeat_status.php turns into the status banner and the footer line.
// The shared secret lives in heartbeat_secret.php (not in git, see heartbeat_secret.php.example).
header('Content-Type: application/json');
header('Cache-Control: no-store');

function heartbeat_fail($code, $message) {
    http_response_code($code);
    echo json_encode(['error' => $message]);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    heartbeat_fail(405, 'POST only');
}

$secret_file = __DIR__ . '/heartbeat_secret.php';
$secret = is_file($secret_file) ? (include $secret_file) : '';
$given = $_SERVER['HTTP_X_HEARTBEAT_SECRET'] ?? '';
if (!is_string($secret) || $secret === '' || !hash_equals($secret, (string)$given)) {
    heartbeat_fail(403, 'forbidden');
}

if ((int)($_SERVER['CONTENT_LENGTH'] ?? 0) > 4096) {
    heartbeat_fail(413, 'payload too large');
}
$body = json_decode(file_get_contents('php://input'), true);
if (!is_array($body) || !isset($body['stations_ok'], $body['stations_total'])) {
    heartbeat_fail(400, 'invalid payload');
}

// Ages are sent relative ("n seconds ago") so a wrong clock on the Pi doesn't matter;
// the moment of receipt is stamped here with the server's clock.
$age = function ($key) use ($body) {
    return isset($body[$key]) && is_numeric($body[$key]) ? max(0, (int)$body[$key]) : null;
};
$data = [
    'received_at' => time(),
    'stations_ok' => max(0, (int)$body['stations_ok']),
    'stations_total' => max(0, (int)$body['stations_total']),
    'last_change_age_s' => $age('last_change_age_s'),
    'upload_pending_age_s' => $age('upload_pending_age_s'),
];

// write to a temp file and rename, so a page never reads a half-written file
$target = __DIR__ . '/heartbeat.json';
$tmp = $target . '.tmp';
if (file_put_contents($tmp, json_encode($data), LOCK_EX) === false || !rename($tmp, $target)) {
    heartbeat_fail(500, 'could not store heartbeat');
}
echo json_encode(['ok' => true]);
