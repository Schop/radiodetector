# Station Configuration Guide

Station configurations are stored in `config.yaml` which supports comments with `#`.

## YAML Format

**config.yaml** makes it easy to temporarily disable stations by commenting them out:

```yaml
# Radio Station Configuration
# Comment out stations with # to disable them

# Target artists and songs to check
target_artists:
  - Phil Collins
  - Genesis

target_songs:
  - Africa

relisten:
  Arrow Classic Rock: arrow
  FunX: funx
  # Juize: juize        # Commented out - won't be monitored
  Veronica: veronica
  Sky Radio: skyradio

myonlineradio:
  Radio 10: radio-10
  # Sky Radio: sky-radio   # Temporarily disabled

playlist24:
  KINK: kink-playlist
  NPO 3FM: 3fm-playlist
  # Aardschok: aardschok-playlist  # Disabled
```

**To disable a station:** Just add `#` at the start of the line  
**To re-enable:** Remove the `#`

## Fields

### `target_artists`
List of artist names to monitor. When any song by these artists is detected, you'll get a red alert with a beep.

```yaml
target_artists:
  - Phil Collins
  - Genesis
  - Toto
```

### `target_songs`
List of song titles to monitor. When any of these songs are detected (regardless of artist), you'll get a red alert with a beep.

```yaml
target_songs:
  - Africa
  - In The Air Tonight
```

### `relisten`
Lists stations to monitor from relisten.nl homepage. The application scrapes https://www.relisten.nl/ and filters to only these stations.

**The slug values are not used** (homepage shows all stations), but keep them for reference:

```yaml
Veronica: veronica     # Monitor this station from homepage
Radio 10: radio10      # Monitor this station from homepage  
# Juize: juize         # Skip this station
```

To monitor all stations from relisten.nl, list them all. To exclude specific stations, comment them out with `#`.

### `myonlineradio`
Maps station display names to their myonlineradio.nl URL slugs. These are used when fetching station data from https://myonlineradio.nl/[slug]/playlist

**Example:**
```yaml
Radio 10: radio-10     # → https://myonlineradio.nl/radio-10/playlist
Sky Radio: sky-radio   # → https://myonlineradio.nl/sky-radio/playlist
```

### `playlist24`
Maps station display names to their playlist24.nl URL slugs. These are used when fetching station data from https://playlist24.nl/[slug]/

**Example:**
```yaml
KINK: kink-playlist       # → https://playlist24.nl/kink-playlist/
NPO 3FM: 3fm-playlist     # → https://playlist24.nl/3fm-playlist/
```

## How to Edit (YAML)

### Disabling a station
Just add `#` at the start of the line:
```yaml
relisten:
  Arrow Classic Rock: arrow
  # Juize: juize        # Temporarily disabled
  Veronica: veronica
```

### Re-enabling a station
Remove the `#`:
```yaml
relisten:
  Arrow Classic Rock: arrow
  Juize: juize          # Now active again
  Veronica: veronica
```

### Adding a new station

**For relisten.nl:**
1. Find the station's slug from https://www.relisten.nl (check dropdown menu)
2. Add to the `relisten` section:
   ```yaml
   Station Name: station-slug
   ```

**For myonlineradio.nl:**
1. Find the station's slug on https://myonlineradio.nl
2. Add to the `myonlineradio` section:
   ```yaml
   Station Name: station-slug
   ```

**For playlist24.nl:**
1. Find the station in the dropdown menu on https://playlist24.nl
2. Add to the `playlist24` section:
   ```yaml
   Station Name: station-slug
   ```

### Removing a station
1. Delete the line from the relevant section (`relisten`, `myonlineradio`, or `playlist24`)
2. Or simply comment it out with `#` to keep the configuration

## Finding Station Names/Slugs

### relisten.nl
Station names must match exactly as they appear on the https://www.relisten.nl/ homepage. The slug value can be anything (it's not used).

To find station names:
1. Visit https://www.relisten.nl
2. Copy the station name exactly as shown
3. Add to YAML: `Station Name: placeholder`

### myonlineradio.nl
1. Visit https://myonlineradio.nl
2. Search for the station
3. The URL will be: `https://myonlineradio.nl/[SLUG]/playlist`

### playlist24.nl
1. Visit https://playlist24.nl
2. Check the dropdown menu for available stations
3. The URL will be: `https://playlist24.nl/[SLUG]/`

## Operation Modes

- **Primary:** Uses relisten.nl homepage scraping (14 stations)
- **Secondary Fallback:** If relisten.nl is down, switches to myonlineradio.nl (18 unique stations)
- **Tertiary Fallback:** If both above fail or return few results, adds playlist24.nl (13 unique stations)

## Notes

- The application will automatically reload the configuration on restart
- Invalid YAML will cause the application to use an empty configuration
- Use `#` to comment out stations without deleting them
- The system automatically avoids checking duplicate stations across sources
- Currently configured: **14 relisten stations**, **18 myonlineradio stations**, **13 playlist24 stations**
