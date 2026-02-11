# RadioChecker Static Web Setup

This directory contains the static web files for hosting the RadioChecker frontend.

## Files

- `index.html` - Main dashboard page
- `station.html` - Station detail page
- `static/` - CSS, images, etc.

## Setup Instructions

1. **Upload Static Files:**
   - Upload all files in this directory to your hosting provider's public web directory (e.g., `public_html` or `www`).
   - Ensure the `static/` directory is uploaded with its contents.

2. **Upload CGI Script:**
   - Upload `data_api.py` to your hosting provider's `cgi-bin/` directory.
   - Make the script executable: `chmod 755 data_api.py`
   - Ensure Python 3 is available on the server.

3. **Database:**
   - Upload the `radio_songs.db` SQLite database to a location accessible by the CGI script.
   - Update the `DB_PATH` in `data_api.py` to point to the correct path.

4. **Configuration:**
   - If your CGI path is different, update `API_BASE` in the HTML files.
   - Example: If CGI is at `/cgi-bin/data_api.py`, keep as is.

5. **Test:**
   - Visit your site's `index.html` to see the dashboard.
   - Click on stations/artists/songs to view details.

## Notes

- The pages use URL fragments (#) to pass parameters for station/song/artist names.
- No admin pages are included, as requested.
- Data is fetched via AJAX from the CGI script.