<?php
$page_title = 'Wat draait er nu op de Nederlandse radio?';
$page_description = 'Het laatst gedetecteerde nummer bij elk gecontroleerd Nederlands radiostation, elke minuut bijgewerkt.';
require_once __DIR__ . '/includes/stations_now.php';
$snapshot = load_stations_now(__DIR__ . '/stations_now.json', time());
$esc = fn($text) => htmlspecialchars((string)$text, ENT_QUOTES, 'UTF-8');
?>
<?php include 'includes/head.html'; ?>

<body>
    <div class="container-fluid">
        <main>
            <?php include 'includes/nav.html'; ?>

            <h1>Nu op de radio</h1>
            <p class="text-muted">Het laatst gedetecteerde nummer bij elk gecontroleerd radiostation. Nummers van Phil Collins en Genesis zijn groen gemarkeerd; zenders die al meer dan 10 minuten geen nieuw nummer of geen gegevens meer doorgeven zijn grijs.</p>

            <?php if ($snapshot === null): ?>
            <div class="alert alert-info text-center" role="alert">
                Er is nog geen overzicht beschikbaar. Dit verschijnt zodra de controle zich meldt.
            </div>
            <?php else: ?>
            <div class="card">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h5 class="card-title mb-0">Zenders (<?= count($snapshot['rows']) ?>)</h5>
                        <small class="text-muted">Bijgewerkt om <?= $esc((new DateTime('@' . $snapshot['received_at']))->setTimezone(new DateTimeZone('Europe/Amsterdam'))->format('H:i:s')) ?></small>
                    </div>
                    <table id="nowTable" class="table table-striped table-hover">
                        <thead class="table-light">
                            <tr>
                                <th>Zender</th>
                                <th>Artiest</th>
                                <th>Nummer</th>
                                <th>Gezien sinds</th>
                            </tr>
                        </thead>
                        <tbody>
                        <?php foreach ($snapshot['rows'] as $row): ?>
                            <tr class="<?= trim(($row['highlight'] ? 'table-success fw-semibold ' : '') . ($row['stale'] ? 'nu-stale' : '')) ?>">
                                <td><a href="/station.php#<?= rawurlencode($row['station']) ?>" class="text-decoration-none"><?= $esc($row['station']) ?></a></td>
                                <?php if ($row['artist'] === null): ?>
                                <td class="text-muted">geen gegevens</td>
                                <td></td>
                                <td data-order="999999"></td>
                                <?php else: ?>
                                <td><?= $esc($row['artist']) ?></td>
                                <td>
                                    <?php if ($row['highlight']): ?>
                                    <a href="/song.php#<?= rawurlencode($row['song']) ?>" class="text-decoration-none"><?= $esc($row['song']) ?></a>
                                    <?php else: ?>
                                    <?= $esc($row['song']) ?>
                                    <?php endif; ?>
                                </td>
                                <td data-order="<?= (int)$row['since_s'] ?>" class="<?= $row['stale'] ? 'text-muted' : '' ?>">
                                    <?= $row['since_s'] === null ? '-' : $esc(nu_duration($row['since_s'])) ?>
                                    <?php if ($row['no_data']): ?><small>(geen recente gegevens)</small>
                                    <?php elseif ($row['unchanged']): ?><small>(al even hetzelfde)</small><?php endif; ?>
                                </td>
                                <?php endif; ?>
                            </tr>
                        <?php endforeach; ?>
                        </tbody>
                    </table>
                    <p class="text-muted small mb-0">&lsquo;Gezien sinds&rsquo; is het moment waarop de controle dit nummer voor het eerst zag, niet per se het moment waarop het begon.</p>
                </div>
            </div>
            <?php endif; ?>

            <?php include 'includes/footer.html'; ?>
        </main>
    </div>

    <style>
        /* no new data from this station for a while: fade the whole row a little */
        #nowTable tr.nu-stale > * { opacity: .55; }
    </style>

    <script>
        <?php if ($snapshot !== null): ?>
        $('#nowTable').DataTable({
            paging: false,
            order: [[0, 'asc']],
            responsive: true,
            autoWidth: false,
            language: {
                search: "Zoek:",
                info: "",
                infoEmpty: "",
                infoFiltered: "(gefilterd uit _MAX_ zenders)",
                zeroRecords: "Geen zenders gevonden"
            }
        });
        <?php endif; ?>
        // the checker reports every minute; reload so the page keeps up
        setTimeout(() => location.reload(), 60000);
    </script>
</body>
</html>
