<?php $page_title = '{songName} - Phil Collins Detector'; ?>
<?php include 'includes/head.html'; ?>

<body>
    <div class="container-fluid">
        <main>
            <?php include 'includes/nav.html'; ?>

            <h1 id="songTitle">Loading...</h1>
            <h3 class="text-muted mb-4" id="songSubtitle">Song details and play history</h3>

            <!-- Summary Stats -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title"><span id="songNameStats">...</span> Statistieken</h6>
                            <table class="compact-stats-table w-100">
                                <tbody>
                                    <tr>
                                        <td>Totaal gespeeld</td>
                                        <td id="totalDetections">...</td>
                                    </tr>
                                    <tr>
                                        <td>Unieke Radiostations</td>
                                        <td id="uniqueStations">...</td>
                                    </tr>
                                    <tr>
                                        <td>Artiesten</td>
                                        <td id="uniqueArtists">...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">Radiostations die <span id="songNameStations">...</span> spelen</h6>
                            <div style="height: 200px;">
                                <canvas id="stationsChart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">Laatste 14 dagen voor <span id="songNameTimeline">...</span></h6>
                            <div style="height: 200px;">
                                <canvas id="timelineChart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Second Row: Hourly, Weekly, and Recent Detections -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">Uurverdeling voor <span id="songNameHourly">...</span></h6>
                            <div style="height: 200px;">
                                <canvas id="hourlyChart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">Weekdagverdeling voor <span id="songNameWeekly">...</span></h6>
                            <div style="height: 200px;">
                                <canvas id="weekdayChart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body" style="display: flex; flex-direction: column;">
                            <h6 class="card-title">Recente detecties van <span id="songNameRecent">...</span> - <a href="/detections.php" class="text-danger">Bekijk hier alle detecties</a></h6>
                            <div id="recentDetectionsContainer" style="flex: 1; overflow-y: auto;">
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
            </div>

            <?php include 'includes/footer.html'; ?>
        </main>
    </div>

    <script>
        const API_BASE = '/api.php';

        // Get song name from URL hash
        const songName = decodeURIComponent(window.location.hash.substring(1));

        if (!songName) {
            document.getElementById('songTitle').textContent = 'Song not specified';
            document.querySelectorAll('#songNameStats, #songNameStations, #songNameTimeline, #songNameRecent, #songNameHourly, #songNameWeekly').forEach(el => {
                el.textContent = 'Unknown Song';
            });
        } else {
            document.getElementById('songTitle').textContent = songName;
            document.title = document.title.replace('{songName}', songName);
            document.querySelectorAll('#songNameStats, #songNameStations, #songNameTimeline, #songNameRecent, #songNameHourly, #songNameWeekly').forEach(el => {
                el.textContent = songName;
            });

            // Load song data
            fetch(`${API_BASE}/api/song/${encodeURIComponent(songName)}/data`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('API Error:', data.error);
                        return;
                    }

                    // Update stats
                    document.getElementById('totalDetections').textContent = data.total_detections;
                    document.getElementById('uniqueStations').textContent = data.stations.length;
                    document.getElementById('uniqueArtists').textContent = data.artists.length;

                    // Populate recent detections table (last 10 detections)
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
                                                    <a href="/station.php#${encodeURIComponent(song.station)}" class="text-decoration-none">${song.station}</a>
                                                </small>
                                            </td>
                                        </tr>
                                    `}).join('')}
                                </tbody>
                            </table>
                        `;
                        document.getElementById('recentDetectionsContainer').innerHTML = recentTableHtml;
                    } else {
                        document.getElementById('recentDetectionsContainer').innerHTML = `
                            <div class="text-center text-muted py-3">
                                <small>Geen recente detecties</small>
                            </div>
                        `;
                    }

                    // Update subtitle with artist info
                    const subtitle = document.getElementById('songSubtitle');
                    if (data.artists.length === 1) {
                        subtitle.innerHTML = `by ${data.artists[0]}`;
                    } else if (data.artists.length > 1) {
                        subtitle.innerHTML = `by ${data.artists.join(', ')}`;
                    }
                })
                .catch(err => {
                    console.error('Failed to load song data:', err);
                });

            // Load charts
            fetch(`${API_BASE}/api/song/${encodeURIComponent(songName)}/charts`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('API Error:', data.error);
                        return;
                    }

                    // Stations chart
                    new Chart(document.getElementById('stationsChart'), {
                        type: 'doughnut',
                        data: {
                            labels: data.stations.labels,
                            datasets: [{
                                label: 'Aantal per zender',
                                data: data.stations.data,
                                backgroundColor: [
                                    'rgba(255, 99, 132, 0.8)',
                                    'rgba(54, 162, 235, 0.8)',
                                    'rgba(255, 205, 86, 0.8)',
                                    'rgba(75, 192, 192, 0.8)',
                                    'rgba(153, 102, 255, 0.8)',
                                    'rgba(255, 159, 64, 0.8)',
                                    'rgba(201, 203, 207, 0.8)',
                                    'rgba(255, 99, 132, 0.5)',
                                    'rgba(54, 162, 235, 0.5)',
                                    'rgba(255, 205, 86, 0.5)'
                                ],
                                borderWidth: 2
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            cutout: '50%',
                            plugins: {
                                legend: {
                                    position: 'bottom',
                                    labels: {
                                        boxWidth: 12,
                                        font: { size: 11 }
                                    }
                                }
                            }
                        }
                    });

                    // Timeline chart (last 14 days)
                    new Chart(document.getElementById('timelineChart'), {
                        type: 'line',
                        data: {
                            labels: data.timeline.labels,
                            datasets: [{
                                label: 'Dagelijkse detecties',
                                data: data.timeline.data,
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

                    // Hourly chart
                    new Chart(document.getElementById('hourlyChart'), {
                        type: 'bar',
                        data: {
                            labels: data.hours.labels,
                            datasets: [{
                                label: 'Detections by Hour',
                                data: data.hours.data,
                                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                                borderColor: 'rgba(75, 192, 192, 1)',
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

                    // Weekday chart
                    new Chart(document.getElementById('weekdayChart'), {
                        type: 'bar',
                        data: {
                            labels: data.weekdays.labels,
                            datasets: [{
                                label: 'Detections by Weekday',
                                data: data.weekdays.data,
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
                })
                .catch(err => console.error('Failed to load chart data:', err));
        }

        // Set active nav link
        document.querySelector('a[href="/"]').classList.add('active');
    </script>
</body>
</html>