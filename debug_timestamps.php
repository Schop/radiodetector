<?php
$pdo = new PDO('sqlite:d:/dev/radiochecker/static_web/radio_songs.db');

$now = new DateTime();
$cutoff = $now->modify('-10 minutes')->format('Y-m-d\TH:i:s');

echo "Current time: " . (new DateTime())->format('Y-m-d\TH:i:s') . "\n";
echo "Cutoff: $cutoff\n\n";

// Check exact format
$stmt = $pdo->query("SELECT timestamp FROM songs ORDER BY timestamp DESC LIMIT 1");
$latest = $stmt->fetchColumn();
echo "Latest timestamp in DB: $latest\n";
echo "Cutoff: $cutoff\n";
echo "Comparison: '$latest' > '$cutoff' = " . ($latest > $cutoff ? 'true' : 'false') . "\n\n";

// Try with LIKE to see if format issue
$stmt = $pdo->prepare("SELECT timestamp, artist, song FROM songs WHERE timestamp LIKE ? ORDER BY timestamp DESC LIMIT 5");
$stmt->execute([$cutoff . '%']);
$results = $stmt->fetchAll(PDO::FETCH_ASSOC);

echo "Songs starting with cutoff date:\n";
foreach ($results as $row) {
    echo $row['timestamp'] . " - " . $row['artist'] . " - " . $row['song'] . "\n";
}
?>