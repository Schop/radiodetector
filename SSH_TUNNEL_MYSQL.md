# Using SSH Tunnel for MySQL Access

If your hosting provider blocks direct MySQL connections (port 3306), you can use an SSH tunnel.

## Setup SSH Tunnel

### On Windows (PowerShell):
```powershell
# Create SSH tunnel (replace with your SSH credentials)
ssh -L 3307:localhost:3306 your_username@database-5019663848.webspace-host.com

# Keep this terminal open while using the connection
```

### Then update config.yaml:
```yaml
database:
  type: mysql
  mysql_host: localhost  # Changed from remote host
  mysql_port: 3307       # Changed to tunnel port
  mysql_user: dbu5562565
  mysql_password: Passie.19720104
  mysql_database: dbs15302621
```

Now the connection goes through the encrypted SSH tunnel to your server.

## Alternative: Use SQLite Locally, MySQL on Pi

Since your Raspberry Pi is likely closer to the server (or on same network), you could:

1. **Local development**: Use SQLite (`type: sqlite` in config.yaml)
2. **Production (Pi)**: Use MySQL (`type: mysql` in config.yaml on the Pi)

This is actually the most practical approach for development!

## Check with Hosting Provider

Contact your webspace-host.com support and ask:
- "Is remote MySQL access enabled?"
- "What port is MySQL accessible on?"
- "Do I need to whitelist my IP address?"
- "Should I use an SSH tunnel instead?"

Many shared hosts require SSH tunnels or only allow MySQL from their own servers.
