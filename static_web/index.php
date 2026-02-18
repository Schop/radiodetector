<?php $page_title = 'Phil Collins Detector'; ?>
<?php include 'includes/head.html'; ?>

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
                        <p>Gemiddeld worden er per uur <strong id="averagePerHour">...</strong>
                           nummers van Phil Collins gedetecteerd op de Nederlandse radiozenders.</p>
                        <p>Phil was <strong id="lastSongMinutesAgo">...</strong> minuten geleden voor het laatst bij <span id="lastSongStation">...</span> te horen met het nummer <span id="lastSongTitle">...</span>.</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-2">
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-title">Trend in de laatste 14 dagen</h6>
                        <div style="height: 250px;">
                            <canvas id="timelineChart" width="400" height="300"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-2">
                <div class="card h-100">
                    <div class="card-body">
                        <p>Sinds <span id="firstTimestamp">...</span> is Phil Collins <strong id="totalCount">...</strong> keer gedetecteerd,
                           op <strong id="uniqueStations">...</strong> verschillende radiozenders,
                           met <strong id="uniqueSongs">...</strong> verschillende nummers.
                        </p>
                        <p>Op de dag met de meeste detecties (<span id="mostSongsDay">...</span>)
                           werden <strong id="mostSongsCount">...</strong> nummers van Phil gedetecteerd.
                        </p>
                        <hr>
                        <p>De langste onderbreking tussen detecties was <strong id="largestGap">...</strong>. Aan deze periode van rust kwam een einde toen <span id="largestGapEndStation">...</span>
                           het nummer <span id="largestGapEndSong">...</span>
                            draaide op <span id="largestGapEndTime">...</span>.</p>
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

        <?php include 'includes/footer.html'; ?>
        </main>
    </div>

    <script>
        //console.log('Script starting...');
        const API_BASE = '/api.php'; // Adjust this path as needed

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

                const lastSongMinutesAgo = data.songs && data.songs.length > 0 ? Math.round((Date.now() - new Date(data.songs[0].timestamp_raw).getTime()) / 60000) : null;
                document.getElementById('lastSongMinutesAgo').textContent = lastSongMinutesAgo !== null ? lastSongMinutesAgo : '...';
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

                    // Initialize timeline chart
                    fetch(`${API_BASE}/api/chart-data`)
                        .then(response => response.json())
                        .then(chartData => {
                            // Timeline chart
                            new Chart(document.getElementById('timelineChart'), {
                                type: 'line',
                                data: {
                                    labels: chartData.timeline.labels,
                                    datasets: [{
                                        label: 'Dagelijkse Detecties',
                                        data: chartData.timeline.data,
                                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                                        borderColor: 'rgba(54, 162, 235, 1)',
                                        borderWidth: 2,
                                        fill: true,
                                        tension: 0.3
                                    }]
                                },
                                options: {
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
                                    plugins: { legend: { display: false } },
                                    onHover: (event, elements) => {
                                        event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                                    },
                                    onClick: (event, elements) => {
                                        // Use the index of the clicked point to find the ISO date from the API response
                                        if (elements.length > 0 && chartData.timeline && chartData.timeline.dates) {
                                            const idx = elements[0].index;
                                            const isoDate = chartData.timeline.dates[idx];
                                            if (isoDate) {
                                                window.location.href = `/day.php?date=${encodeURIComponent(isoDate)}`;
                                            }
                                        }
                                    }
                                }
                            });

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
                                    scales: { x: { beginAtZero: true, ticks: { precision: 0 } } },
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
                                    scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
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
                })
                .catch(err => {
                    console.error('Failed to load now playing:', err);
                    document.getElementById('nowPlayingContent').innerHTML = `
                        <div class="text-center text-muted py-3">
                            <small>Fout bij het laden van gegevens</small>
                        </div>
                    `;
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