# RadioChecker Static Web Setup

This directory contains the static web files for hosting the RadioChecker frontend using PHP and JavaScript.

## Files

- `index.html` - Main dashboard page
- `station.html` - Station detail page
- `api.php` - PHP API script for serving data
- `static/` - CSS and images
- `README.md` - Setup instructions

## Setup Instructions

1. **Upload Static Files:**
   - Upload all files in this directory to your hosting provider's public web directory (e.g., `public_html` or `www`).
   - Ensure the `static/` directory is uploaded with its contents.

2. **PHP Requirements:**
   - Your hosting must support PHP (most shared hosts do).
   - PHP must have PDO and SQLite extensions enabled.
   - No special permissions needed - PHP files run automatically.

3. **Database:**
   - Upload the `radio_songs.db` SQLite database to the same directory as `api.php`.
   - Update the `$db_path` variable in `api.php` if needed.

4. **Configuration:**
   - The API endpoints are now at `/api.php/api/...` instead of CGI paths.
   - No additional configuration needed.

5. **Test:**
   - Visit your site's `index.html` to see the dashboard.
   - Click on stations to view details.

## Advantages of PHP Approach

- **Easier Setup:** No CGI configuration or executable permissions needed
- **Better Compatibility:** PHP is supported on virtually all web hosts
- **Simpler Deployment:** Just upload files, no server configuration
- **Direct Database Access:** PHP can read SQLite databases natively
- **Better Performance:** No subprocess overhead like CGI

## Notes

- The pages use URL fragments (#) to pass parameters for station/song/artist names.
- No admin pages are included, as requested.
- Data is fetched via AJAX from the PHP API.