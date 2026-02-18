<?php $page_title = '{date} - Phil Collins Detector'; ?>
<?php include 'includes/head.html'; ?>

<body>
    <div class="container-fluid">
        <main>
            <?php include 'includes/nav.html'; ?>

            <h1 id="dayTitle">Loading...</h1>
            <h5 class="text-muted mb-4" id="daySubtitle">Details van detecties op deze dag</h5>

            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <p>Op <strong><span id="displayDate">...</span></strong> is Phil Collins <strong><span id="totalCount">...</span></strong> keer op de radio geweest.
                            op <strong id="uniqueStations">...</strong> verschillende zenders, met <strong id="uniqueSongs">...</strong> verschillende nummers.</p>
                        </div>
                    </div>
                </div>

                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">Top 5 stations op <span id="topStationsDate">...</span></h6>
                            <div style="height: 200px;"><canvas id="stationsChart" width="400" height="200"></canvas></div>
                        </div>
                    </div>
                </div>

                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">Top 5 nummers op <span id="topSongsDate">...</span></h6>
                            <div style="height: 200px;"><canvas id="songsChart" width="400" height="200"></canvas></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-md-8">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">Recente detecties op <span id="recentForDate">...</span></h6>
                            <div id="recentDetectionsContainer" style="height: 400px; overflow-y: auto;">
                                <div class="text-center text-muted py-3">
                                    <div class="spinner-border spinner-border-sm" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                    <small class="d-block mt-2">Loading detections...</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">Cumulatieve opbouw per uur</h6>
                            <div style="height: 360px;"><canvas id="hoursChart" width="400" height="360"></canvas></div>
                        </div>
                    </div>
                </div>
            </div>

            <?php include 'includes/footer.html'; ?>
        </main>
    </div>

    <script>
        const API_BASE = '/api.php';
        const params = new URLSearchParams(window.location.search);
        const dateParam = params.get('date') || decodeURIComponent(window.location.hash.substring(1));

        function formatDateDisplay(iso) {
            try {
                const dt = new Date(iso + 'T00:00:00');
                return dt.toLocaleDateString('nl-NL', { day: 'numeric', month: 'long', year: 'numeric' });
            } catch (e) { return iso; }
        }

        function formatTitleDateDisplay(iso) {
            try {
                const dt = new Date(iso + 'T00:00:00');
                return dt.toLocaleDateString('nl-NL', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
            } catch (e) { return iso; }
        }

        if (!dateParam) {
            document.getElementById('dayTitle').textContent = 'Datum niet opgegeven';
            document.getElementById('recentDetectionsContainer').innerHTML = '<div class="text-center text-muted py-3"><small>Geen datum opgegeven</small></div>';
        } else {
            const isoDate = dateParam;
            const normalDate = formatDateDisplay(isoDate);
            const titleDate = formatTitleDateDisplay(isoDate);
            document.getElementById('dayTitle').textContent = `${titleDate}`;
            document.getElementById('displayDate').textContent = normalDate;
            document.getElementById('topStationsDate').textContent = normalDate;
            document.getElementById('topSongsDate').textContent = normalDate;
            document.title = document.title.replace('{date}', normalDate);
            document.getElementById('recentForDate').textContent = normalDate;

            // Fetch day data
            fetch(`${API_BASE}/api/day/${encodeURIComponent(isoDate)}/data`)
                .then(r => r.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('recentDetectionsContainer').innerHTML = `<div class="text-center text-muted py-3"><small>${data.error}</small></div>`;
                        return;
                    }

                    document.getElementById('totalCount').textContent = data.total_count || 0;
                    document.getElementById('uniqueStations').textContent = data.stations ? data.stations.length : 0;
                    document.getElementById('uniqueSongs').textContent = data.song_titles ? data.song_titles.length : 0;

                    if (data.songs && data.songs.length > 0) {
                        const rows = data.songs.map(s => {
                            const ts = new Date(s.timestamp_raw);
                            const timeOnly = ts.toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit', hour12: false });
                            return `
                                <tr style="border-bottom: 1px solid #eee;">
                                    <td class="p-2" style="white-space: nowrap;"><small class="text-muted">${timeOnly}</small></td>
                                    <td class="p-2"><small><a href="/station.php#${encodeURIComponent(s.station)}" class="text-decoration-none">${s.station}</a></small></td>
                                    <td class="p-2"><small><a href="/song.php#${encodeURIComponent(s.song)}" class="text-decoration-none">${s.song}</a></small></td>
                                </tr>
                            `;
                        }).join('');

                        document.getElementById('recentDetectionsContainer').innerHTML = `
                            <table class="table table-sm table-borderless mb-0"><tbody>${rows}</tbody></table>
                        `;
                    } else {
                        document.getElementById('recentDetectionsContainer').innerHTML = `<div class="text-center text-muted py-3"><small>Geen detecties voor ${formatDateDisplay(isoDate)}</small></div>`;
                    }
                })
                .catch(err => {
                    console.error('Failed to load day data', err);
                    document.getElementById('recentDetectionsContainer').innerHTML = `<div class="text-center text-muted py-3"><small>Fout bij laden</small></div>`;
                });

            // Fetch charts for the day
            fetch(`${API_BASE}/api/day/${encodeURIComponent(isoDate)}/charts`)
                .then(r => r.json())
                .then(data => {
                    // Stations
                    new Chart(document.getElementById('stationsChart'), {
                        type: 'doughnut',
                        data: { labels: data.stations.labels || [], datasets: [{ data: data.stations.data || [], backgroundColor: [ 'rgba(75,192,192,0.8)', 'rgba(54,162,235,0.8)', 'rgba(153,102,255,0.8)', 'rgba(255,159,64,0.8)', 'rgba(255,99,132,0.8)' ], borderWidth: 1 }] },
                        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
                    });

                    // Top songs
                    new Chart(document.getElementById('songsChart'), {
                        type: 'bar',
                        data: { labels: data.songs.labels || [], datasets: [{ data: data.songs.data || [], backgroundColor: 'rgba(255,99,132,0.6)' }] },
                        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
                    });

                    // Cumulative buildup (line) — replaces the hourly bar chart
                    const hourLabels = data.hours.labels || Array.from({length:24}, (_,i) => `${String(i).padStart(2,'0')}:00`);
                    const hourCounts = (data.hours.data || []).map(v => Number(v || 0));

                    const cumulative = [];
                    let running = 0;
                    for (let i = 0; i < hourCounts.length; i++) {
                        running += hourCounts[i];
                        cumulative.push(running);
                    }

                    new Chart(document.getElementById('hoursChart'), {
                        type: 'line',
                        data: {
                            labels: hourLabels,
                            datasets: [{
                                label: 'Cumulatief aantal detecties',
                                data: cumulative,
                                backgroundColor: 'rgba(54,162,235,0.12)',
                                borderColor: 'rgba(54,162,235,1)',
                                pointRadius: 3,
                                fill: true,
                                tension: 0.25
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: { beginAtZero: true, ticks: { precision: 0 } },
                                x: { ticks: { maxRotation: 45, minRotation: 30 } }
                            },
                            plugins: {
                                legend: { display: false },
                                tooltip: {
                                    callbacks: {
                                        label: ctx => `${ctx.parsed.y} totaal`
                                    }
                                }
                            }
                        }
                    });
                })
                .catch(err => console.error('Failed to load day charts', err));
        }

        // set active nav
        const navLink = document.querySelector('a[href="/"]');
        if (navLink) navLink.classList.add('active');
    </script>
</body>
</html>