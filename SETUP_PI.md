# Radio Checker - Pi Zero Setup Instructions

## Installation on Raspberry Pi Zero

### 1. Clone and Setup

```bash
# Update system
sudo apt update
sudo apt install git python3-pip -y

# Clone repository
cd ~
git clone https://github.com/yourusername/radiochecker.git
cd radiochecker

# Install Python dependencies
pip3 install -r requirements.txt
```

### 2. Test Run (Optional)

```bash
# Test the radio checker
python3 main.py

# In another terminal, test the web interface
python3 web_app.py
```

Press `Ctrl+C` to stop when done testing.

### 3. Install as Systemd Services

**Important:** The service files use username `schop`. If your username is different, edit the service files first and replace `schop` with your username.

```bash
# Copy service files to systemd directory
sudo cp radiochecker.service /etc/systemd/system/
sudo cp radiochecker-web.service /etc/systemd/system/

# Reload systemd to recognize new services
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable radiochecker
sudo systemctl enable radiochecker-web

# Start services now
sudo systemctl start radiochecker
sudo systemctl start radiochecker-web
```

### 4. Check Status

```bash
# Check if services are running
sudo systemctl status radiochecker
sudo systemctl status radiochecker-web

# View live logs
sudo journalctl -u radiochecker -f

# Or view the log file directly
tail -f ~/radiochecker/radio.log
```

### 5. Access Web Interface

Open a browser and go to:
- From Pi: `http://localhost:5000`
- From another device: `http://<pi-ip-address>:5000`

The web interface includes:
- **Dashboard** - View all detected songs
- **Logs** - Real-time monitoring of the radio checker (auto-refreshes every 5 seconds)

### Managing the Services

```bash
# Stop services
sudo systemctl stop radiochecker
sudo systemctl stop radiochecker-web

# Restart services (e.g., after updating code)
sudo systemctl restart radiochecker
sudo systemctl restart radiochecker-web

# Disable auto-start on boot
sudo systemctl disable radiochecker
sudo systemctl disable radiochecker-web

# View logs
sudo journalctl -u radiochecker -n 100
sudo journalctl -u radiochecker-web -n 100
```

### Updating Code

```bash
# Pull latest changes from GitHub
cd ~/radiochecker
git pull

# Restart services to apply changes
sudo systemctl restart radiochecker
sudo systemctl restart radiochecker-web
```

## Remote Access with Tailscale

Tailscale creates a secure private network so you can access your Pi from anywhere (phone, laptop, etc.) without port forwarding or exposing your home network.

### Install Tailscale

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale and authenticate
sudo tailscale up
```

This will show a URL - open it in a browser to authenticate with your Tailscale account (create one if needed - it's free).

### Get Your Pi's Tailscale IP

```bash
# Find your Tailscale IP address
tailscale ip -4
```

You'll get an IP like `100.x.x.x` - this is your Pi's permanent address on your Tailscale network.

### Access the Web Interface

On any device with Tailscale installed:
1. Install Tailscale app on your phone/laptop
2. Connect to your Tailscale network
3. Open browser and go to: `http://100.x.x.x:5000` (use your Pi's Tailscale IP)

**Benefits:**
- Access from anywhere with internet
- Secured encrypted connection
- No router configuration needed
- Works on same WiFi or remote
- Very lightweight (~10-20MB RAM)

## Running on Windows

The code works on Windows too! Just run:

```powershell
# Start the radio checker (output to console)
python main.py

# Or redirect to log file
python main.py > radio.log 2>&1

# In another terminal, start the web interface
python web_app.py
```

**Note:** When running manually, logs appear in the console. If you want to save them to a file, use output redirection as shown above.

## Log Files

- `radio.log` - Main radio checker logs
- `web.log` - Web server logs (Pi only)
- `radio_songs.db` - SQLite database with detected songs

## Configuration

The web interface provides a Settings page where you can:
- Add/remove artists and songs to track
- Enable/disable individual radio stations
- Set priority for MyOnlineRadio stations
- Add new stations to monitor

**First Run:** `config.yaml` is used to populate the database initially. After that, all settings are managed through the web interface at `http://your-pi-ip:5000/settings` (or via Tailscale).

**Hot Reload:** Changes made via the web interface are automatically picked up within 5 minutes - no need to restart services.

## Troubleshooting

### Service won't start
```bash
# Check for errors
sudo journalctl -u radiochecker -n 50
```

### Can't access web interface
```bash
# Check if service is running
sudo systemctl status radiochecker-web

# Check if port 5000 is in use
sudo netstat -tulpn | grep 5000
```

### Database not found
Make sure the radio checker service has run at least once to create `radio_songs.db`.

## Uninstall

```bash
# Stop and disable services
sudo systemctl stop radiochecker radiochecker-web
sudo systemctl disable radiochecker radiochecker-web

# Remove service files
sudo rm /etc/systemd/system/radiochecker.service
sudo rm /etc/systemd/system/radiochecker-web.service

# Reload systemd
sudo systemctl daemon-reload

# Remove project directory
rm -rf ~/radiochecker
```
