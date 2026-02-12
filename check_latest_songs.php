<?php
$pdo = new PDO('sqlite:d:/dev/radiochecker/static_web/radio_songs.db');

$stmt = $pdo->query("SELECT timestamp, artist, song FROM songs ORDER BY timestamp DESC LIMIT 10");
$results = $stmt->fetchAll(PDO::FETCH_ASSOC);

echo "Latest songs in database:\n";
foreach ($results as $row) {
    echo $row['timestamp'] . " - " . $row['artist'] . " - " . $row['song'] . "\n";
}

echo "\nTotal songs in database: " . $pdo->query("SELECT COUNT(*) FROM songs")->fetchColumn() . "\n";
?>