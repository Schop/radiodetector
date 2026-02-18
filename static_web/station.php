<?php $page_title = '{stationName} - Phil Collins Detector'; ?>
<?php include 'includes/head.html'; ?>

<body>
    <div class="container-fluid">
        <main>
            <?php include 'includes/nav.html'; ?>
            
            <h1 id="stationTitle">Loading...</h1>
            <h3 id="stationSubTitle" class="text-muted mb-4">Wat wordt er gedraaid op {stationName}?</h3>
            
            <!-- Charts Grid - 2x3 Layout -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <p>Sinds <strong><span id="firstTimestamp">...</span></strong> is er in totaal <strong><span id="totalSongs">...</span></strong> keer een nummer gedraaid op <strong><span id="statStation">...</span></strong>.</p>
                            <p>Er zijn in totaal <strong><span id="uniqueSongs">...</span></strong> verschillende nummers gedraaid.</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">Top 5 meest gespeelde nummers</h6>
                            <div style="height: 200px;">
                                <canvas id="topSongsChart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>                 
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">Laatste 14 dagen</h6>
                            <div style="height: 200px;">
                                <canvas id="timelineChart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">Gemiddelde per dag van de week</h6>
                            <small class="text-muted">klik op de balken voor meer details</small>
                            <div style="height: 200px;">
                                <canvas id="weekdayChart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">Gemiddelde per uur van de dag</h6>
                            <div style="height: 200px;">
                                <canvas id="hourlyChart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body" style="display: flex; flex-direction: column;">
                            <h6 class="card-title">Recente detecties - <a href="detections.php" class="text-danger">Bekijk hier alle detecties</a></h6>
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

        </main>
    </div>

    <?php include 'includes/footer.html'; ?>

    <script>
        const API_BASE = '/api.php';
        const stationName = decodeURIComponent(window.location.hash.substring(1));
        // console.log('Station name from URL:', stationName, 'Hash:', window.location.hash);

        document.getElementById('stationTitle').textContent = stationName;
        document.title = document.title.replace('{stationName}', stationName);
        document.getElementById('stationSubTitle').innerHTML = 
            document.getElementById('stationSubTitle').innerHTML.replace('{stationName}', stationName);

        // Load station data
        // console.log('Loading station data for:', stationName);
        fetch(`${API_BASE}/api/station/${encodeURIComponent(stationName)}/data`)
            .then(response => {
                // console.log('Station data response:', response);
                return response.json();
            })
            .then(data => {
                // console.log('Station data received:', data);
                document.getElementById('totalSongs').textContent = data.total_songs;
                document.getElementById('uniqueSongs').textContent = data.song_titles.length;
                document.getElementById('statStation').textContent = stationName;

                // Format first timestamp as "10 feb 2026"
                    const firstDate = new Date(data.first_timestamp);
                    const formattedFirstDate = firstDate.toLocaleDateString('nl-NL', { 
                        day: 'numeric', 
                        month: 'short', 
                        year: 'numeric' 
                    });
                    document.getElementById('firstTimestamp').textContent = formattedFirstDate;

                // Populate recent detections table (last 8 detections)
                if (data.songs && data.songs.length > 0) {
                    const recentSongs = data.songs.slice(0, 8);
                    const recentTableHtml = `
                        <table class="table table-sm table-borderless mb-0">
                            <tbody>
                                ${recentSongs.map(song => {
                                    // Format timestamp more compactly: date + time
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
                                    <tr>
                                        <td class="p-1">
                                            <small class="text-muted" style="white-space: nowrap;"><a href="${dayHref}" class="text-decoration-none">${compactDate}</a>, ${compactTime}</small>
                                        </td>
                                        <td class="p-1">
                                            <small>
                                                <a href="/song.php#${encodeURIComponent(song.song)}" class="text-decoration-none">${song.song}</a>
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
            })
            .catch(err => {
                console.error('Failed to load station data:', err);
                document.getElementById('recentDetectionsContainer').innerHTML = `
                    <div class="text-center text-muted py-3">
                        <small>Fout bij laden</small>
                    </div>
                `;
            });

        // Load charts
        fetch(`${API_BASE}/api/station/${encodeURIComponent(stationName)}/charts`)
            .then(response => response.json())
            .then(data => {
                new Chart(document.getElementById('hourlyChart'), {
                    type: 'bar',
                    data: {
                        labels: data.hours.labels,
                        datasets: [{
                            label: 'In dit uur gedetecteerd',
                            data: data.hours.data,
                            backgroundColor: 'rgba(54, 162, 235, 0.6)',
                            borderColor: 'rgba(54, 162, 235, 1)',
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

                new Chart(document.getElementById('weekdayChart'), {
                    type: 'bar',
                    data: {
                        labels: data.weekdays.labels,
                        datasets: [{
                            label: 'Op deze dag gedetecteerd',
                            data: data.weekdays.data,
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

                // Top 5 songs chart (horizontal bars, clickable)
                const top5Labels = data.top_songs.labels.slice(0, 5);
                const top5Data = data.top_songs.data.slice(0, 5);
                new Chart(document.getElementById('topSongsChart'), {
                    type: 'bar',
                    data: {
                        labels: top5Labels,
                        datasets: [{
                            label: 'Aantal keer gespeeld',
                            data: top5Data,
                            backgroundColor: 'rgba(255, 99, 132, 0.6)',
                            borderColor: 'rgba(255, 99, 132, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: false,
                        scales: { 
                            x: { beginAtZero: true, ticks: { precision: 0 } }
                        },
                        plugins: { legend: { display: false } },
                        onHover: (event, elements) => {
                            event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                        },
                        onClick: (event, elements) => {
                            if (elements.length > 0) {
                                const index = elements[0].index;
                                const song = top5Labels[index];
                                window.location.href = `/song.php#${encodeURIComponent(song)}`;
                                // console.log('Clicked on song:', song);
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
                            label: 'Aantal detecties per dag',
                            data: data.timeline.data,
                            backgroundColor: 'rgba(153, 102, 255, 0.2)',
                            borderColor: 'rgba(153, 102, 255, 1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: false,
                        scales: { 
                            y: { beginAtZero: true, ticks: { precision: 0 } }
                        },
                        plugins: { legend: { display: false } }
                    }
                });
            })
            .catch(err => console.error('Failed to load chart data:', err));
    </script>
</body>
</html>