<?php
// Status of the checker on the Pi, from heartbeat.json (written by heartbeat.php).
// Sets $hb_banner (most severe problem, or '') and $hb_footer (when the Pi last reported in, or '').
// Nothing is shown until the first heartbeat has arrived, so deploying the site before the Pi is
// configured doesn't raise an alarm.
$hb_banner = '';
$hb_footer = '';

(function () use (&$hb_banner, &$hb_footer) {
    $silent_after = 15 * 60;      // no heartbeat for this long: the Pi or its network is down
    $stuck_after = 60 * 60;       // no station changed song for this long: the feeds are stuck
    $upload_late_after = 30 * 60; // detections waiting this long for an upload: the site lags behind

    $file = defined('HEARTBEAT_FILE') ? HEARTBEAT_FILE : __DIR__ . '/../heartbeat.json';
    $raw = is_file($file) ? @file_get_contents($file) : false;
    $hb = $raw ? json_decode($raw, true) : null;
    if (!is_array($hb) || !isset($hb['received_at'])) return;

    $now = defined('HEARTBEAT_NOW') ? HEARTBEAT_NOW : time();
    $age = max(0, $now - (int)$hb['received_at']);
    $clock = function ($ts) {
        return (new DateTime('@' . (int)$ts))->setTimezone(new DateTimeZone('Europe/Amsterdam'))->format('H:i');
    };
    $ago = function ($seconds) {
        if ($seconds < 60) return 'zojuist';
        if ($seconds < 3600) return floor($seconds / 60) . ' min geleden';
        if ($seconds < 172800) return floor($seconds / 3600) . ' uur geleden';
        return floor($seconds / 86400) . ' dagen geleden';
    };

    $ok = (int)($hb['stations_ok'] ?? 0);
    $total = (int)($hb['stations_total'] ?? 0);
    $last_change = $hb['last_change_age_s'] ?? null;
    $upload_pending = $hb['upload_pending_age_s'] ?? null;

    if ($age > $silent_after) {
        $hb_banner = 'Let op: de detectie ligt stil. De laatste melding van de controle was om '
            . $clock($hb['received_at']) . ', dus nieuwe nummers worden mogelijk niet gezien.';
    } elseif ($total > 0 && $ok < max(1, $total / 2)) {
        $hb_banner = "Let op: de controle draait, maar krijgt nog maar van $ok van de $total radiostations gegevens.";
    } elseif ($last_change !== null && $last_change > $stuck_after) {
        $hb_banner = 'Let op: er is al meer dan een uur bij geen enkel radiostation een nieuw nummer gezien. De bronnen lijken vast te zitten.';
    } elseif ($upload_pending !== null && $upload_pending > $upload_late_after) {
        $hb_banner = 'De gegevens op deze site lopen achter: nieuwe detecties zijn sinds '
            . $clock($hb['received_at'] - $upload_pending) . ' nog niet verwerkt.';
    }

    $hb_footer = 'Laatste controle: ' . $ago($age);
})();
