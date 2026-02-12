<?php
$pdo = new PDO('sqlite:d:/dev/radiochecker/static_web/radio_songs.db');

// Delete old test songs
$pdo->exec("DELETE FROM songs WHERE artist LIKE 'Test Artist%'");

// Add new test songs with correct artists
$now = new DateTime();
$testSongs = [
    ['timestamp' => $now->modify('-2 minutes')->format('Y-m-d\TH:i:s') . '.000000', 'artist' => 'Phil Collins', 'song' => 'Recent Song 1', 'station' => 'Test Station 1'],
    ['timestamp' => $now->modify('-4 minutes')->format('Y-m-d\TH:i:s') . '.000000', 'artist' => 'Genesis', 'song' => 'Recent Song 2', 'station' => 'Test Station 2'],
    ['timestamp' => $now->modify('-6 minutes')->format('Y-m-d\TH:i:s') . '.000000', 'artist' => 'Phil Collins', 'song' => 'Recent Song 3', 'station' => 'Test Station 3'],
    ['timestamp' => $now->modify('-8 minutes')->format('Y-m-d\TH:i:s') . '.000000', 'artist' => 'Genesis', 'song' => 'Recent Song 4', 'station' => 'Test Station 4'],
    ['timestamp' => $now->modify('-12 minutes')->format('Y-m-d\TH:i:s') . '.000000', 'artist' => 'Phil Collins', 'song' => 'Old Song', 'station' => 'Test Station 5'],
];

$stmt = $pdo->prepare("INSERT INTO songs (timestamp, artist, song, station) VALUES (?, ?, ?, ?)");
foreach ($testSongs as $song) {
    $stmt->execute([$song['timestamp'], $song['artist'], $song['song'], $song['station']]);
}

echo "Added " . count($testSongs) . " test songs with correct artists.\n";
?>