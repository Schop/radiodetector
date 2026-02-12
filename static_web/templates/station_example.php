<?php
// Example of how to use the templating system
require_once 'includes/template.php';

// Set up template with page data
$template->setPageData('{stationName} - Phil Collins Detector', [
    'station_name' => '{stationName}',
    'api_base' => '/api.php'
]);

// Set page-specific content
$content = '
<h1 id="stationTitle">Loading...</h1>
<h3 class="text-muted mb-4">Radiostation gegevens</h3>

<!-- Summary Stats -->
<div class="row mb-4">
    <div class="col-md-4">
        <div class="card h-100">
            <div class="card-body">
                <h6 class="card-title">Statistieken</h6>
                <table class="compact-stats-table w-100">
                    <tbody>
                        <tr><td>Total Detections</td><td id="totalSongs">...</td></tr>
                        <tr><td>Unique Songs</td><td id="uniqueSongs">...</td></tr>
                        <tr><td>Unique Artists</td><td id="uniqueArtists">...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card h-100">
            <div class="card-body">
                <h6 class="card-title">Uurverdeling</h6>
                <div style="height: 200px;">
                    <canvas id="hourlyChart" width="400" height="200"></canvas>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card h-100">
            <div class="card-body">
                <h6 class="card-title">Weekdagverdeling</h6>
                <div style="height: 200px;">
                    <canvas id="weekdayChart" width="400" height="200"></canvas>
                </div>
            </div>
        </div>
    </div>
</div>

<h3 class="mt-4">All Detections</h3>
<div id="songsContainer">
    <div class="text-center text-muted py-3">
        <div class="spinner-border spinner-border-sm" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <small class="d-block mt-2">Loading songs...</small>
    </div>
</div>
';

$page_script = '
const API_BASE = "/api.php";
const stationName = decodeURIComponent(window.location.hash.substring(1));
// console.log("Station name from URL:", stationName, "Hash:", window.location.hash);

document.getElementById("stationTitle").textContent = stationName;
document.title = document.title.replace("{stationName}", stationName);

// Load station data
// console.log("Loading station data for:", stationName);
fetch(`${API_BASE}/api/station/${encodeURIComponent(stationName)}/data`)
    .then(response => response.json())
    .then(data => {
        // console.log("Station data received:", data);
        document.getElementById("totalSongs").textContent = data.total_songs;
        document.getElementById("uniqueSongs").textContent = data.song_titles.length;
        document.getElementById("uniqueArtists").textContent = data.artists.length;

        // Render table (simplified for example)
        if (data.songs && data.songs.length > 0) {
            const tableHtml = `<table id="stationSongsTable" class="table table-striped">
                <thead><tr><th>Artist</th><th>Song</th><th>Detected</th></tr></thead>
                <tbody>${data.songs.slice(0, 10).map(song => 
                    `<tr><td>${song.artist}</td><td>${song.song}</td><td>${song.timestamp}</td></tr>`
                ).join("")}</tbody></table>`;
            document.getElementById("songsContainer").innerHTML = tableHtml;
            $("#stationSongsTable").DataTable({pageLength: 25});
        }
    })
    .catch(err => console.error("Failed to load station data:", err));

// Load charts (simplified)
fetch(`${API_BASE}/api/station/${encodeURIComponent(stationName)}/charts`)
    .then(response => response.json())
    .then(data => {
        new Chart(document.getElementById("hourlyChart"), {
            type: "bar", data: {labels: data.hours.labels, datasets: [{
                label: "Detections by Hour", data: data.hours.data,
                backgroundColor: "rgba(54, 162, 235, 0.6)"
            }]},
            options: {responsive: true, maintainAspectRatio: false}
        });
        new Chart(document.getElementById("weekdayChart"), {
            type: "bar", data: {labels: data.weekdays.labels, datasets: [{
                label: "Detections by Weekday", data: data.weekdays.data,
                backgroundColor: "rgba(75, 192, 192, 0.6)"
            }]},
            options: {responsive: true, maintainAspectRatio: false}
        });
    })
    .catch(err => console.error("Failed to load chart data:", err));
';

$template->set('content', $content);
$template->set('page_script', $page_script);

// Render the page
$template->display('layout.php');
?>