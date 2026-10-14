<?php
// Reads stations_now.json (written by heartbeat.php) for nu.php.
// Returns ['received_at' => unix time, 'rows' => [...]] or null when no snapshot has arrived yet.
// Each row: station, artist, song, source, highlight, seen_ago_s (how long ago the checker last got
// data for this station), since_s (how long that song has been seen), stale (no recent data).

const STATIONS_NOW_STALE_AFTER = 10 * 60;  // no data from a station for this long: show it greyed out

function load_stations_now($file, $now) {
    $raw = is_file($file) ? @file_get_contents($file) : false;
    $data = $raw ? json_decode($raw, true) : null;
    if (!is_array($data) || !isset($data['received_at'], $data['stations']) || !is_array($data['stations'])) {
        return null;
    }
    // ages in the file are relative to the moment the heartbeat arrived
    $elapsed = max(0, $now - (int)$data['received_at']);
    $rows = [];
    foreach ($data['stations'] as $s) {
        if (empty($s['station'])) continue;
        $has_song = !empty($s['artist']) && !empty($s['song']);
        $seen_ago = isset($s['seen_age_s']) ? (int)$s['seen_age_s'] + $elapsed : null;
        $rows[] = [
            'station' => $s['station'],
            'artist' => $has_song ? $s['artist'] : null,
            'song' => $has_song ? $s['song'] : null,
            'source' => $s['source'] ?? null,
            'highlight' => !empty($s['highlight']),
            'seen_ago_s' => $seen_ago,
            'since_s' => isset($s['since_age_s']) ? (int)$s['since_age_s'] + $elapsed : null,
            'stale' => !$has_song || $seen_ago === null || $seen_ago > STATIONS_NOW_STALE_AFTER,
        ];
    }
    usort($rows, fn($a, $b) => strcasecmp($a['station'], $b['station']));
    return ['received_at' => (int)$data['received_at'], 'rows' => $rows];
}

// "3 min" / "2 uur" / "1 dag" style duration, for "gezien sinds ... geleden"
function nu_duration($seconds) {
    if ($seconds < 60) return 'minder dan 1 min';
    if ($seconds < 3600) return floor($seconds / 60) . ' min';
    if ($seconds < 86400) return floor($seconds / 3600) . ' uur';
    return floor($seconds / 86400) . ' dgn';
}
