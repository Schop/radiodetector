<?php
// Server-side figures: crawlers (and AI search engines) that don't run JavaScript get real numbers
// instead of '...'. The page script below overwrites the same elements with live values.
define('RADIO_API_LIBRARY', true);
require_once __DIR__ . '/api.php';
require_once __DIR__ . '/includes/seo.php';
date_default_timezone_set('Europe/Amsterdam');

$seo = null;
try {
    $seo = index_data();
} catch (Throwable $e) {
    $seo = null; // keep the placeholders; the page script fills them in
}
$seo_ok = is_array($seo) && !isset($seo['error']) && !empty($seo['total_count']);

// Figures per artist, from the same rows. 'total_count' mixes Phil Collins and Genesis, so the
// descriptive text below uses these instead.
$today_key = (new DateTime('now', new DateTimeZone('Europe/Amsterdam')))->format('Y-m-d');
$pc = ['total' => 0, 'today' => 0];
$gen = ['total' => 0, 'today' => 0];
$pc_top_songs = [];
$pc_top_stations = [];
if ($seo_ok) {
    foreach ($seo['songs'] as $row) {
        $is_today = strpos($row['timestamp_raw'], $today_key) === 0;
        if (stripos($row['artist'], 'Phil Collins') === 0) {
            $pc['total']++;
            if ($is_today) $pc['today']++;
            $pc_top_songs[$row['song']] = ($pc_top_songs[$row['song']] ?? 0) + 1;
            $pc_top_stations[$row['station']] = ($pc_top_stations[$row['station']] ?? 0) + 1;
        } elseif (strcasecmp($row['artist'], 'Genesis') === 0) {
            $gen['total']++;
            if ($is_today) $gen['today']++;
        }
    }
    arsort($pc_top_songs);
    arsort($pc_top_stations);
}

$page_title = 'Phil Collins Detector | Live Radio Statistieken & Hits';
$page_description = 'Hoe vaak is Phil Collins nu op de radio? Bekijk real-time statistieken, recente detecties en de meest gedraaide Genesis hits op Nederlandse radiozenders.';
if ($seo_ok && $pc['total'] > 0) {
    $page_description = sprintf(
        'Phil Collins is al %s keer gedetecteerd op de Nederlandse radio, vandaag %d keer. Bekijk real-time statistieken, recente detecties en de meest gedraaide Genesis hits.',
        number_format($pc['total'], 0, ',', '.'), $pc['today']
    );
}
include 'includes/head.html';
?>

