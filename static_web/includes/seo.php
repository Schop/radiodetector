<?php
// Helpers for the numbers that index.php renders on the server, so crawlers and AI search
// engines that do not run JavaScript still see real figures. The page script overwrites the
// same elements with live values afterwards.

function h($value) {
    return htmlspecialchars((string)$value, ENT_QUOTES, 'UTF-8');
}

// Escaped value, or the same '...' placeholder the page script starts with
function seo_text($value) {
    return ($value === null || $value === '') ? '...' : h($value);
}

// "11 feb 2026", like toLocaleDateString('nl-NL', {day: 'numeric', month: 'short', year: 'numeric'})
function nl_date_short($value) {
    static $months = ['jan', 'feb', 'mrt', 'apr', 'mei', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec'];
    try {
        $d = new DateTime($value);
    } catch (Exception $e) {
        return h($value);
    }
    return $d->format('j') . ' ' . $months[(int)$d->format('n') - 1] . ' ' . $d->format('Y');
}

function seo_link($href, $label) {
    return '<a href="' . h($href) . '" class="text-decoration-none">' . h($label) . '</a>';
}

function station_href($name) {
    return '/station.php#' . rawurlencode($name);
}

function song_href($name) {
    return '/song.php#' . rawurlencode($name);
}

// Detection timestamps are naive Amsterdam local time, whatever the web host's timezone is
function minutes_since($timestamp) {
    $tz = new DateTimeZone('Europe/Amsterdam');
    try {
        $then = new DateTime($timestamp, $tz);
    } catch (Exception $e) {
        return null;
    }
    $now = new DateTime('now', $tz);
    return max(0, (int)round(($now->getTimestamp() - $then->getTimestamp()) / 60));
}

// "1 nummer" / "5 nummers"
function nl_count($n, $singular, $plural) {
    return number_format($n, 0, ',', '.') . ' ' . ($n === 1 ? $singular : $plural);
}
