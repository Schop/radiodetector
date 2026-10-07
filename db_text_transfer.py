#!/usr/bin/env python3
"""
Move the SQLite database through channels that corrupt binary files (e.g. a web host's file manager).
The database is compressed and written as plain ASCII (base64) with a checksum, so it survives
any text-mangling download.

On the Pi (next to radio_songs.db and upload_db.py):
    python3 db_text_transfer.py export                # snapshot + encode + upload via SFTP
    python3 db_text_transfer.py export --no-upload    # only write radio_songs.db.b64.txt locally

On the PC, after downloading radio_songs.db.b64.txt from the host:
    python db_text_transfer.py restore radio_songs.db.b64.txt
    python db_text_transfer.py restore radio_songs.db.b64.txt -o my_copy.db --force

The export uses SQLite's backup API, so it is safe while the radio checker is running.
restore refuses to produce a file whose size or SHA-256 doesn't match, or that fails
PRAGMA integrity_check. Delete the .b64.txt from the host once downloaded.
"""

import argparse
import base64
import hashlib
import os
import sqlite3
import sys
import tempfile
import zlib

MAGIC = 'RADIODB-B64-V1'
DEFAULT_TEXT_NAME = 'radio_songs.db.b64.txt'


def integrity(path):
    conn = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
    try:
        return conn.execute('PRAGMA integrity_check').fetchone()[0]
    finally:
        conn.close()


def encode(raw):
    """bytes -> ASCII text: header lines, then zlib+base64 wrapped at 76 columns"""
    payload = base64.b64encode(zlib.compress(raw, 9)).decode('ascii')
    lines = [MAGIC, f'sha256={hashlib.sha256(raw).hexdigest()}', f'size={len(raw)}']
    lines += [payload[i:i + 76] for i in range(0, len(payload), 76)]
    return '\n'.join(lines) + '\n'


def decode(text):
    """ASCII text -> bytes; tolerant of CRLF, a BOM and blank lines, strict about content"""
    lines = [l.strip() for l in text.replace('\r', '').lstrip('﻿').split('\n') if l.strip()]
    if len(lines) < 4 or lines[0] != MAGIC:
        raise ValueError('not a RADIODB-B64-V1 file (header missing or damaged)')
    meta = dict(l.split('=', 1) for l in lines[1:3])
    try:
        raw = zlib.decompress(base64.b64decode(''.join(lines[3:]), validate=True))
    except Exception as e:
        raise ValueError(f'payload is damaged: {e}')
    if len(raw) != int(meta['size']):
        raise ValueError(f"size mismatch: expected {meta['size']}, got {len(raw)}")
    if hashlib.sha256(raw).hexdigest() != meta['sha256']:
        raise ValueError('SHA-256 mismatch: the file was altered in transit')
    return raw


def cmd_export(args):
    if not os.path.exists(args.db):
        sys.exit(f'Database not found: {args.db}')
    with tempfile.TemporaryDirectory() as tmp:
        snap = os.path.join(tmp, 'snapshot.db')
        src = sqlite3.connect(f'file:{args.db}?mode=ro', uri=True)
        dst = sqlite3.connect(snap)
        src.backup(dst)  # consistent copy even while the service is writing
        dst.close()
        src.close()
        result = integrity(snap)
        if result != 'ok':
            sys.exit(f'Snapshot failed integrity_check ({result}); not exporting')
        with open(snap, 'rb') as f:
            raw = f.read()

    text = encode(raw)
    out = args.out
    with open(out, 'w', encoding='ascii', newline='\n') as f:
        f.write(text)
    assert decode(text) == raw  # the encoding must round-trip before anything is uploaded
    print(f'Wrote {out}: {len(raw):,} byte database -> {len(text):,} bytes of text (sha256 {hashlib.sha256(raw).hexdigest()[:12]}...)')

    if args.no_upload:
        print('Skipped upload (--no-upload).')
        return
    import paramiko
    import upload_db  # reuse the SFTP credentials already configured for the database upload
    cfg = upload_db.SFTP_CONFIG
    remote = os.path.join(os.path.dirname(cfg['remote_path']), os.path.basename(out)) or os.path.basename(out)
    transport = paramiko.Transport((cfg['host'], cfg['port']))
    transport.connect(username=cfg['username'], password=cfg['password'])
    sftp = paramiko.SFTPClient.from_transport(transport)
    try:
        sftp.put(out, remote)
        if sftp.stat(remote).st_size != os.path.getsize(out):
            sys.exit('Upload size mismatch - remote file is incomplete')
    finally:
        sftp.close()
        transport.close()
    print(f'Uploaded to {cfg["host"]}:{remote}')
    print('Download it from the host, then run "restore" on your PC. Delete it from the host afterwards.')


def cmd_restore(args):
    if os.path.exists(args.out) and not args.force:
        sys.exit(f'{args.out} already exists (use --force to overwrite, or -o for another name)')
    with open(args.text_file, encoding='utf-8-sig', errors='strict') as f:
        raw = decode(f.read())
    with open(args.out, 'wb') as f:
        f.write(raw)
    result = integrity(args.out)
    if result != 'ok':
        os.remove(args.out)
        sys.exit(f'Restored file failed integrity_check ({result}); removed it')
    conn = sqlite3.connect(f'file:{args.out}?mode=ro', uri=True)
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY 1")]
    counts = {t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}
    conn.close()
    print(f'Restored {args.out}: {len(raw):,} bytes, SHA-256 and integrity_check OK')
    print('Rows per table:', counts)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('export', help='snapshot the database, encode it as text and upload it')
    e.add_argument('--db', default='radio_songs.db')
    e.add_argument('-o', '--out', default=DEFAULT_TEXT_NAME)
    e.add_argument('--no-upload', action='store_true')
    e.set_defaults(func=cmd_export)
    r = sub.add_parser('restore', help='rebuild a database from the downloaded text file')
    r.add_argument('text_file')
    r.add_argument('-o', '--out', default='radio_songs_restored.db')
    r.add_argument('--force', action='store_true')
    r.set_defaults(func=cmd_restore)
    args = ap.parse_args()
    try:
        args.func(args)
    except ValueError as e:
        sys.exit(f'ERROR: {e}')


if __name__ == '__main__':
    main()
