<?php
/**
 * PHP API for RadioChecker data
 * Serves JSON data for the static frontend
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

function get_song_count() {
    if (!file_exists('radio_songs.db')) {
        return ['error' => 'Database file not found'];
    }
    try {
        $pdo = get_db_connection();
        $stmt = $pdo->query('SELECT COUNT(*) as count FROM songs');
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        return (int)($row['count'] ?? 0);
    } catch (Exception $e) {
        // Debug: list tables
        try {
            $pdo = get_db_connection();
            $stmt = $pdo->query('SELECT name FROM sqlite_master WHERE type="table"');
            $tables = $stmt->fetchAll(PDO::FETCH_COLUMN);
            return ['error' => $e->getMessage(), 'tables' => $tables];
        } catch (Exception $e2) {
            return ['error' => $e->getMessage(), 'connection_error' => $e2->getMessage()];
        }
    }
}

// Lightweight endpoint for song count polling
if (isset($_GET['song_count']) && $_GET['song_count'] == '1') {
    $result = get_song_count();
    if (is_array($result)) {
        echo json_encode($result);
    } else {
        echo json_encode(['count' => $result]);
    }
    exit;
}

// Database path - adjust as needed
$db_path = 'static_web/radio_songs.db';

function get_db_connection() {
    global $db_path;
    try {
        return new PDO('sqlite:' . $db_path);
    } catch (PDOException $e) {
        die(json_encode(['error' => 'Database connection failed']));
    }
}

function parse_iso_timestamp($ts_str) {
    try {
        return new DateTime($ts_str);
    } catch (Exception $e) {
        return null;
    }
}

function get_setting($key, $default = null) {
    try {
        $pdo = get_db_connection();
        $stmt = $pdo->prepare("SELECT value FROM settings WHERE key = ?");
        $stmt->execute([$key]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if ($row) {
            return json_decode($row['value'], true);
        }
        return $default;
    } catch (Exception $e) {
        return $default;
    }
}

function chart_data() {
    $pdo = get_db_connection();
    
    // Songs per station (top 5)
    $stmt = $pdo->query("
        SELECT station, COUNT(*) as count 
        FROM songs 
        GROUP BY station 
        ORDER BY count DESC 
        LIMIT 5
    ");
    $stations_data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Top songs (top 5)
    $stmt = $pdo->query("
        SELECT song, COUNT(*) as count 
        FROM songs 
        GROUP BY song 
        ORDER BY count DESC 
        LIMIT 5
    ");
    $songs_data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Songs by hour of day
    $stmt = $pdo->query("SELECT timestamp FROM songs");
    $all_songs = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    $hours = array_fill(0, 24, 0);
    $days_of_week = array_fill(0, 7, 0);
    $days_count = [];
    
    foreach ($all_songs as $timestamp) {
        $ts = parse_iso_timestamp($timestamp);
        if ($ts) {
            $hour = (int)$ts->format('H');
            $weekday = (int)$ts->format('w');
            $hours[$hour] += 1;
            $days_of_week[$weekday] += 1;
            $date_key = $ts->format('Y-m-d');
            $days_count[$date_key] = ($days_count[$date_key] ?? 0) + 1;
        }
    }
    
    // Get last 14 days
    krsort($days_count);
    $sorted_days = array_slice($days_count, 0, 14, true);
    ksort($sorted_days);
    
    $day_names = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'];
    
    return [
        'stations' => [
            'labels' => array_column($stations_data, 'station'),
            'data' => array_column($stations_data, 'count')
        ],
        'songs' => [
            'labels' => array_column($songs_data, 'song'),
            'data' => array_column($songs_data, 'count')
        ],
        'hours' => [
            'labels' => array_map(fn($h) => sprintf('%02d:00', $h), range(0, 23)),
            'data' => $hours
        ],
        'weekdays' => [
            'labels' => $day_names,
            'data' => $days_of_week
        ],
        'timeline' => [
            'labels' => array_keys($sorted_days),
            'data' => array_values($sorted_days)
        ]
    ];
}

function now_playing() {
    $pdo = get_db_connection();
    
    // Get target artists
    $target_artists = get_setting('target_artists', []);
    
    if (empty($target_artists)) {
        return ['success' => true, 'playing' => []];
    }
    
    // Get songs detected in last 10 minutes - most recent per station
    $cutoff_time = (new DateTime())->modify('-10 minutes')->format('Y-m-d\TH:i:s');
    
    // Get all stations that have songs in the last 10 minutes
    $stmt = $pdo->prepare("SELECT DISTINCT station FROM songs WHERE timestamp > ?");
    $stmt->execute([$cutoff_time]);
    $stations = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    // Get the most recent song for each station
    $now_playing_list = [];
    foreach ($stations as $station) {
        $stmt = $pdo->prepare("
            SELECT station, artist, song, timestamp
            FROM songs
            WHERE station = ? AND timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 1
        ");
        $stmt->execute([$station, $cutoff_time]);
        
        $song_data = $stmt->fetch(PDO::FETCH_ASSOC);
        if ($song_data && in_array($song_data['artist'], $target_artists)) {
            $ts = parse_iso_timestamp($song_data['timestamp']);
            if ($ts) {
                $time_ago = (new DateTime())->getTimestamp() - $ts->getTimestamp();
                $minutes_ago = (int)($time_ago / 60);
                if ($minutes_ago == 0) {
                    $time_ago_str = 'Just now';
                } elseif ($minutes_ago == 1) {
                    $time_ago_str = '1 min ago';
                } else {
                    $time_ago_str = $minutes_ago . ' mins ago';
                }
            } else {
                $time_ago_str = 'Recently';
            }
            
            $now_playing_list[] = [
                'station' => $song_data['station'],
                'artist' => $song_data['artist'],
                'song' => $song_data['song'],
                'time_ago' => $time_ago_str,
                'timestamp' => $song_data['timestamp'] // Keep for sorting
            ];
        }
    }
    
    // Sort by timestamp (most recent first)
    usort($now_playing_list, function($a, $b) {
        return strcmp($b['timestamp'], $a['timestamp']);
    });
    
    // Remove timestamp from output
    foreach ($now_playing_list as &$item) {
        unset($item['timestamp']);
    }
    
    return [
        'success' => true,
        'playing' => $now_playing_list
    ];
}

function station_data($station_name) {
    $pdo = get_db_connection();
    
    // Get all songs from station
    $stmt = $pdo->prepare("SELECT * FROM songs WHERE station = ? ORDER BY timestamp DESC");
    $stmt->execute([$station_name]);
    $songs = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    $total_songs = count($songs);
    
    // Unique artists
    $stmt = $pdo->prepare("SELECT DISTINCT artist FROM songs WHERE station = ? ORDER BY artist");
    $stmt->execute([$station_name]);
    $artists = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    // Unique songs
    $stmt = $pdo->prepare("SELECT DISTINCT song FROM songs WHERE station = ? ORDER BY song");
    $stmt->execute([$station_name]);
    $song_titles = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    // Format songs
    $songs_data = [];
    foreach ($songs as $song) {
        $ts = parse_iso_timestamp($song['timestamp']);
        $ts_formatted = $ts ? $ts->format('d M Y at H:i') : $song['timestamp'];
        $songs_data[] = [
            'station' => $song['station'],
            'artist' => $song['artist'],
            'song' => $song['song'],
            'timestamp' => $ts_formatted,
            'timestamp_raw' => $song['timestamp']
        ];
    }
    
    return [
        'station_name' => $station_name,
        'total_songs' => $total_songs,
        'artists' => $artists,
        'song_titles' => $song_titles,
        'songs' => $songs_data
    ];
}

function station_charts($station_name) {
    $pdo = get_db_connection();
    
    // Songs by hour and weekday for this station
    $stmt = $pdo->prepare("SELECT timestamp FROM songs WHERE station = ?");
    $stmt->execute([$station_name]);
    $songs = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    $hours = array_fill(0, 24, 0);
    $weekdays = array_fill(0, 7, 0);
    $days_count = [];
    
    foreach ($songs as $timestamp) {
        $ts = parse_iso_timestamp($timestamp);
        if ($ts) {
            $hours[(int)$ts->format('H')] += 1;
            $weekdays[(int)$ts->format('w')] += 1;
            $date_key = $ts->format('Y-m-d');
            $days_count[$date_key] = ($days_count[$date_key] ?? 0) + 1;
        }
    }
    
    // Get last 14 days for this station
    krsort($days_count);
    $sorted_days = array_slice($days_count, 0, 14, true);
    ksort($sorted_days);
    
    // Top songs for this station
    $stmt = $pdo->prepare("
        SELECT song, COUNT(*) as count
        FROM songs
        WHERE station = ?
        GROUP BY song
        ORDER BY count DESC
        LIMIT 10
    ");
    $stmt->execute([$station_name]);
    $top_songs = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    $day_names = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'];
    
    return [
        'hours' => [
            'labels' => array_map(fn($h) => sprintf('%02d:00', $h), range(0, 23)),
            'data' => $hours
        ],
        'weekdays' => [
            'labels' => $day_names,
            'data' => $weekdays
        ],
        'top_songs' => [
            'labels' => array_column($top_songs, 'song'),
            'data' => array_column($top_songs, 'count')
        ],
        'timeline' => [
            'labels' => array_keys($sorted_days),
            'data' => array_values($sorted_days)
        ]
    ];
}

function index_data() {
    $pdo = get_db_connection();
    
    // Get all songs (limit 1000)
    $stmt = $pdo->query("SELECT * FROM songs ORDER BY timestamp DESC LIMIT 1000");
    $songs = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Get first and last timestamps
    $stmt = $pdo->query("SELECT MIN(timestamp), MAX(timestamp) FROM songs");
    $ts_row = $stmt->fetch(PDO::FETCH_NUM);
    $first_ts = $ts_row[0];
    $last_ts = $ts_row[1];
    
    $first_timestamp = null;
    $last_timestamp = null;
    if ($first_ts) {
        $ts = parse_iso_timestamp($first_ts);
        $first_timestamp = $ts ? $ts->format('D M j H:i:s Y') : $first_ts;
    }
    if ($last_ts) {
        $ts = parse_iso_timestamp($last_ts);
        $last_timestamp = $ts ? $ts->format('d M Y at H:i') : $last_ts;
    }
    
    // Get unique stations
    $stmt = $pdo->query("SELECT DISTINCT station FROM songs ORDER BY station");
    $stations = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    // Get unique song titles
    $stmt = $pdo->query("SELECT DISTINCT song FROM songs ORDER BY song");
    $song_titles = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    // Get target artists
    $target_artists = get_setting('target_artists', []);
    
    // Get today's count
    $today = (new DateTime())->format('Y-m-d');
    $stmt = $pdo->prepare("SELECT COUNT(*) FROM songs WHERE DATE(timestamp) = ?");
    $stmt->execute([$today]);
    $today_count = $stmt->fetchColumn();
    
    // Format songs
    $songs_data = [];
    foreach ($songs as $song) {
        $ts = parse_iso_timestamp($song['timestamp']);
        $ts_formatted = $ts ? $ts->format('d M Y at H:i') : $song['timestamp'];
        $songs_data[] = [
            'station' => $song['station'],
            'artist' => $song['artist'],
            'song' => $song['song'],
            'timestamp' => $ts_formatted,
            'timestamp_raw' => $song['timestamp']
        ];
    }
    
    return [
        'songs' => $songs_data,
        'stations' => $stations,
        'song_titles' => $song_titles,
        'target_artists' => $target_artists,
        'total_count' => count($songs_data),
        'today_count' => $today_count,
        'first_timestamp' => $first_timestamp,
        'last_timestamp' => $last_timestamp
    ];
}

function export_csv() {
    $pdo = get_db_connection();
    $stmt = $pdo->query("SELECT station, artist, song, timestamp FROM songs ORDER BY timestamp DESC");
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Set headers for CSV download
    header('Content-Type: text/csv');
    header('Content-Disposition: attachment; filename="radio_songs.csv"');
    
    // Output CSV
    $output = fopen('php://output', 'w');
    fputcsv($output, ['Station', 'Artist', 'Song', 'Detected At']);
    foreach ($rows as $row) {
        fputcsv($output, $row);
    }
    fclose($output);
    exit;
}

function artist_data($artist_name) {
    $pdo = get_db_connection();
    
    // Get all songs by artist
    $stmt = $pdo->prepare("SELECT * FROM songs WHERE artist = ? ORDER BY timestamp DESC");
    $stmt->execute([$artist_name]);
    $songs = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    $total_songs = count($songs);
    
    // Unique stations
    $stmt = $pdo->prepare("SELECT DISTINCT station FROM songs WHERE artist = ? ORDER BY station");
    $stmt->execute([$artist_name]);
    $stations = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    // Unique songs
    $stmt = $pdo->prepare("SELECT DISTINCT song FROM songs WHERE artist = ? ORDER BY song");
    $stmt->execute([$artist_name]);
    $song_titles = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    // Format songs
    $songs_data = [];
    foreach ($songs as $song) {
        $ts = parse_iso_timestamp($song['timestamp']);
        $ts_formatted = $ts ? $ts->format('d M Y at H:i') : $song['timestamp'];
        $songs_data[] = [
            'station' => $song['station'],
            'artist' => $song['artist'],
            'song' => $song['song'],
            'timestamp' => $ts_formatted,
            'timestamp_raw' => $song['timestamp']
        ];
    }
    
    return [
        'artist_name' => $artist_name,
        'total_detections' => $total_songs,
        'stations' => $stations,
        'song_titles' => $song_titles,
        'songs' => $songs_data
    ];
}

function artist_charts($artist_name) {
    $pdo = get_db_connection();
    
    // Songs by hour and weekday for this artist
    $stmt = $pdo->prepare("SELECT timestamp FROM songs WHERE artist = ?");
    $stmt->execute([$artist_name]);
    $songs = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    $hours = array_fill(0, 24, 0);
    $weekdays = array_fill(0, 7, 0);
    foreach ($songs as $timestamp) {
        $ts = parse_iso_timestamp($timestamp);
        if ($ts) {
            $hours[(int)$ts->format('H')] += 1;
            $weekdays[(int)$ts->format('w')] += 1;
        }
    }
    
    // Top songs for this artist
    $stmt = $pdo->prepare("
        SELECT song, COUNT(*) as count
        FROM songs
        WHERE artist = ?
        GROUP BY song
        ORDER BY count DESC
        LIMIT 10
    ");
    $stmt->execute([$artist_name]);
    $top_songs = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    $day_names = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'];
    
    return [
        'hours' => [
            'labels' => array_map(fn($h) => sprintf('%02d:00', $h), range(0, 23)),
            'data' => $hours
        ],
        'weekdays' => [
            'labels' => $day_names,
            'data' => $weekdays
        ],
        'top_songs' => [
            'labels' => array_column($top_songs, 'song'),
            'data' => array_column($top_songs, 'count')
        ]
    ];
}

function song_data($song_name) {
    $pdo = get_db_connection();
    
    // Get all detections of this song
    $stmt = $pdo->prepare("SELECT * FROM songs WHERE song = ? ORDER BY timestamp DESC");
    $stmt->execute([$song_name]);
    $songs = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    
    $total_detections = count($songs);
    
    $today = (new DateTime())->format('Y-m-d');
    $stmt = $pdo->prepare("SELECT COUNT(*) FROM songs WHERE DATE(timestamp) = ?");
    $stmt->execute([$today]);
    $today_count = $stmt->fetchColumn();

    // Unique stations
    $stmt = $pdo->prepare("SELECT DISTINCT station FROM songs WHERE song = ? ORDER BY station");
    $stmt->execute([$song_name]);
    $stations = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    // Unique artists (usually just one, but could be multiple)
    $stmt = $pdo->prepare("SELECT DISTINCT artist FROM songs WHERE song = ? ORDER BY artist");
    $stmt->execute([$song_name]);
    $artists = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    // Format songs
    $songs_data = [];
    foreach ($songs as $song) {
        $ts = parse_iso_timestamp($song['timestamp']);
        $ts_formatted = $ts ? $ts->format('d M Y at H:i') : $song['timestamp'];
        $songs_data[] = [
            'station' => $song['station'],
            'artist' => $song['artist'],
            'song' => $song['song'],
            'timestamp' => $ts_formatted,
            'timestamp_raw' => $song['timestamp']
        ];
    }
    
    return [
        'song_name' => $song_name,
        'total_detections' => $total_detections,
        'stations' => $stations,
        'artists' => $artists,
        'songs' => $songs_data,
        'today_count' => $today_count
    ];
}

function song_charts($song_name) {
    $pdo = get_db_connection();
    
    // Detections by hour and weekday for this song
    $stmt = $pdo->prepare("SELECT timestamp FROM songs WHERE song = ?");
    $stmt->execute([$song_name]);
    $songs = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    $hours = array_fill(0, 24, 0);
    $weekdays = array_fill(0, 7, 0);
    $days_count = [];
    
    foreach ($songs as $timestamp) {
        $ts = parse_iso_timestamp($timestamp);
        if ($ts) {
            $hours[(int)$ts->format('H')] += 1;
            $weekdays[(int)$ts->format('w')] += 1;
            $date_key = $ts->format('Y-m-d');
            $days_count[$date_key] = ($days_count[$date_key] ?? 0) + 1;
        }
    }
    
    // Get last 14 days for this song
    krsort($days_count);
    $sorted_days = array_slice($days_count, 0, 14, true);
    ksort($sorted_days);
    
    // Stations that play this song
    $stmt = $pdo->prepare("
        SELECT station, COUNT(*) as count
        FROM songs
        WHERE song = ?
        GROUP BY station
        ORDER BY count DESC
        LIMIT 10
    ");
    $stmt->execute([$song_name]);
    $stations_data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    $day_names = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'];
    
    return [
        'hours' => [
            'labels' => array_map(fn($h) => sprintf('%02d:00', $h), range(0, 23)),
            'data' => $hours
        ],
        'weekdays' => [
            'labels' => $day_names,
            'data' => $weekdays
        ],
        'stations' => [
            'labels' => array_column($stations_data, 'station'),
            'data' => array_column($stations_data, 'count')
        ],
        'timeline' => [
            'labels' => array_keys($sorted_days),
            'data' => array_values($sorted_days)
        ]
    ];
}

// Route handling
$request_uri = $_SERVER['REQUEST_URI'] ?? '';
if (preg_match('#/api\.php/api/([^/]+)(?:/(.+))?#', $request_uri, $matches)) {
    $endpoint = $matches[1];
    $action = $matches[2] ?? '';
    
    switch ($endpoint) {
        case 'chart-data':
            echo json_encode(chart_data());
            break;
        case 'now-playing':
            echo json_encode(now_playing());
            break;
        case 'index-data':
            echo json_encode(index_data());
            break;
        case 'export':
            export_csv();
            break;
        case 'station':
            $station_name = urldecode($action);
            if (preg_match('#^([^/]+)(?:/(.+))?$#', $action, $sub_matches)) {
                $station_name = urldecode($sub_matches[1]);
                $sub_action = $sub_matches[2] ?? '';
                if ($sub_action === 'charts') {
                    echo json_encode(station_charts($station_name));
                } elseif ($sub_action === 'data') {
                    echo json_encode(station_data($station_name));
                } else {
                    echo json_encode(['error' => 'Invalid station endpoint']);
                }
            } else {
                echo json_encode(['error' => 'Invalid station endpoint']);
            }
            break;
        case 'artist':
            $artist_name = urldecode($action);
            if (preg_match('#^([^/]+)(?:/(.+))?$#', $action, $sub_matches)) {
                $artist_name = urldecode($sub_matches[1]);
                $sub_action = $sub_matches[2] ?? '';
                if ($sub_action === 'charts') {
                    echo json_encode(artist_charts($artist_name));
                } elseif ($sub_action === 'data') {
                    echo json_encode(artist_data($artist_name));
                } else {
                    echo json_encode(['error' => 'Invalid artist endpoint']);
                }
            } else {
                echo json_encode(['error' => 'Invalid artist endpoint']);
            }
            break;
        case 'song':
            $song_name = urldecode($action);
            if (preg_match('#^([^/]+)(?:/(.+))?$#', $action, $sub_matches)) {
                $song_name = urldecode($sub_matches[1]);
                $sub_action = $sub_matches[2] ?? '';
                if ($sub_action === 'charts') {
                    echo json_encode(song_charts($song_name));
                } elseif ($sub_action === 'data') {
                    echo json_encode(song_data($song_name));
                } else {
                    echo json_encode(['error' => 'Invalid song endpoint']);
                }
            } else {
                echo json_encode(['error' => 'Invalid song endpoint']);
            }
            break;
        default:
            echo json_encode(['error' => 'Endpoint not found']);
            break;
    }
    exit;
}

echo json_encode(['error' => 'Endpoint not found']);
?>
