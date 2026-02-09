import urllib.request
import ssl

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://www.radio538.nl/api/tracks/recent'
try:
    response = urllib.request.urlopen(url, context=ctx)
    data = response.read().decode('utf-8')
    print(data)
except Exception as e:
    print(f"Error: {e}")