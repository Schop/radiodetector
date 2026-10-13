<?php
// Generic page for side-project songs (tracked_songs table): tracked.php?artist=Toto&song=Africa
$artist = trim($_GET['artist'] ?? '');
$song = trim($_GET['song'] ?? '');
$valid = $artist !== '' && $song !== '';
$h_artist = htmlspecialchars($artist, ENT_QUOTES, 'UTF-8');
$h_song = htmlspecialchars($song, ENT_QUOTES, 'UTF-8');

if ($valid) {
    $page_title = "$song van $artist op de Nederlandse radio";
    $page_description = "Hoe vaak draait $song van $artist op de Nederlandse radio? Overzicht per zender, uur en weekdag.";
} else {
    $page_title = 'Nummer volgen';
    $page_description = 'Overzicht van een gevolgd nummer op de Nederlandse radio.';
}
?>
<?php include 'includes/head.html'; ?>

<body>
    <div class="container-fluid">
        <main>
            <?php include 'includes/nav.html'; ?>

            <?php if (!$valid): ?>
            <h1>Nummer volgen</h1>
            <div class="alert alert-warning">Geef een artiest en nummer op, bijvoorbeeld <a href="tracked.php?artist=Toto&amp;song=Africa">tracked.php?artist=Toto&amp;song=Africa</a>.</div>
            <?php else: ?>
            <h1><?= $h_song ?></h1>
            <h5 class="text-muted mb-4"><?= $h_song ?> van <?= $h_artist ?> heeft niks met Phil Collins te maken, maar wordt hier voor de zekerheid toch bijgehouden.</h5>

            <div id="errorMessage" class="alert alert-warning d-none"></div>

            <!-- Summary, stations and timeline -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <p>Sinds <strong><span id="firstTimestamp">...</span></strong> is <strong><?= $h_song ?></strong> van <?= $h_artist ?> in totaal <strong><span id="totalPlays">...</span></strong> keer gedraaid op <strong><span id="uniqueStations">...</span></strong> verschillende radiostations.</p>
                            <p class="mb-2">Gemiddeld <strong><span id="averagePerDay">...</span></strong> keer per dag. Laatst gehoord op <strong><span id="lastTimestamp">...</span></strong>.</p>
                            <p class="text-muted small mb-0">Gebaseerd op de detecties vanaf het begin van de logboeken; eerdere draaibeurten zijn niet bekend.</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body" style="display: flex; flex-direction: column;">
                            <h6 class="card-title">Radiostations die <?= $h_song ?> spelen</h6>
                            <div id="stationsContainer" style="flex: 1; overflow-y: auto; max-height: 220px;">
                                <div class="text-center text-muted py-3">
                                    <div class="spinner-border spinner-border-sm" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">Laatste 30 dagen voor <?= $h_song ?></h6>
                            <div style="height: 200px;">
                                <canvas id="timelineChart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Hourly, weekly and recent plays -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">Aantal per uur van de dag voor <?= $h_song ?></h6>
                            <div style="height: 200px;">
                                <canvas id="hourlyChart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">Gemiddelde per dag van de week voor <?= $h_song ?></h6>
                            <div style="height: 200px;">
                                <canvas id="weekdayChart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card h-100">
                        <div class="card-body" style="display: flex; flex-direction: column;">
                            <h6 class="card-title">Recente draaibeurten</h6>
                            <div id="recentContainer" style="flex: 1; overflow-y: auto;">
                                <div class="text-center text-muted py-3">
                                    <div class="spinner-border spinner-border-sm" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <?php endif; ?>

            <?php include 'includes/footer.html'; ?>
        </main>
    </div>

