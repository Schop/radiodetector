<?php
$pdo = new PDO('sqlite:d:/dev/radiochecker/static_web/radio_songs.db');

$now = new DateTime();
$cutoff_10min = $now->modify('-10 minutes')->format('Y-m-d\TH:i:s');
$cutoff_1hour = $now->modify('-50 minutes')->format('Y-m-d\TH:i:s'); // back to 1 hour total

echo "Current time: " . (new DateTime())->format('Y-m-d\TH:i:s') . "\n";
echo "10 min cutoff: $cutoff_10min\n";
echo "1 hour cutoff: $cutoff_1hour\n\n";

$stmt = $pdo->prepare("SELECT timestamp, artist, song FROM songs WHERE timestamp > ? ORDER BY timestamp DESC");
$stmt->execute([$cutoff_10min]);
$results_10min = $stmt->fetchAll(PDO::FETCH_ASSOC);

$stmt = $pdo->prepare("SELECT timestamp, artist, song FROM songs WHERE timestamp > ? ORDER BY timestamp DESC");
$stmt->execute([$cutoff_1hour]);
$results_1hour = $stmt->fetchAll(PDO::FETCH_ASSOC);

echo "Songs in last 10 minutes: " . count($results_10min) . "\n";
echo "Songs in last hour: " . count($results_1hour) . "\n\n";

if (count($results_1hour) > 0) {
    echo "Recent songs (last hour):\n";
    foreach (array_slice($results_1hour, 0, 5) as $row) {
        echo $row['timestamp'] . " - " . $row['artist'] . " - " . $row['song'] . "\n";
    }
}
?>