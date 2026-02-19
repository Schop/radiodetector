"""Simple Bluesky poster helper.

Usage:
1) Set environment variables `BLUESKY_IDENTIFIER` and `BLUESKY_PASSWORD`,
   or `BLUESKY_ACCESS_JWT` (if you already have a session token).
2) Optionally set `BLUESKY_SERVICE` (defaults to https://bsky.social).

Example:
    from bluesky_post import post_song
    post_song(artist='Artist', song='Title', station='Station Name')

Notes:
- This is a minimal helper that uses the XRPC endpoints. You may need
  to adapt authentication details for your account or use an official
  client library for advanced workflows.
"""
from typing import Optional
import os
import requests
from datetime import datetime

# Replace these placeholder values before publishing or running on your Pi.
# Do NOT commit real credentials to version control.
DEFAULT_IDENTIFIER = 'john.schop@gmx.com'
DEFAULT_PASSWORD = 'nrdo-4fhd-fz6k-m75n'


class BlueskyPoster:
    def __init__(self,
                 service: Optional[str] = None,
                 identifier: Optional[str] = None,
                 password: Optional[str] = None,
                 access_jwt: Optional[str] = None):
        self.service = service or os.getenv('BLUESKY_SERVICE', 'https://bsky.social')
        self.identifier = identifier or os.getenv('BLUESKY_IDENTIFIER') or DEFAULT_IDENTIFIER
        self.password = password or os.getenv('BLUESKY_PASSWORD') or DEFAULT_PASSWORD
        self.access_jwt = access_jwt or os.getenv('BLUESKY_ACCESS_JWT')
        self.headers = {}
        self.did: Optional[str] = None

        if self.access_jwt:
            self.headers = {'Authorization': f'Bearer {self.access_jwt}'}

    def create_session(self) -> bool:
        """Create a session using identifier/password and store access JWT.

        Returns True if session created or access JWT already present.
        """
        if self.access_jwt:
            return True

        if not (self.identifier and self.password):
            raise ValueError('No credentials: set BLUESKY_IDENTIFIER and BLUESKY_PASSWORD or BLUESKY_ACCESS_JWT')

        url = f"{self.service}/xrpc/com.atproto.server.createSession"
        payload = {'identifier': self.identifier, 'password': self.password}
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            # The response typically contains `accessJwt`
            token = data.get('accessJwt') or data.get('accessJwt')
            if token:
                self.access_jwt = token
                self.headers = {'Authorization': f'Bearer {self.access_jwt}'}
                # store did if returned (needed for repo.createRecord fallback)
                self.did = data.get('did') or data.get('handle')
                return True

        raise RuntimeError(f'Failed to create Bluesky session: {resp.status_code} {resp.text}')

    def post(self, text: str) -> dict:
        """Post `text` to Bluesky feed. Returns response JSON on success.

        This will attempt to create a session if no JWT is available.
        """
        if not self.access_jwt:
            self.create_session()

        # First try the high-level feed.post endpoint
        url = f"{self.service}/xrpc/app.bsky.feed.post"
        payload = {'text': text}
        resp = requests.post(url, json=payload, headers=self.headers, timeout=15)
        if resp.status_code in (200, 201):
            try:
                return resp.json()
            except Exception:
                return {'status': 'ok', 'raw': resp.text}

        # Inspect JSON error if available
        err_json = None
        try:
            err_json = resp.json()
        except Exception:
            err_json = None

        # If the server doesn't support app.bsky.feed.post, fallback to createRecord
        if resp.status_code == 404 or (isinstance(err_json, dict) and err_json.get('error') == 'XRPCNotSupported'):
            return self.create_record(text)

        raise RuntimeError(f'Failed to post to Bluesky: {resp.status_code} {resp.text}')

    def create_record(self, text: str) -> dict:
        """Fallback to create a repo record in `app.bsky.feed.post` collection."""
        if not self.did:
            # Try to create a session to obtain DID
            self.create_session()

        if not self.did:
            raise RuntimeError('No DID available for createRecord fallback')

        url = f"{self.service}/xrpc/com.atproto.repo.createRecord"
        payload = {
            'repo': self.did,
            'collection': 'app.bsky.feed.post',
            'record': {
                'createdAt': datetime.utcnow().isoformat() + 'Z',
                'text': text,
            }
        }

        resp = requests.post(url, json=payload, headers=self.headers, timeout=15)
        if resp.status_code in (200, 201):
            try:
                return resp.json()
            except Exception:
                return {'status': 'ok', 'raw': resp.text}

        raise RuntimeError(f'Failed to create record on Bluesky: {resp.status_code} {resp.text}')


def post_song(artist: str, song: str, station: Optional[str] = None, tag: Optional[str] = 'nowplaying') -> bool:
    """Helper to post a formatted "now playing" message.

    Returns True on success. Raises on error.
    """
    poster = BlueskyPoster()
    parts = []
    if station:
        parts.append(f"{artist} gedetecteerd op {station}:")
    parts.append(f"{song} - ")
    # Append site link (no tag)
    parts.append('https://philcollinsdetector.nl')

    text = ' '.join(parts)
    poster.post(text)
    return True


if __name__ == '__main__':
    # Quick local test when run directly (requires env vars)
    try:
        post_song('Test Artist', 'Test Song', station='Test Station')
        print('Posted test song to Bluesky (check your account).')
    except Exception as e:
        print('Error posting to Bluesky:', e)
