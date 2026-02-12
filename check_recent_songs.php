<?php
$pdo = new PDO('sqlite:d:/dev/radiochecker/static_web/radio_songs.db');
$cutoff = (new DateTime())->modify('-10 minutes')->format('Y-m-d\TH:i:s');
echo "Cutoff time: $cutoff\n";

$stmt = $pdo->prepare("SELECT timestamp, artist, song FROM songs WHERE timestamp > ? ORDER BY timestamp DESC LIMIT 10");
$stmt->execute([$cutoff]);
$results = $stmt->fetchAll(PDO::FETCH_ASSOC);

echo "Recent songs:\n";
foreach ($results as $row) {
    echo $row['timestamp'] . " - " . $row['artist'] . " - " . $row['song'] . "\n";
}

echo "\nTotal recent songs: " . count($results) . "\n";
?>