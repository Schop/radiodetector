<?php $page_title = 'Alle Detecties - Phil Collins Detector'; ?>
<?php include 'includes/head.html'; ?>

<body>
    <div class="container-fluid">
        <main>
            <?php include 'includes/nav.html'; ?>

            <h1>Alle Phil Collins Detecties</h1>
            <p class="text-muted">Complete lijst van alle gedetecteerde Phil Collins nummers op Nederlandse radio</p>

            <!-- Results -->
            <div id="detectionsContainer">
                <div class="text-center text-muted py-3">
                    <div class="spinner-border spinner-border-sm" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <small class="d-block mt-2">Loading detections...</small>
                </div>
            </div>

            <?php include 'includes/footer.html'; ?>
        </main>
    </div>

    <script>
        const API_BASE = '/api.php'; // Adjust this path as needed

        // Load index data
        // console.log('Loading detections data...');
        fetch(`${API_BASE}/api/index-data`)
            .then(response => {
                // console.log('Fetch response received:', response);
                return response.json();
            })
            .then(data => {
                // console.log('Data received:', data);

                if (data.songs && data.songs.length > 0) {
                    // Render detections table
                    const tableHtml = `
                        <div class="card">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <h5 class="card-title mb-0">Alle Detecties (${data.total_count})</h5>
                                    <a href="${API_BASE}/api/export" class="btn btn-primary">Export CSV</a>
                                </div>
                                <table id="detectionsTable" class="table table-striped table-hover display">
                                    <thead class="table-light">
                                        <tr>
                                            <th>Detected</th>
                                            <th>Station</th>
                                            <th>Artist</th>
                                            <th>Song</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${data.songs.map(song => {
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
                                            <tr>
                                                <td class="timestamp" data-order="${song.timestamp_raw}">${compactTime}</td>
                                                <td><a href="/station.php#${encodeURIComponent(song.station)}" class="station-link">${song.station}</a></td>
                                                <td>${song.artist}</td>
                                                <td><a href="/song.php#${encodeURIComponent(song.song)}" class="station-link">${song.song}</a></td>
                                            </tr>
                                        `}).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    `;
                    document.getElementById('detectionsContainer').innerHTML = tableHtml;
                    document.getElementById('todayCountnav').textContent = data.today_count || '0';
                    // Initialize DataTable
                    $('#detectionsTable').DataTable({
                        order: [[0, 'desc']],
                        pageLength: 50,
                        lengthMenu: [[25, 50, 100, 250], [25, 50, 100, 250]],
                        responsive: true,
                        autoWidth: false,
                        language: {
                            search: "Zoek in alle kolommen:",
                            lengthMenu: "Toon _MENU_ items",
                            info: "Toont _START_ tot _END_ van de _TOTAL_ detecties",
                            paginate: {
                                first: "Eerste",
                                last: "Laatste",
                                next: "Volgende",
                                previous: "Vorige"
                            }
                        }
                    });
                } else {
                    document.getElementById('detectionsContainer').innerHTML = `
                        <div class="alert alert-info text-center" role="alert">
                            <h4 class="alert-heading">Geen detecties gevonden</h4>
                            <p>Zorg ervoor dat <code>main.py</code> op de achtergrond draait om liedjes van radiostations te verzamelen.</p>
                        </div>
                    `;
                }
            })
            .catch(err => {
                console.error('Failed to load detections data:', err);
                document.getElementById('detectionsContainer').innerHTML = `
                    <div class="alert alert-danger text-center" role="alert">
                        <h4 class="alert-heading">Fout bij het laden van gegevens</h4>
                        <p>Controleer de serverconfiguratie.</p>
                    </div>
                `;
            });

        // Set active nav link
        const navLink = document.querySelector('a[href="/"]');
        if (navLink) {
            navLink.classList.add('active');
        }

        

    </script>
</body>
</html>