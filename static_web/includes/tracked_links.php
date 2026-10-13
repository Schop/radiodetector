<?php
// Footer links to the side-project songs, built from the 'tracked_songs' setting ("Artist - Title").
// Entries without an artist can't be linked (tracked.php needs both) and are skipped.
if (!defined('RADIO_API_LIBRARY')) define('RADIO_API_LIBRARY', true);
require_once __DIR__ . '/../api.php';

$tracked_links = [];
$tracked_entries = get_setting('tracked_songs', []);
if (is_array($tracked_entries)) {
    foreach ($tracked_entries as $entry) {
        $parts = explode(' - ', (string)$entry, 2);
        if (count($parts) !== 2) continue;
        [$t_artist, $t_song] = array_map('trim', $parts);
        if ($t_artist === '' || $t_song === '') continue;
        // on a tracked song's own page only list the others
        if (isset($artist, $song) && strcasecmp($artist, $t_artist) === 0 && strcasecmp($song, $t_song) === 0) continue;

        $href = 'tracked.php?' . http_build_query(['artist' => $t_artist, 'song' => $t_song]);
        $tracked_links[] = '<a href="' . htmlspecialchars($href, ENT_QUOTES, 'UTF-8') . '" class="text-decoration-none">'
            . htmlspecialchars("$t_song - $t_artist", ENT_QUOTES, 'UTF-8') . '</a>';
    }
}
