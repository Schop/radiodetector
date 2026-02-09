# Station Configuration Guide

Station configurations are stored in `stations.yaml` which supports comments with `#`.

## YAML Format

**stations.yaml** makes it easy to temporarily disable stations by commenting them out:

```yaml
# Radio Station Configuration
# Comment out stations with # to disable them

relisten:
  Arrow Classic Rock: arrow
  FunX: funx
  # Juize: juize        # Commented out - won't be monitored
  Veronica: veronica
  Sky Radio: skyradio

myonlineradio:
  Radio 10: radio-10
  # Sky Radio: sky-radio   # Temporarily disabled
  
priority_stations:
  - Radio 10
  - Sky Radio
  # - Juize    # Not monitored when commented
```

**To disable a station:** Just add `#` at the start of the line  
**To re-enable:** Remove the `#`

## Fields

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

### `priority_stations`
List of station names to check first during myonlineradio.nl fallback mode. These should be stations that:
- Are available on both relisten.nl and myonlineradio.nl
- Are popular/major national stations
- You want to monitor with lowest latency during fallback

**Current priority stations (22):**
Stations that overlap between both sources for seamless fallback.

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

3. Optionally add to `priority_stations` if it's a major station:
   ```yaml
   priority_stations:
     - Station Name
   ```

### Removing a station
1. Delete the line from the relevant section (`relisten` or `myonlineradio`)
2. Remove from `priority_stations` if present
3. Or simply comment it out with `#` to keep the configuration

### Changing station priority
Reorder entries in the `priority_stations` list. Stations at the top are checked first during fallback.

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

## Operation Modes

- **Primary:** Uses relisten.nl individual station playlists (40 stations)
- **Fallback:** If relisten.nl is down, switches to myonlineradio.nl (89 stations)
- **Priority:** During fallback, checks priority stations first for faster coverage

## Notes

- Station names in `priority_stations` must exactly match those in `myonlineradio`
- The application will automatically reload the configuration on restart
- Invalid YAML will cause the application to use an empty configuration
- Use `#` to comment out stations without deleting them
- Currently configured: **40 relisten stations**, **89 myonlineradio stations** (22 priority)
