<?php
/**
 * PHP API for RadioChecker data
 * Serves JSON data for the static frontend
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

// absolute path to the SQLite DB (ensure PHP uses the same file you inspect locally)
$db_path = 'radio_songs.db';

function get_song_count() {
    global $db_path;

    if (empty($db_path)) {
        return ['error' => 'db_path not set'];
    }

    $exists = file_exists($db_path);
    $info = ['db_path' => $db_path, 'exists' => $exists];
    if ($exists) {
        $info['realpath'] = realpath($db_path) ?: null;
        $info['size'] = filesize($db_path);
        $info['mtime'] = date('c', filemtime($db_path));
    }

    try {
        $pdo = get_db_connection();

        // confirm songs table exists
        $check = $pdo->query("SELECT name FROM sqlite_master WHERE type='table' AND name='songs'");
        $hasSongs = (bool)$check->fetchColumn();
        if (!$hasSongs) {
            // include available tables for debugging
            $stmt = $pdo->query("SELECT name FROM sqlite_master WHERE type='table'");
            $tables = $stmt->fetchAll(PDO::FETCH_COLUMN);
            return array_merge(['error' => 'no such table: songs', 'tables' => $tables], $info);
        }

        $stmt = $pdo->query('SELECT COUNT(*) as count FROM songs');
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        return (int)($row['count'] ?? 0);
    } catch (Exception $e) {
        // try to list tables if possible
        try {
            $pdo = get_db_connection();
            $stmt = $pdo->query('SELECT name FROM sqlite_master WHERE type="table"');
            $tables = $stmt->fetchAll(PDO::FETCH_COLUMN);
            return array_merge(['error' => $e->getMessage(), 'tables' => $tables], $info);
        } catch (Exception $e2) {
            return array_merge(['error' => $e->getMessage(), 'connection_error' => $e2->getMessage()], $info);
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

// DB health/info endpoint (for debugging)
if (isset($_GET['db_info']) && $_GET['db_info'] == '1') {
    $dbInfo = ['db_path' => $db_path, 'exists' => file_exists($db_path)];
    if ($dbInfo['exists']) {
        $dbInfo['realpath'] = realpath($db_path);
        $dbInfo['size'] = filesize($db_path);
        $dbInfo['mtime'] = date('c', filemtime($db_path));
        try {
            $pdo = get_db_connection();
            $stmt = $pdo->query("SELECT name FROM sqlite_master WHERE type='table'");
            $dbInfo['tables'] = $stmt->fetchAll(PDO::FETCH_COLUMN);
        } catch (Exception $e) {
            $dbInfo['db_error'] = $e->getMessage();
        }
    }
    echo json_encode($dbInfo);
    exit;
}

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
            $weekday = ((int)$ts->format('N')) - 1;
            $hours[$hour] += 1;
            $days_of_week[$weekday] += 1;
            $date_key = $ts->format('Y-m-d');
            $days_count[$date_key] = ($days_count[$date_key] ?? 0) + 1;
        }
    }
    // Count how many distinct dates we have for each weekday so we can compute averages
    $distinct_dates_per_weekday = array_fill(0, 7, 0);
    foreach (array_keys($days_count) as $date_key) {
        $dt = DateTime::createFromFormat('Y-m-d', $date_key);
        if ($dt) {
            $wd = ((int)$dt->format('N')) - 1;
            $distinct_dates_per_weekday[$wd] += 1;
        }
    }

    // Compute average songs per weekday (total songs on that weekday / number of that weekday dates)
    $average_weekdays = array_fill(0, 7, 0);
    for ($i = 0; $i < 7; $i++) {
        if ($distinct_dates_per_weekday[$i] > 0) {
            $average_weekdays[$i] = $days_of_week[$i] / $distinct_dates_per_weekday[$i];
        } else {
            $average_weekdays[$i] = 0;
        }
    }
    // Compute average songs per hour (total songs in each hour / number of distinct dates observed)
    $num_days = max(1, count($days_count));
    $average_hours = array_fill(0, 24, 0);
    for ($h = 0; $h < 24; $h++) {
        $average_hours[$h] = $hours[$h] / $num_days;
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
            'data' => $average_hours
        ],
        'weekdays' => [
            'labels' => $day_names,
            'data' => $average_weekdays
        ],
        'timeline' => [
            'labels' => array_map(function($d) {
                $dt = DateTime::createFromFormat('Y-m-d', $d);
                return $dt ? strtolower($dt->format('j M')) : $d;
            }, array_keys($sorted_days)),
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
    
    // Get first and last timestamps (full-table)
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
        'songs' => $songs_data,
        'first_timestamp' => $first_timestamp,
        'last_timestamp' => $last_timestamp
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
            $weekdays[((int)$ts->format('N')) - 1] += 1;
            $date_key = $ts->format('Y-m-d');
            $days_count[$date_key] = ($days_count[$date_key] ?? 0) + 1;
        }
    }
    // Count distinct dates per weekday to compute averages
    $distinct_dates_per_weekday = array_fill(0, 7, 0);
    foreach (array_keys($days_count) as $date_key) {
        $dt = DateTime::createFromFormat('Y-m-d', $date_key);
        if ($dt) {
            $wd = ((int)$dt->format('N')) - 1;
            $distinct_dates_per_weekday[$wd] += 1;
        }
    }

    $average_weekdays = array_fill(0, 7, 0);
    for ($i = 0; $i < 7; $i++) {
        if ($distinct_dates_per_weekday[$i] > 0) {
            $average_weekdays[$i] = $weekdays[$i] / $distinct_dates_per_weekday[$i];
        } else {
            $average_weekdays[$i] = 0;
        }
    }
    // Compute average songs per hour (total songs in each hour / number of distinct dates observed)
    $num_days = max(1, count($days_count));
    $average_hours = array_fill(0, 24, 0);
    for ($h = 0; $h < 24; $h++) {
        $average_hours[$h] = $hours[$h] / $num_days;
    }

    // Compute average songs per hour (total songs in each hour / number of distinct dates observed)
    $num_days = max(1, count($days_count));
    $average_hours = array_fill(0, 24, 0);
    for ($h = 0; $h < 24; $h++) {
        $average_hours[$h] = $hours[$h] / $num_days;
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
            'data' => $average_hours
        ],
        'weekdays' => [
            'labels' => $day_names,
            'data' => $average_weekdays
        ],
        'top_songs' => [
            'labels' => array_column($top_songs, 'song'),
            'data' => array_column($top_songs, 'count')
        ],
        'timeline' => [
            'labels' => array_map(function($d) {
                $dt = DateTime::createFromFormat('Y-m-d', $d);
                return $dt ? strtolower($dt->format('j M')) : $d;
            }, array_keys($sorted_days)),
            'data' => array_values($sorted_days)
        ]
    ];
}

function index_data() {
    $pdo = get_db_connection();
    
    // Get all songs for listing
    $stmt = $pdo->query("SELECT * FROM songs ORDER BY timestamp DESC");
    $songs = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Get first and last timestamps (full-table)
    $stmt = $pdo->query("SELECT MIN(timestamp), MAX(timestamp) FROM songs");
    $ts_row = $stmt->fetch(PDO::FETCH_NUM);
    $first_ts = $ts_row[0];
    $last_ts = $ts_row[1];
    
    // Calculate total hours between first and last timestamp (rounded to whole hours)
    $hours_between = null;
    if ($first_ts && $last_ts) {
        $dt_first = parse_iso_timestamp($first_ts);
        $dt_last = parse_iso_timestamp($last_ts);
        if ($dt_first && $dt_last) {
            $diff_seconds = $dt_last->getTimestamp() - $dt_first->getTimestamp();
            $hours_between = (int)round($diff_seconds / 3600);
        }
    }
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
    
    // --- Calculate largest gap between consecutive song detections ---
    // We fetch all timestamps ordered ASC and compute the biggest interval between adjacent rows.
    $largest_gap_seconds = 0;
    $gap_start_ts = null;
    $gap_end_ts = null;
    $gap_end_song = null;
    $gap_end_station = null;

    try {
        $stmt = $pdo->query("SELECT timestamp, song, station FROM songs ORDER BY timestamp ASC");
        $all_timestamps = $stmt->fetchAll(PDO::FETCH_ASSOC);

        $prev_epoch = null;
        $prev_iso = null;
        foreach ($all_timestamps as $iso) {
            $dt = parse_iso_timestamp($iso['timestamp'] ?? null);
            if (!$dt) continue;
            $epoch = $dt->getTimestamp();
            if ($prev_epoch !== null && is_array($prev_iso)) {
                $diff = $epoch - $prev_epoch;
                if ($diff > $largest_gap_seconds) {
                    $largest_gap_seconds = $diff;
                    $gap_start_ts = $prev_iso['timestamp'] ?? null;
                    $gap_end_ts = $iso['timestamp'] ?? null;
                    $gap_end_song = $iso['song'] ?? null;
                    $gap_end_station = $iso['station'] ?? null;
                }
            }
            $prev_epoch = $epoch;
            $prev_iso = $iso;
        }
    } catch (Exception $e) {
        // leave defaults if query fails
    }

    // Helper to format interval in a human-friendly way
    $format_interval = function(int $s) {
        if ($s <= 0) return '0s';
        $days = intdiv($s, 86400);
        $hours = intdiv($s % 86400, 3600);
        $mins = intdiv($s % 3600, 60);
        $secs = $s % 60;
        if ($days > 0) return sprintf('%d dagen, %d uur en %d minuten', $days, $hours, $mins);
        if ($hours > 0) return sprintf('%d uur en %d minuten', $hours, $mins);
        if ($mins > 0) return sprintf('%d minuten en %d seconden', $mins, $secs);
        return sprintf('%d seconden', $secs);
    };

    $largest_gap = null;
    if ($largest_gap_seconds > 0 && $gap_end_ts) {
        $gap_day = null;
        $end_dt = parse_iso_timestamp($gap_end_ts);
        if ($end_dt) {
            // attach the gap to the later song's date (user preference)
            $gap_day = $end_dt->format('Y-m-d');
        }

        $largest_gap = [
            'seconds' => $largest_gap_seconds,
            'readable' => $format_interval($largest_gap_seconds),
            'start_timestamp' => $gap_start_ts,
            'end_timestamp' => $gap_end_ts,
            'end_song' => $gap_end_song,
            'end_station' => $gap_end_station,
            'date' => $gap_day
        ];
    } else {
        $largest_gap = [
            'seconds' => 0,
            'readable' => '0s',
            'start_timestamp' => null,
            'end_timestamp' => null,
            'date' => null
        ];
    }
    // ---------------------------------------------------------------
    
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

    // get day with the most songs
    $stmt = $pdo->query("SELECT DATE(timestamp) as day, COUNT(*) as count FROM songs GROUP BY day ORDER BY count DESC LIMIT 1");
    $most_songs_day = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($most_songs_day && isset($most_songs_day['day'])) {
        $date = new DateTime($most_songs_day['day']);
        $most_songs_day['day'] = $date->format('d M Y');
    }

    
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
        'average_per_hour' => $hours_between > 0 ? round(count($songs_data) / $hours_between, 2) : null,
        'today_count' => $today_count,
        'hours_between' => $hours_between,
        'first_timestamp' => $first_timestamp,
        'last_timestamp' => $last_timestamp,
        'largest_gap' => $largest_gap,
        'most_songs_day' => $most_songs_day
    ];
}

function export_csv() {
    $pdo = get_db_connection();
    $stmt = $pdo->query("SELECT station, artist, song, timestamp FROM songs ORDER BY timestamp DESC");
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Set headers for CSV download

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
    
    // Get first and last timestamps (full-table)
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
        'today_count' => $today_count,
        'first_timestamp' => $first_timestamp,
        'last_timestamp' => $last_timestamp
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
            $weekdays[((int)$ts->format('N')) - 1] += 1;
            $date_key = $ts->format('Y-m-d');
            $days_count[$date_key] = ($days_count[$date_key] ?? 0) + 1;
        }
    }
    // Count distinct dates per weekday to compute averages
    $distinct_dates_per_weekday = array_fill(0, 7, 0);
    foreach (array_keys($days_count) as $date_key) {
        $dt = DateTime::createFromFormat('Y-m-d', $date_key);
        if ($dt) {
            $wd = ((int)$dt->format('N')) - 1;
            $distinct_dates_per_weekday[$wd] += 1;
        }
    }

    $average_weekdays = array_fill(0, 7, 0);
    for ($i = 0; $i < 7; $i++) {
        if ($distinct_dates_per_weekday[$i] > 0) {
            $average_weekdays[$i] = $weekdays[$i] / $distinct_dates_per_weekday[$i];
        } else {
            $average_weekdays[$i] = 0;
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
            'data' => $average_weekdays
        ],
        'stations' => [
            'labels' => array_column($stations_data, 'station'),
            'data' => array_column($stations_data, 'count')
        ],
        'timeline' => [
            'labels' => array_map(function($d) {
                $dt = DateTime::createFromFormat('Y-m-d', $d);
                return $dt ? strtolower($dt->format('j M')) : $d;
            }, array_keys($sorted_days)),
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