<body>
    <div class="container-fluid">
        <main>
            <?php include 'includes/nav.html'; ?>
        <div class="row mb-4">
            <div class="col-md-9 d-flex align-items-center gap-3">
                <img src="/static/images/phil.png" alt="Phil Collins" class="d-none d-md-block" style="max-height: 8em; height: auto; width: auto; border-radius: 8px; object-fit: cover; box-shadow: 0 2px 6px rgba(0,0,0,0.2);">
                <div class="">
                    <h1>Phil Collins Detector</h1>
                    <h3 class="">hoe vaak hoor je Phil Collins op de Nederlandse radio?</h3>
                </div>
            </div>
            <div class="col-md-3">
                
            </div>
        </div>
        <div class="row mb-4">
            <div class="col-md-4 mb-2">
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-title"><i class="bi bi-broadcast"></i> Nu op de radio</h6>
                        <div id="nowPlayingContent">
                            <div class="text-center text-muted py-3">
                                <div class="spinner-border spinner-border-sm" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <small class="d-block mt-2">radiostations checken...</small>
                            </div>
                        </div>
                        <p>Gemiddeld worden er per uur <strong id="averagePerHour"><?php echo $seo_ok && $seo['average_per_hour'] !== null ? h(str_replace('.', ',', (string)$seo['average_per_hour'])) : '...'; ?></strong>
                           nummers van Phil Collins gedetecteerd op de Nederlandse radiozenders.</p>
                        <p>Phil was <strong id="lastSongMinutesAgo"><?php $m = $seo_ok && !empty($seo['songs']) ? minutes_since($seo['songs'][0]['timestamp_raw']) : null; echo $m !== null ? $m : '...'; ?></strong> minuten geleden nog op de radio bij <span id="lastSongStation"><?php echo $seo_ok && !empty($seo['songs']) ? seo_link(station_href($seo['songs'][0]['station']), $seo['songs'][0]['station']) : '...'; ?></span> met het nummer <span id="lastSongTitle"><?php echo $seo_ok && !empty($seo['songs']) ? seo_link(song_href($seo['songs'][0]['song']), $seo['songs'][0]['song']) : '...'; ?></span>.</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-2">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h6 class="card-title mb-0">Trend</h6>
                            <div class="btn-group btn-group-sm" role="group" aria-label="Tijdsbereik">
                                <button type="button" class="btn btn-outline-primary" data-range="7">7d</button>
                                <button type="button" class="btn btn-outline-primary active" data-range="14">14d</button>
                                <button type="button" class="btn btn-outline-primary" data-range="30">30d</button>
                                <button type="button" class="btn btn-outline-primary" data-range="all">Alles</button>
                            </div>
                        </div>
                        <div style="height: 250px;">
                            <canvas id="timelineChart" width="400" height="300"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-2">
                <div class="card h-100">
                    <div class="card-body">
                        <p>Sinds <span id="firstTimestamp"><?php echo $seo_ok && !empty($seo['songs']) ? nl_date_short($seo['songs'][count($seo['songs']) - 1]['timestamp_raw']) : '...'; ?></span> is Phil Collins <strong id="totalCount"><?php echo $seo_ok ? h($seo['total_count']) : '...'; ?></strong> keer gedetecteerd,
                           op <strong id="uniqueStations"><?php echo $seo_ok ? h(count($seo['stations'])) : '...'; ?></strong> verschillende radiozenders,
                           met <strong id="uniqueSongs"><?php echo $seo_ok ? h(count($seo['song_titles'])) : '...'; ?></strong> verschillende nummers.
                        </p>
                        <p>Op de dag met de meeste detecties (<span id="mostSongsDay"><?php echo $seo_ok && !empty($seo['most_songs_day']['day_iso']) ? seo_link('/day.php?date=' . rawurlencode($seo['most_songs_day']['day_iso']), $seo['most_songs_day']['day']) : '...'; ?></span>)
                           werden <strong id="mostSongsCount"><?php echo $seo_ok && !empty($seo['most_songs_day']) ? h($seo['most_songs_day']['count']) : '...'; ?></strong> nummers van Phil gedetecteerd.
                        </p>
                        <hr>
                        <p>De langste onderbreking tussen detecties was <strong id="largestGap"><?php echo $seo_ok && !empty($seo['largest_gap']['seconds']) ? h($seo['largest_gap']['readable']) : '...'; ?></strong>. Aan deze periode van rust kwam een einde toen <span id="largestGapEndStation"><?php echo $seo_ok && !empty($seo['largest_gap']['end_station']) ? seo_link(station_href($seo['largest_gap']['end_station']), $seo['largest_gap']['end_station']) : '...'; ?></span>
                           het nummer <span id="largestGapEndSong"><?php echo $seo_ok && !empty($seo['largest_gap']['end_song']) ? seo_link(song_href($seo['largest_gap']['end_song']), $seo['largest_gap']['end_song']) : '...'; ?></span>
                            draaide op <span id="largestGapEndTime"><?php echo $seo_ok && !empty($seo['largest_gap']['date']) ? seo_link('/day.php?date=' . rawurlencode($seo['largest_gap']['date']), nl_date_short($seo['largest_gap']['date'])) : '...'; ?></span>.</p>
                    </div>
                </div>
            </div>                      


        </div>

        <!-- Third Row: Top Charts -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-title">Top 5 Radiostations die Phil Collins draaien</h6>
                        <small class="text-muted">klik op de grafiek voor meer details over een zender</small>
                        <div style="height: 300px;">
                            <canvas id="stationsChart" width="400" height="300"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-title">Top 5 Nummers die het vaakst worden gedraaid</h6>
                        <small class="text-muted">klik op de grafiek voor meer details over een nummer</small>
                        <div style="height: 300px;">
                            <canvas id="songsChart" width="400" height="300"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Fourth Row: Weekday and Hours Charts -->
         
        <div class="row mb-4">
            <div class="col-md-4 mb-2">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h6 class="card-title mb-0">Recente detecties -  <a href="detections.php" class="text-danger">Bekijk hier alle detecties</a></h6>
                        </div>
                        <div id="recentDetectionsContainer" style="height: 250px; overflow-y: auto;">
                            <div class="text-center text-muted py-3">
                                <div class="spinner-border spinner-border-sm" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <small class="d-block mt-2">Loading recent detections...</small>
                            </div>
                        </div>                        
                    </div>
                </div>
            </div>    
            <div class="col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-title">Gemiddelde detecties per dag van de week</h6>
                        <div style="height: 300px;">
                            <canvas id="weekdaysChart" width="400" height="300"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-title">Gemiddelde detecties per uur van de dag</h6>
                        <div style="height: 300px;">
                            <canvas id="hoursChart" width="400" height="300"></canvas>
                        </div>
                    </div>
                </div>
            </div>
      
        </div>


        <!-- FAQ: answers are rendered on the server from the database, so search engines and AI assistants can read them -->
        <section class="row mb-4" id="veelgestelde-vragen">
            <div class="col-12">
                <div class="card">
                    <div class="card-body">
                        <h2 class="h4 mb-3">Veelgestelde vragen over Phil Collins op de radio</h2>

                        <h3 class="h6">Hoe vaak is Phil Collins op de Nederlandse radio?</h3>
                        <p><?php if ($seo_ok && $pc['total'] > 0): ?>
                            Sinds <?php echo nl_date_short($seo['songs'][count($seo['songs']) - 1]['timestamp_raw']); ?> is een nummer van Phil Collins
                            <strong><?php echo h(number_format($pc['total'], 0, ',', '.')); ?></strong> keer gedetecteerd
                            op <?php echo h(count($seo['stations'])); ?> radiozenders, gemiddeld ongeveer
                            <?php echo h(str_replace('.', ',', (string)$seo['average_per_hour'])); ?> keer per uur voor Phil Collins en Genesis samen.
                            Vandaag was dat al <strong><?php echo h($pc['today']); ?></strong> keer.
                        <?php else: ?>De cijfers worden geladen.<?php endif; ?></p>

                        <h3 class="h6">Welk radiostation draait Phil Collins het vaakst?</h3>
                        <p><?php if ($pc_top_stations): $names = array_keys($pc_top_stations); ?>
                            Dat is <?php echo seo_link(station_href($names[0]), $names[0]); ?> met
                            <strong><?php echo h(number_format($pc_top_stations[$names[0]], 0, ',', '.')); ?></strong> detecties<?php
                            if (count($names) > 1): ?>, gevolgd door <?php echo seo_link(station_href($names[1]), $names[1]); ?>
                            (<?php echo h(number_format($pc_top_stations[$names[1]], 0, ',', '.')); ?>)<?php
                            endif;
                            if (count($names) > 2): ?> en <?php echo seo_link(station_href($names[2]), $names[2]); ?>
                            (<?php echo h(number_format($pc_top_stations[$names[2]], 0, ',', '.')); ?>)<?php endif; ?>.
                        <?php else: ?>De cijfers worden geladen.<?php endif; ?></p>

                        <h3 class="h6">Wat is het meest gedraaide Phil Collins-nummer op de Nederlandse radio?</h3>
                        <p><?php if ($pc_top_songs): $titles = array_keys($pc_top_songs); ?>
                            Het meest gedraaide nummer is <?php echo seo_link(song_href($titles[0]), $titles[0]); ?> met
                            <strong><?php echo h(number_format($pc_top_songs[$titles[0]], 0, ',', '.')); ?></strong> keer<?php
                            if (count($titles) > 1): ?>, gevolgd door <?php echo seo_link(song_href($titles[1]), $titles[1]); ?>
                            (<?php echo h(number_format($pc_top_songs[$titles[1]], 0, ',', '.')); ?>)<?php endif; ?>.
                        <?php else: ?>De cijfers worden geladen.<?php endif; ?></p>

                        <h3 class="h6">Worden Genesis-nummers ook bijgehouden?</h3>
                        <p>Ja. Naast Phil Collins (inclusief duetten als &lsquo;Easy Lover&rsquo; met Philip Bailey) telt de detector ook Genesis.
                            <?php if ($seo_ok && $gen['total'] > 0): ?>Genesis is <strong><?php echo h(number_format($gen['total'], 0, ',', '.')); ?></strong> keer gedetecteerd,
                            vandaag <?php echo h($gen['today']); ?> keer.<?php endif; ?></p>

                        <h3 class="h6">Hoe werkt de Phil Collins Detector?</h3>
                        <p>Een kleine computer in een garage controleert elke minuut de &lsquo;nu aan het spelen&rsquo;-informatie van Nederlandse radiozenders
                            en legt vast wanneer er een nummer van Phil Collins of Genesis voorbijkomt. Lees meer op de pagina
                            <a href="about.php" class="text-decoration-none">Over / FAQs</a>.</p>
                    </div>
                </div>
            </div>
        </section>

        <?php
        // front page only: a quiet link to the Toto - Africa side project
        $footer_extra = '<a href="africa.php" class="ms-2" style="opacity: .5;" title="Africa - Toto"><small>en &lsquo;Africa&rsquo; van Toto dan?</small></a>';
        include 'includes/footer.html';
        ?>
        </main>
    </div>

    <script>
        //console.log('Script starting...');
        const API_BASE = '/api.php'; // Adjust this path as needed

        // ── Timeline chart with switchable range ──────────────────────────
        let timelineChart = null;
        function loadTimeline(range) {
            fetch(`${API_BASE}/api/chart-data?range=${encodeURIComponent(range)}`)
                .then(r => r.json())
                .then(chartData => {
                    if (!chartData || !chartData.timeline) {
                        console.error('Unexpected chart-data response', chartData);
                        return;
                    }
                    const timelineData = chartData.timeline.data || [];
                    // weight by observed share of each day, so outage days don't drag the average down
                    const coverage = chartData.timeline.coverage || timelineData.map(() => 1);
                    const observedDays = coverage.reduce((a, b) => a + b, 0);
                    const avg = observedDays > 0
                        ? timelineData.reduce((a, b) => a + b, 0) / observedDays
                        : 0;
                    const avgArray = Array(timelineData.length).fill(avg);
                    if (timelineChart) timelineChart.destroy();
                    timelineChart = new Chart(document.getElementById('timelineChart'), {
                        type: 'line',
                        data: {
                            labels: chartData.timeline.labels || [],
                            datasets: [
                                {
                                    label: 'Dagelijkse Detecties',
                                    data: timelineData,
                                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                                    borderColor: 'rgba(54, 162, 235, 1)',
                                    borderWidth: 2,
                                    fill: true,
                                    tension: 0.3
                                },
                                {
                                    label: 'Gemiddelde: ' + avg.toFixed(2),
                                    data: avgArray,
                                    borderColor: 'rgba(255, 99, 132, 0.8)',
                                    borderWidth: 2,
                                    borderDash: [8, 6],
                                    pointRadius: 0,
                                    fill: false,
                                    tension: 0,
                                    type: 'line',
                                    order: 1
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: { y: { beginAtZero: false, ticks: { precision: 0 } } },
                            plugins: { legend: { display: true } },
                            onHover: (event, elements) => {
                                event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                            },
                            onClick: (event, elements) => {
                                if (elements.length > 0 && chartData.timeline.dates) {
                                    const isoDate = chartData.timeline.dates[elements[0].index];
                                    if (isoDate) window.location.href = `/day.php?date=${encodeURIComponent(isoDate)}`;
                                }
                            }
                        }
                    });
                })
                .catch(err => console.error('Failed to load timeline data:', err));
        }

        document.querySelectorAll('[data-range]').forEach(btn => {
            btn.addEventListener('click', e => {
                document.querySelectorAll('[data-range]').forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');
                loadTimeline(e.currentTarget.dataset.range);
            });
        });

        loadTimeline('14');
        // ─────────────────────────────────────────────────────────────────

        // Load index data
        // console.log('Starting to load index data...');
        fetch(`${API_BASE}/api/index-data`)
            .then(response => {
                // console.log('Fetch response received:', response);
                return response.json();
            })
            .then(data => {
                // console.log('Data received:', data);
                // Update stats
                document.getElementById('totalCount').textContent = data.total_count;
                document.getElementById('uniqueStations').textContent = data.stations.length;
                document.getElementById('uniqueSongs').textContent = data.song_titles.length;
                document.getElementById('mostSongsDay').innerHTML = data.most_songs_day && data.most_songs_day.day_iso ? `<a href="/day.php?date=${encodeURIComponent(data.most_songs_day.day_iso)}" class="text-decoration-none">${data.most_songs_day.day}</a>` : (data.most_songs_day ? data.most_songs_day.day : '...');
                document.getElementById('mostSongsCount').textContent = data.most_songs_day ? data.most_songs_day.count : '...';
                document.getElementById('averagePerHour').textContent = data.average_per_hour !== null ? data.average_per_hour : '...';
                
                // Format first timestamp as "10 feb 2026"
                const firstDate = new Date(data.first_timestamp);
                const formattedFirstDate = firstDate.toLocaleDateString('nl-NL', { 
                    day: 'numeric', 
                    month: 'short', 
                    year: 'numeric' 
                });
                document.getElementById('firstTimestamp').textContent = formattedFirstDate;
                
                document.getElementById('todayCountnav').textContent = data.today_count || '0';

                // Populate largest-gap info (if available)
                if (data.largest_gap && data.largest_gap.seconds && data.largest_gap.seconds > 0) {
                    const lg = data.largest_gap;
                    const gapDateStr = lg.date ? new Date(lg.date).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short', year: 'numeric' }) : (lg.date || '');
                    document.getElementById('largestGap').textContent = `${lg.readable}`;
                    const stationEl = document.getElementById('largestGapEndStation');
                    const songEl = document.getElementById('largestGapEndSong');
                    if (lg.end_station) {
                        stationEl.innerHTML = `<a href="/station.php#${encodeURIComponent(lg.end_station)}" class="text-decoration-none">${lg.end_station}</a>`;
                    } else {
                        stationEl.textContent = '...';
                    }
                    if (lg.end_song) {
                        songEl.innerHTML = `<a href="/song.php#${encodeURIComponent(lg.end_song)}" class="text-decoration-none">${lg.end_song}</a>`;
                    } else {
                        songEl.textContent = '...';
                    }
                    document.getElementById('largestGapEndTime').innerHTML = lg.date ? `<a href="/day.php?date=${encodeURIComponent(lg.date)}" class="text-decoration-none">${gapDateStr}</a>` : '...';
                } else {
                    document.getElementById('largestGap').textContent = 'Geen gegevens';
                    document.getElementById('largestGapEndStation').textContent = '...';
                    document.getElementById('largestGapEndSong').textContent = '...';
                    document.getElementById('largestGapEndTime').textContent = '...';
                }

                const lastSongMinutesAgoEl = document.getElementById('lastSongMinutesAgo');
                let lastSongMinutesAgo = null;
                if (data.songs && data.songs.length > 0 && data.songs[0].timestamp_raw) {
                    const lastTimestamp = new Date(data.songs[0].timestamp_raw).getTime();
                    lastSongMinutesAgo = Math.round((Date.now() - lastTimestamp) / 60000);
                    lastSongMinutesAgoEl.textContent = lastSongMinutesAgo;
                    lastSongMinutesAgoEl.dataset.lastTimestamp = lastTimestamp;
                } else {
                    lastSongMinutesAgoEl.textContent = '...';
                    delete lastSongMinutesAgoEl.dataset.lastTimestamp;
                }
                document.getElementById('lastSongStation').innerHTML = data.songs && data.songs.length > 0 ? `<a href="/station.php#${encodeURIComponent(data.songs[0].station)}" class="text-decoration-none">${data.songs[0].station}</a>` : '...';
                document.getElementById('lastSongTitle').innerHTML = data.songs && data.songs.length > 0 ? `<a href="/song.php#${encodeURIComponent(data.songs[0].song)}" class="text-decoration-none">${data.songs[0].song}</a>` : '...';

                // Update footer
                document.getElementById('footerText').textContent = `Tracking since ${data.first_timestamp || '...'} - Version 1.0 - Data auto-refreshes every 30 seconds`;

                // Populate recent detections table (last 10 detections, no artist column)
                if (data.songs && data.songs.length > 0) {
                    const recentSongs = data.songs.slice(0, 10);
                    const recentTableHtml = `
                        <table class="table table-sm table-borderless mb-0">
                            <tbody>
                                ${recentSongs.map(song => {
                                    // Format timestamp more compactly: date + time
                                    const ts = new Date(song.timestamp_raw);
                                    const compactDate = ts.toLocaleDateString('nl-NL', { day: 'numeric', month: 'short' });
                                    const compactTime = ts.toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit', hour12: false });
                                    const isoDate = (song.timestamp_raw && song.timestamp_raw.split('T')[0]) || '';
                                    const dayHref = '/day.php?date=' + encodeURIComponent(isoDate);
                                    return `
                                    <tr style="border-bottom: 1px solid #dee2e6;">
                                        <td class="p-1" style="white-space: nowrap;">
                                            <small><a href="${dayHref}" class="text-decoration-none">${compactDate}</a>, ${compactTime}</small>
                                        </td>
                                        <td class="p-1">
                                            <small>
                                                <a href="/station.php#${encodeURIComponent(song.station)}" class="text-decoration-none">${song.station}</a> - 
                                                <a href="/song.php#${encodeURIComponent(song.song)}" class="text-decoration-none">${song.song}</a>
                                            </small>
                                        </td>
                                    </tr>
                                `}).join('')}
                            </tbody>
                        </table>
                    `;
                    document.getElementById('recentDetectionsContainer').innerHTML = recentTableHtml;

                    // Other charts (stations / songs / weekdays / hours)
                    fetch(`${API_BASE}/api/chart-data`)
                        .then(response => response.json())
                        .then(chartData => {
                            // Stations chart (doughnut)
                            new Chart(document.getElementById('stationsChart'), {
                                type: 'doughnut',
                                data: {
                                    labels: chartData.stations.labels,
                                    datasets: [{
                                        label: 'Detecties per zender',
                                        data: chartData.stations.data,
                                        backgroundColor: [
                                            'rgba(75, 192, 192, 0.8)',
                                            'rgba(54, 162, 235, 0.8)',
                                            'rgba(153, 102, 255, 0.8)',
                                            'rgba(255, 159, 64, 0.8)',
                                            'rgba(255, 99, 132, 0.8)'
                                        ],
                                        borderColor: 'rgba(255,255,255,0.8)',
                                        borderWidth: 1
                                    }]
                                },
                                options: {
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    cutout: '30%',
                                    animation: { animateRotate: true, animateScale: true },
                                    plugins: {
                                        legend: { display: true, position: 'right' }
                                    },
                                    onHover: (event, elements) => {
                                        event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                                    },
                                    onClick: (event, elements) => {
                                        if (elements.length > 0) {
                                            const index = elements[0].index;
                                            const station = chartData.stations.labels[index];
                                            window.location.href = `/station.php#${encodeURIComponent(station)}`;
                                        }
                                    }
                                }
                            });

                            // Songs chart
                            new Chart(document.getElementById('songsChart'), {
                                type: 'bar',
                                data: {
                                    labels: chartData.songs.labels,
                                    datasets: [{
                                        label: 'Detections',
                                        data: chartData.songs.data,
                                        backgroundColor: 'rgba(255, 99, 132, 0.6)',
                                        borderColor: 'rgba(255, 99, 132, 1)',
                                        borderWidth: 1
                                    }]
                                },
                                options: {
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    indexAxis: 'y',
                                    scales: { x: { beginAtZero: false, ticks: { precision: 0 } } },
                                    plugins: { legend: { display: false } },
                                    onHover: (event, elements) => {
                                        event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                                    },
                                    onClick: (event, elements) => {
                                        if (elements.length > 0) {
                                            const index = elements[0].index;
                                            const song = chartData.songs.labels[index];
                                            window.location.href = `/song.php#${encodeURIComponent(song)}`;
                                        }
                                    }
                                }
                            });

                            // Weekdays chart
                            new Chart(document.getElementById('weekdaysChart'), {
                                type: 'bar',
                                data: {
                                    labels: chartData.weekdays.labels,
                                    datasets: [{
                                        label: 'Detecties',
                                        data: chartData.weekdays.data,
                                        backgroundColor: 'rgba(153, 102, 255, 0.6)',
                                        borderColor: 'rgba(153, 102, 255, 1)',
                                        borderWidth: 1
                                    }]
                                },
                                options: {
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    scales: { y: { beginAtZero: false, ticks: { precision: 0 } } },
                                    plugins: { legend: { display: false } }
                                }
                            });

                            // Hours chart
                            new Chart(document.getElementById('hoursChart'), {
                                type: 'bar',
                                data: {
                                    labels: chartData.hours.labels,
                                    datasets: [{
                                        label: 'Detecties',
                                        data: chartData.hours.data,
                                        backgroundColor: 'rgba(255, 159, 64, 0.6)',
                                        borderColor: 'rgba(255, 159, 64, 1)',
                                        borderWidth: 1
                                    }]
                                },
                                options: {
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
                                    plugins: { legend: { display: false } }
                                }
                            });
                        })
                        .catch(err => console.error('Failed to load chart data:', err));

                } else {
                    document.getElementById('recentDetectionsContainer').innerHTML = `
                        <div class="text-center text-muted py-3">
                            <small>Geen recente detecties</small>
                        </div>
                    `;
                }
            })
            .catch(err => {
                console.error('Failed to load index data:', err);
                document.getElementById('recentDetectionsContainer').innerHTML = `
                    <div class="text-center text-muted py-3">
                        <small>Fout bij laden</small>
                    </div>
                `;
            });

        // Load and render charts
        // console.log('Loading chart data...');
        fetch(`${API_BASE}/api/chart-data`)
            .then(response => {
                // console.log('Chart response received:', response);
                return response.json();
            })
            .then(data => {
                // console.log('Chart data received:', data);
                // Charts are now initialized with index data
            })
            .catch(err => console.error('Failed to load chart data:', err));

        // Update Now Playing
        function updateNowPlaying() {
            fetch(`${API_BASE}/api/now-playing`)
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('nowPlayingContent');
                    // ...existing code...
                    if (data.success && data.playing && data.playing.length > 0) {
                        let html = '<ul class="list-group list-group-flush">';
                        data.playing.forEach(item => {
                            html += `
                                <li class="list-group-item">
                                    <div class="d-flex justify-content-between align-items-start">
                                        <div>
                                            <div class="fw-bold">${item.station}</div>
                                            <div class="text-muted small">${item.artist} - ${item.song}</div>
                                        </div>
                                        <span class="badge bg-success rounded-pill">${item.time_ago}</span>
                                    </div>
                                </li>
                            `;
                        });
                        html += '</ul>';
                        container.innerHTML = html;
                    } else {
                        container.innerHTML = `
                            <div class="text-center text-muted py-3">
                                <i class="bi bi-music-note-beamed" style="font-size: 2rem;"></i>
                                <p class="mb-0 mt-2">Heerlijk, Phil is nu even niet op de radio</p>
                            </div>
                        `;
                    }

                    // Update lastSongMinutesAgo
                    // Find the most recent Phil Collins detection (if available)
                    let lastSongTimestamp = null;
                    if (data.playing && data.playing.length > 0) {
                        // Find the most recent detection by timestamp_raw
                        let maxTimestamp = null;
                        data.playing.forEach(item => {
                            if (item.timestamp_raw) {
                                const ts = new Date(item.timestamp_raw).getTime();
                                if (!maxTimestamp || ts > maxTimestamp) {
                                    maxTimestamp = ts;
                                }
                            }
                        });
                        if (maxTimestamp) {
                            lastSongTimestamp = new Date(maxTimestamp);
                        }
                    }
                    const lastSongMinutesAgoEl = document.getElementById('lastSongMinutesAgo');
                    if (lastSongTimestamp) {
                        const minutesAgo = Math.round((Date.now() - lastSongTimestamp.getTime()) / 60000);
                        lastSongMinutesAgoEl.textContent = minutesAgo;
                        lastSongMinutesAgoEl.dataset.lastTimestamp = lastSongTimestamp.getTime();
                    } else {
                        // If we have a previous timestamp, recalculate
                        if (lastSongMinutesAgoEl.dataset.lastTimestamp) {
                            const prevTimestamp = parseInt(lastSongMinutesAgoEl.dataset.lastTimestamp);
                            const minutesAgo = Math.round((Date.now() - prevTimestamp) / 60000);
                            lastSongMinutesAgoEl.textContent = minutesAgo;
                        } else {
                            lastSongMinutesAgoEl.textContent = '...';
                        }
                    }
                })
                .catch(err => {
                    console.error('Failed to load now playing:', err);
                    document.getElementById('nowPlayingContent').innerHTML = `
                        <div class="text-center text-muted py-3">
                            <small>Fout bij het laden van gegevens</small>
                        </div>
                    `;
                    // Retain previous value for lastSongMinutesAgo if available
                    const lastSongMinutesAgoEl = document.getElementById('lastSongMinutesAgo');
                    if (lastSongMinutesAgoEl.dataset.lastTimestamp) {
                        const prevTimestamp = parseInt(lastSongMinutesAgoEl.dataset.lastTimestamp);
                        const minutesAgo = Math.round((Date.now() - prevTimestamp) / 60000);
                        lastSongMinutesAgoEl.textContent = minutesAgo;
                    } else {
                        lastSongMinutesAgoEl.textContent = '...';
                    }
                });
        }

        // Refresh dashboard data (stats and recent detections)
        function refreshDashboardData() {
            console.log('Refreshing dashboard data...');
            
            fetch(`${API_BASE}/api/index-data`)
                .then(response => response.json())
                .then(data => {
                    // Update stats
                    document.getElementById('totalCount').textContent = data.total_count;
                    document.getElementById('uniqueStations').textContent = data.stations.length;
                    document.getElementById('uniqueSongs').textContent = data.song_titles.length;
                    document.getElementById('mostSongsDay').innerHTML = data.most_songs_day && data.most_songs_day.day_iso ? `<a href="/day.php?date=${encodeURIComponent(data.most_songs_day.day_iso)}" class="text-decoration-none">${data.most_songs_day.day}</a>` : (data.most_songs_day ? data.most_songs_day.day : '...');
                    document.getElementById('mostSongsCount').textContent = data.most_songs_day ? data.most_songs_day.count : '...';
                    document.getElementById('averagePerHour').textContent = data.average_per_hour !== null ? data.average_per_hour : '...';
                    
                    // Format first timestamp
                    const firstDate = new Date(data.first_timestamp);
                    const formattedFirstDate = firstDate.toLocaleDateString('nl-NL', { 
                        day: 'numeric', 
                        month: 'short', 
                        year: 'numeric' 
                    });
                    document.getElementById('firstTimestamp').textContent = formattedFirstDate;
                    
                    document.getElementById('todayCountnav').textContent = data.today_count || '0';

                    // Populate largest-gap info (if available)
                    if (data.largest_gap && data.largest_gap.seconds && data.largest_gap.seconds > 0) {
                        const lg = data.largest_gap;
                        const gapDateStr = lg.date ? new Date(lg.date).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short', year: 'numeric' }) : (lg.date || '');
                        document.getElementById('largestGap').textContent = `${lg.readable} op ${gapDateStr}`;
                        const stationEl2 = document.getElementById('largestGapEndStation');
                        const songEl2 = document.getElementById('largestGapEndSong');
                        if (lg.end_station) {
                            stationEl2.innerHTML = `<a href="/station.php#${encodeURIComponent(lg.end_station)}" class="text-decoration-none">${lg.end_station}</a>`;
                        } else {
                            stationEl2.textContent = '...';
                        }
                        if (lg.end_song) {
                            songEl2.innerHTML = `<a href="/song.php#${encodeURIComponent(lg.end_song)}" class="text-decoration-none">${lg.end_song}</a>`;
                        } else {
                            songEl2.textContent = '...';
                        }
                        document.getElementById('largestGapEndTime').innerHTML = lg.date ? `<a href="/day.php?date=${encodeURIComponent(lg.date)}" class="text-decoration-none">${gapDateStr}</a>` : '...';
                    } else {
                        document.getElementById('largestGap').textContent = 'Geen gegevens';
                        document.getElementById('largestGapEndStation').textContent = '...';
                        document.getElementById('largestGapEndSong').textContent = '...';
                        document.getElementById('largestGapEndTime').textContent = '...';
                    }

                    const lastSongMinutesAgo = data.songs && data.songs.length > 0 ? Math.round((Date.now() - new Date(data.songs[0].timestamp_raw).getTime()) / 60000) : null;
                    document.getElementById('lastSongMinutesAgo').textContent = lastSongMinutesAgo !== null ? lastSongMinutesAgo : '...';
                    document.getElementById('lastSongStation').innerHTML = data.songs && data.songs.length > 0 ? `<a href="/station.php#${encodeURIComponent(data.songs[0].station)}" class="text-decoration-none">${data.songs[0].station}</a>` : '...';
                    document.getElementById('lastSongTitle').innerHTML = data.songs && data.songs.length > 0 ? `<a href="/song.php#${encodeURIComponent(data.songs[0].song)}" class="text-decoration-none">${data.songs[0].song}</a>` : '...';


                    // Update footer
                    document.getElementById('footerText').textContent = `Tracking since ${formattedFirstDate} - Version 1.0 - Data auto-refreshes every 30 seconds`;


                    // Update recent detections table
                    if (data.songs && data.songs.length > 0) {
                        const recentSongs = data.songs.slice(0, 10);
                        const recentTableHtml = `
                            <table class="table table-sm table-borderless mb-0">
                                <tbody>
                                    ${recentSongs.map(song => {
                                        const ts = new Date(song.timestamp_raw);
                                        const compactTime = ts.toLocaleTimeString('nl-NL', { 
                                            hour: '2-digit', 
                                            minute: '2-digit',
                                            hour12: false 
                                        });
                                        const compactDate = ts.toLocaleDateString('nl-NL', { 
                                            day: 'numeric', 
                                            month: 'short',  
                                        });
                                        const isoDate = (song.timestamp_raw && song.timestamp_raw.split('T')[0]) || '';
                                        const dayHref = '/day.php?date=' + encodeURIComponent(isoDate);
                                        return `
                                        <tr style="border-bottom: 1px solid #dee2e6;">
                                            <td class="p-1" style="white-space: nowrap;">
                                                <small><a href="${dayHref}" class="text-decoration-none">${compactDate}</a>, ${compactTime}</small>
                                            </td>
                                            <td class="p-1">
                                                <small>
                                                    <a href="/station.php#${encodeURIComponent(song.station)}" class="text-decoration-none">${song.station}</a> - 
                                                    <a href="/song.php#${encodeURIComponent(song.song)}" class="text-decoration-none">${song.song}</a>
                                                </small>
                                            </td>
                                        </tr>
                                    `}).join('')}
                                </tbody>
                            </table>
                        `;
                        document.getElementById('recentDetectionsContainer').innerHTML = recentTableHtml;
                    }
                })
                .catch(err => console.error('Failed to refresh dashboard data:', err));
        }
        
        updateNowPlaying();
        setInterval(updateNowPlaying, 60000);

        // Poll for song count every 10 seconds and refresh dashboard if changed
        let lastSongCount = null;
        function pollSongCount() {
            //console.log('Polling song count...');

            // cache-bust to avoid intermediate caching
            const url = `${API_BASE}?song_count=1&_=${Date.now()}`;

            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status} ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    //console.log('Data received:', data);

                    // If the API returned an error object, surface it and stop
                    if (data && data.error) {
                        console.error('Song-count API error:', data.error, data.tables || '');
                        // show short notice in footer (non-persistent)
                        const footer = document.getElementById('footerText');
                        if (footer) {
                            const prev = footer.dataset.prev || footer.textContent;
                            footer.dataset.prev = prev;
                            footer.textContent = `ERROR: ${data.error}`;
                            footer.classList.add('text-danger');
                            setTimeout(() => {
                                footer.textContent = footer.dataset.prev;
                                footer.classList.remove('text-danger');
                            }, 8000);
                        }
                        return;
                    }

                    if (typeof data.count === 'number') {
                        if (lastSongCount === null) {
                            lastSongCount = data.count;
                            //console.log(`Initial song count set to ${lastSongCount}`);
                        } else if (data.count !== lastSongCount) {
                            lastSongCount = data.count;
                            refreshDashboardData();
                            updateNowPlaying();
                            console.log(`Song count changed to ${data.count}, dashboard refreshed`);
                        } else {
                            //console.log(`Song count unchanged at ${data.count}`);
                        }
                    } else {
                        console.warn('pollSongCount: unexpected response format', data);
                    }
                })
                .catch(err => {
                    console.error('Failed to poll song count:', err);
                });
        }
        pollSongCount();
        setInterval(pollSongCount, 10000);

        // Auto-refresh page every 10 minutes (fallback)
        setTimeout(() => location.reload(), 600000);

        // Set active nav link
        const navLink = document.querySelector('a[href="/"]');
        if (navLink) {
            navLink.classList.add('active');
        }
    </script>
</body>
</html>