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
                <h5>Phil detecties vandaag: <strong id="todayCount">...</strong></h5>
                <p>Sinds <span id="firstTimestamp">...</span> is Phil Collins <strong id="totalCount">...</strong> keer gedetecteerd,
                        op <strong id="uniqueStations">...</strong> verschillende radiozenders,
                        met <strong id="uniqueSongs">...</strong> verschillende nummers.
                </p>
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
                    </div>
                </div>
            </div>
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
        </div>

        <!-- Third Row: Top Charts -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-title">Top 5 Radiostations die Phil Collins draaien</h6>
                        <small class="text-muted">klik op de balken voor meer details</small>
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
                        <small class="text-muted">klik op de balken voor meer details</small>
                        <div style="height: 300px;">
                            <canvas id="songsChart" width="400" height="300"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <?php include 'includes/footer.html'; ?>
        </main>
    </div>

    <script>
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
                
                // Format first timestamp as "10 feb 2026"
                const firstDate = new Date(data.first_timestamp);
                const formattedFirstDate = firstDate.toLocaleDateString('nl-NL', { 
                    day: 'numeric', 
                    month: 'short', 
                    year: 'numeric' 
                });
                document.getElementById('firstTimestamp').textContent = formattedFirstDate;
                
                document.getElementById('todayCount').textContent = data.today_count || '0';

                // Update footer
                document.getElementById('footerText').textContent = `Tracking since ${data.first_timestamp || '...'} - Version 1.0 - Data auto-refreshes every 30 seconds`;

                // Populate recent detections table (last 10 detections, no artist column)
                if (data.songs && data.songs.length > 0) {
                    const recentSongs = data.songs.slice(0, 10);
                    const recentTableHtml = `
                        <table class="table table-sm table-borderless mb-0">
                            <tbody>
                                ${recentSongs.map(song => {
                                    // Format timestamp more compactly: "12 Feb, 21:12"
                                    const ts = new Date(song.timestamp_raw);
                                    const compactTime = ts.toLocaleDateString('nl-NL', { 
                                        day: 'numeric', 
                                        month: 'short' 
                                    }) + ', ' + ts.toLocaleTimeString('nl-NL', { 
                                        hour: '2-digit', 
                                        minute: '2-digit',
                                        hour12: false 
                                    });
                                    return `
                                    <tr style="border-bottom: 1px solid #dee2e6;">
                                        <td class="p-1" style="white-space: nowrap;">
                                            <small class="text-muted">${compactTime}</small>
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
                                    plugins: { legend: { display: false } }
                                }
                            });

                            // Stations chart
                            new Chart(document.getElementById('stationsChart'), {
                                type: 'bar',
                                data: {
                                    labels: chartData.stations.labels,
                                    datasets: [{
                                        label: 'Detections',
                                        data: chartData.stations.data,
                                        backgroundColor: 'rgba(75, 192, 192, 0.6)',
                                        borderColor: 'rgba(75, 192, 192, 1)',
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
            // console.log('Refreshing dashboard data...');
            
            fetch(`${API_BASE}/api/index-data`)
                .then(response => response.json())
                .then(data => {
                    // Update stats
                    document.getElementById('totalCount').textContent = data.total_count;
                    document.getElementById('uniqueStations').textContent = data.stations.length;
                    document.getElementById('uniqueSongs').textContent = data.song_titles.length;
                    
                    // Format first timestamp
                    const firstDate = new Date(data.first_timestamp);
                    const formattedFirstDate = firstDate.toLocaleDateString('nl-NL', { 
                        day: 'numeric', 
                        month: 'short', 
                        year: 'numeric' 
                    });
                    document.getElementById('firstTimestamp').textContent = formattedFirstDate;
                    
                    document.getElementById('todayCount').textContent = data.today_count || '0';

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
                                        const compactTime = ts.toLocaleDateString('nl-NL', { 
                                            day: 'numeric', 
                                            month: 'short' 
                                        }) + ', ' + ts.toLocaleTimeString('nl-NL', { 
                                            hour: '2-digit', 
                                            minute: '2-digit',
                                            hour12: false 
                                        });
                                        return `
                                        <tr style="border-bottom: 1px solid #dee2e6;">
                                            <td class="p-1" style="white-space: nowrap;">
                                                <small class="text-muted">${compactTime}</small>
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

        // Auto-refresh key data every 30 seconds
        setInterval(refreshDashboardData, 30000);

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