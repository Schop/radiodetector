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

// The payload carries the per-station snapshot for nu.php (~100 bytes per station), so allow some room.
const HEARTBEAT_MAX_BYTES = 65536;
if ((int)($_SERVER['CONTENT_LENGTH'] ?? 0) > HEARTBEAT_MAX_BYTES) {
    heartbeat_fail(413, 'payload too large');
}
$raw_body = file_get_contents('php://input', false, null, 0, HEARTBEAT_MAX_BYTES + 1);
if (strlen($raw_body) > HEARTBEAT_MAX_BYTES) {
    heartbeat_fail(413, 'payload too large');
}
$body = json_decode($raw_body, true);
if (!is_array($body) || !isset($body['stations_ok'], $body['stations_total'])) {
    heartbeat_fail(400, 'invalid payload');
}

// Ages are sent relative ("n seconds ago") so a wrong clock on the Pi doesn't matter;
// the moment of receipt is stamped here with the server's clock.
function heartbeat_age($value) {
    return is_numeric($value) ? max(0, (int)$value) : null;
}
function heartbeat_text($value) {
    return is_string($value) && trim($value) !== '' ? mb_substr(trim($value), 0, 200) : null;
}
$received_at = time();
$data = [
    'received_at' => $received_at,
    'stations_ok' => max(0, (int)$body['stations_ok']),
    'stations_total' => max(0, (int)$body['stations_total']),
    'last_change_age_s' => heartbeat_age($body['last_change_age_s'] ?? null),
    'upload_pending_age_s' => heartbeat_age($body['upload_pending_age_s'] ?? null),
];

// what is on air per station, for nu.php (optional: an older sender doesn't send it)
$stations = null;
if (isset($body['stations']) && is_array($body['stations'])) {
    $stations = [];
    foreach (array_slice($body['stations'], 0, 200) as $s) {
        $name = is_array($s) ? heartbeat_text($s['station'] ?? null) : null;
        if ($name === null) continue;
        $stations[] = [
            'station' => $name,
            'artist' => heartbeat_text($s['artist'] ?? null),
            'song' => heartbeat_text($s['song'] ?? null),
            'source' => heartbeat_text($s['source'] ?? null),
            'since_age_s' => heartbeat_age($s['since_age_s'] ?? null),
            'seen_age_s' => heartbeat_age($s['seen_age_s'] ?? null),
            'highlight' => !empty($s['highlight']),
        ];
    }
}

// write to a temp file and rename, so a page never reads a half-written file
function heartbeat_store($target, $data) {
    $tmp = $target . '.tmp';
    return file_put_contents($tmp, json_encode($data), LOCK_EX) !== false && rename($tmp, $target);
}
if (!heartbeat_store(__DIR__ . '/heartbeat.json', $data)) {
    heartbeat_fail(500, 'could not store heartbeat');
}
if ($stations !== null
    && !heartbeat_store(__DIR__ . '/stations_now.json', ['received_at' => $received_at, 'stations' => $stations])) {
    heartbeat_fail(500, 'could not store stations');
}
echo json_encode(['ok' => true]);
