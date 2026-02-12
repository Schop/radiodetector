<?php
$pdo = new PDO('sqlite:d:/dev/radiochecker/static_web/radio_songs.db');

// Add some recent test songs
$now = new DateTime();
$testSongs = [
    ['timestamp' => $now->modify('-2 minutes')->format('Y-m-d\TH:i:s') . '.000000', 'artist' => 'Test Artist 1', 'song' => 'Recent Song 1', 'station' => 'Test Station'],
    ['timestamp' => $now->modify('-4 minutes')->format('Y-m-d\TH:i:s') . '.000000', 'artist' => 'Test Artist 2', 'song' => 'Recent Song 2', 'station' => 'Test Station'],
    ['timestamp' => $now->modify('-6 minutes')->format('Y-m-d\TH:i:s') . '.000000', 'artist' => 'Test Artist 3', 'song' => 'Recent Song 3', 'station' => 'Test Station'],
    ['timestamp' => $now->modify('-8 minutes')->format('Y-m-d\TH:i:s') . '.000000', 'artist' => 'Test Artist 4', 'song' => 'Recent Song 4', 'station' => 'Test Station'],
    ['timestamp' => $now->modify('-12 minutes')->format('Y-m-d\TH:i:s') . '.000000', 'artist' => 'Test Artist 5', 'song' => 'Old Song', 'station' => 'Test Station'],
];

$stmt = $pdo->prepare("INSERT INTO songs (timestamp, artist, song, station) VALUES (?, ?, ?, ?)");
foreach ($testSongs as $song) {
    $stmt->execute([$song['timestamp'], $song['artist'], $song['song'], $song['station']]);
}

echo "Added " . count($testSongs) . " test songs to database.\n";
?>