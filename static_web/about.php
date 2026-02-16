<?php $page_title = 'Over de Phil Collins Detector'; ?>
<?php include 'includes/head.html'; ?>
<body>
    <div class="container-fluid">
        <main>
            <?php include 'includes/nav.html'; ?>

            <div class="row mb-4">
                <div class="col-md-9">
                    <h1>Over de Phil Collins Detector</h1>
                    
                    <div class="card mb-3">
                        <div class="card-body">
                            <p>Je zet de radio aan. Eerst verkeersinformatie, dan een reclame, en dan… ja hoor: die onvermijdelijke drumfill. Was dat nou wéér Phil Collins?
                                Ik heb het gevoel dat hij wel heel vaak op de radio te horen is, en het leek me leuk om dat gevoel eens te testen met cijfers in plaats van zuchten.
                                Niet omdat ik iets tegen de persoon Phil Collins heb — integendeel, alle respect — maar mijn oren zijn het niet altijd eens met zijn muzikale keuzes.
                            </p>
                            <p>Zo ontstond de Phil Collins Detector: een speels, lichtelijk obsessief project dat bijhoudt hoe vaak Phil Collins voorbij komt op Nederlandse radiozenders. Geen grote kruistocht, wel een knipoog en een dosis data. De site luistert mee met publieke “now playing”-informatie, telt de draaibeurten, en zet alles netjes op een rij: per zender, per dag, per uur. Je ziet trends, piekmomenten, en kunt zelf ontdekken op welke zenders je de grootste kans hebt om “In the Air Tonight” of “Sussudio” te horen terwijl je net je boterham smeert.
                            </p>
                            <h5>Belangrijk om te weten:
                            </h5>
                            <p>Dit is geen anti-Phil-campagne. Ik heb niets tegen de persoon Phil Collins; mijn smaak en die van de radiozenders botsen alleen soms.
                                De detector is bedoeld voor plezier, nieuwsgierigheid en een beetje radiokennis. Lach mee, discussieer gerust, en verwonder je over hoe vaak bepaalde hits blijven terugkomen.
                                Data is eerlijk, maar niet onfeilbaar. Zie je een vreemde registratie of mis je een nummer? Laat het weten — dan schaaf ik bij.
                                Dus: klik rond, vergelijk zenders, en kijk hoe vaak het nou écht gebeurt. Misschien bevestigt het je gevoel. Misschien verrast het je compleet. En mocht die drumfill weer eens door je keuken galmen, weet dan: de Phil Collins Detector telt mee.    
                            </p>
                     </div>
                    </div>

                    <div class="card mb-3">
                        <div class="card-body">
                            <h5>Technische details</h5>
                            <ul>
                                <li>De Phil Collins Detector draait op minimale hardware, een Raspberry Pi Zero van een paar tientjes, in mijn garage.</li>
                                <li>Alle detecties worden ge-upload naar een webserver, die het laat zien op <a href="https://philcollinsdetector.nl">philcollinsdetector.nl</a>.</li>
                            </ul>
                        </div>
                    </div>
                    <div class="card mb-3">
                        <div class="card-body">
                            <h5>Veel gestelde vragen</h5>
                            <p><strong>Kun je ook een Bonnie St. Claire detector maken?</strong> Ja, dat is zelfs vrij eenvoudig, ook voor andere artiesten als Snollebollekes, Maroon 5 of zelfs Taylor Swift. Alle code is open source en beschikbaar op <a href="https://github.com/Schop/radiodetector" target="_blank">GitHub</a>. En als het niet lukt, wil ik je ook nog wel helpen</p>
                            <p>Je kunt ook even contact opnemen via <a href="mailto:john.schop@gmail.com" target="_blank">een e-mail</a> of (als je hier ervaring mee hebt) een issue openen in de <a href="https://github.com/Schop/radiodetector" target="_blank">GitHub repository</a>.</p>  
                        </div>
                    </div>                    

                </div>
                <div class="col-md-3">
                    <div class="card mb-3">
                        <div class="card-body">
                            <h6>Contact</h6>
                            <p class="small mb-0">Feedback of verbeteringen, of andere vragen? Open een issue in de <a href="https://github.com/Schop/radiodetector" target="_blank">GitHub repository</a> of stuur een <a href="mailto:john.schop@gmail.com" target="_blank">e-mail</a>.</p>
                        </div>
                    </div>
                    <div class="card mb-3">
                        <div class="card-body">
                            <h6>Doneren</h6>
                            <p class="small mb-0">De Phil Collins Detector kan natuurlijk niet helemaal voor niets draaien. Vind je het leuk en wil je een bijdrage leveren? Dat kan via de knop hieronder. </p>
                            <br>
                            <form action="https://www.paypal.com/donate" method="post" target="_top">
                            <input type="hidden" name="hosted_button_id" value="2L7TXP67GNGD4" />
                            <input type="image" src="https://www.paypalobjects.com/nl_NL/NL/i/btn/btn_donate_LG.gif" border="0" name="submit" title="PayPal - The safer, easier way to pay online!" alt="Doneren met PayPal-knop" />
                            <img alt="" border="0" src="https://www.paypal.com/nl_NL/i/scr/pixel.gif" width="1" height="1" />
                            </form>

                        </div>
                    </div>
                </div>
            </div>

            <?php include 'includes/footer.html'; ?>
        </main>
    </div>

    <script>
        const API_BASE = '/api.php'; // same mechanism as on other static pages

        // Fetch index-data and update the small nav counter (todayCountnav)
        fetch(`${API_BASE}/api/index-data`)
            .then(response => response.json())
            .then(data => {
                const el = document.getElementById('todayCountnav');
                if (el) el.textContent = data.today_count || '0';
            })
            .catch(() => {
                /* ignore errors silently */
            });

        // Highlight active nav item for this page
        const navLink = document.querySelector('a[href="about.php"]');
        if (navLink) navLink.classList.add('active');
    </script>
</body>
</html>