<?php if ($valid): ?>
    <script>
        const API_BASE = '/api.php';
        const ARTIST = <?= json_encode($artist, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) ?>;
        const SONG = <?= json_encode($song, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) ?>;

        function escapeHtml(text) {
            return String(text).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
        }

        function formatDate(raw) {
            return new Date(raw).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short', year: 'numeric' });
        }

        function showError(message) {
            const box = document.getElementById('errorMessage');
            box.textContent = message;
            box.classList.remove('d-none');
        }

        const barOptions = {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
            plugins: { legend: { display: false } }
        };

        fetch(`${API_BASE}/api/tracked?artist=${encodeURIComponent(ARTIST)}&song=${encodeURIComponent(SONG)}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showError('De gegevens zijn nog niet beschikbaar.');
                    console.error('API Error:', data.error);
                    return;
                }
                if (!data.total) {
                    showError(`Er zijn nog geen draaibeurten van ${SONG} vastgelegd.`);
                    document.getElementById('stationsContainer').innerHTML = '';
                    document.getElementById('recentContainer').innerHTML = '';
                }

                // Summary
                document.getElementById('totalPlays').textContent = data.total;
                document.getElementById('uniqueStations').textContent = data.unique_stations;
                document.getElementById('firstTimestamp').textContent = data.first_timestamp ? formatDate(data.first_timestamp) : '...';
                const lastTimestampEl = document.getElementById('lastTimestamp');
                if (data.last_timestamp) {
                    const lastTime = new Date(data.last_timestamp).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit', hour12: false });
                    lastTimestampEl.textContent = formatDate(data.last_timestamp) + ' om ' + lastTime;
                    if (data.last_station) {
                        lastTimestampEl.insertAdjacentHTML('afterend',
                            ` op <a href="/station.php#${encodeURIComponent(data.last_station)}" class="text-decoration-none">${escapeHtml(data.last_station)}</a>`);
                    }
                } else {
                    lastTimestampEl.textContent = '-';
                }
                document.getElementById('averagePerDay').textContent = data.average_per_day !== null
                    ? String(data.average_per_day).replace('.', ',')
                    : '-';

                // Stations: every station with its number of plays and share
                if (data.stations.labels.length) {
                    const top = Math.max(...data.stations.data);
                    const rows = data.stations.labels.map((name, i) => {
                        const count = data.stations.data[i];
                        const share = Math.round(count / top * 100);
                        return `
                            <tr style="border-bottom: 1px solid #dee2e6;">
                                <td class="p-1"><small><a href="/station.php#${encodeURIComponent(name)}" class="text-decoration-none">${escapeHtml(name)}</a></small></td>
                                <td class="p-1" style="width: 35%;">
                                    <div class="progress" style="height: 6px;"><div class="progress-bar" style="width: ${share}%"></div></div>
                                </td>
                                <td class="p-1 text-end"><small>${count}</small></td>
                            </tr>`;
                    }).join('');
                    document.getElementById('stationsContainer').innerHTML =
                        `<table class="table table-sm table-borderless mb-0"><tbody>${rows}</tbody></table>`;
                }

                // Recent plays
                if (data.recent.length) {
                    const rows = data.recent.map(play => {
                        const ts = new Date(play.timestamp_raw);
                        const date = ts.toLocaleDateString('nl-NL', { day: 'numeric', month: 'short' });
                        const time = ts.toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit', hour12: false });
                        return `
                            <tr style="border-bottom: 1px solid #dee2e6;">
                                <td class="p-1" style="white-space: nowrap;"><small class="text-muted">${date}, ${time}</small></td>
                                <td class="p-1"><small><a href="/station.php#${encodeURIComponent(play.station)}" class="text-decoration-none">${escapeHtml(play.station)}</a></small></td>
                            </tr>`;
                    }).join('');
                    document.getElementById('recentContainer').innerHTML =
                        `<table class="table table-sm table-borderless mb-0"><tbody>${rows}</tbody></table>`;
                }

                // Charts, same look as the song page
                new Chart(document.getElementById('timelineChart'), {
                    type: 'line',
                    data: {
                        labels: data.timeline.labels,
                        datasets: [{
                            label: 'Dagelijkse draaibeurten',
                            data: data.timeline.data,
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.3
                        }]
                    },
                    options: barOptions
                });

                new Chart(document.getElementById('hourlyChart'), {
                    type: 'bar',
                    data: {
                        labels: data.hours.labels,
                        datasets: [{
                            label: 'Draaibeurten per uur',
                            data: data.hours.data,
                            backgroundColor: 'rgba(75, 192, 192, 0.6)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: barOptions
                });

                new Chart(document.getElementById('weekdayChart'), {
                    type: 'bar',
                    data: {
                        labels: data.weekdays.labels,
                        datasets: [{
                            label: 'Gemiddeld per weekdag',
                            data: data.weekdays.data,
                            backgroundColor: 'rgba(153, 102, 255, 0.6)',
                            borderColor: 'rgba(153, 102, 255, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: barOptions
                });
            })
            .catch(err => {
                showError('De gegevens konden niet worden geladen.');
                console.error('Failed to load tracked song data:', err);
            });
    </script>
<?php endif; ?>
</body>
</html>
