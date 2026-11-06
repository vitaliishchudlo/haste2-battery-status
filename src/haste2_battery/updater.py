"""Update discovery and download helpers. Platform independent, stdlib only.

Releases are tagged per platform (`vX.Y.Z-win`, `vX.Y.Z-mac`); each app only looks at
tags with its own suffix, so a macOS-only release never notifies Windows users.
"""
import hashlib
import json
import os
import re
import ssl
import threading
import urllib.error
import urllib.request

REPO = 'vitaliishchudlo/haste2-battery-status'
API = f'https://api.github.com/repos/{REPO}/releases?per_page=30'
DOWNLOAD_PREFIX = f'https://github.com/{REPO}/releases/download/'
USER_AGENT = 'Haste2Battery-updater'
TIMEOUT = 20


def _context():
    """System certificates plus the bundled certifi set: frozen apps often lack usable roots."""
    context = ssl.create_default_context()
    try:
        import certifi
        context.load_verify_locations(certifi.where())
    except (ImportError, OSError):
        pass
    return context


class Release:
    def __init__(self, version, tag, assets):
        self.version = version
        self.tag = tag
        self.assets = assets      # {file name: download url}

    def __repr__(self):
        return f'Release({self.tag})'


def parse_version(text):
    """'1.2.10' -> (1, 2, 10); None if it is not a plain dotted number."""
    if not re.fullmatch(r'\d+(\.\d+){1,3}', text or ''):
        return None
    return tuple(int(part) for part in text.split('.'))


def newest_release(releases, suffix):
    """Highest-versioned published release whose tag is `v<version><suffix>`."""
    best = None
    for item in releases:
        tag = item.get('tag_name') or ''
        if not (tag.startswith('v') and tag.endswith(suffix))                 or item.get('draft') or item.get('prerelease'):
            continue
        number = tag[1:-len(suffix)]
        version = parse_version(number)
        if version is None:
            continue
        assets = {asset['name']: asset['browser_download_url']
                  for asset in item.get('assets', [])
                  if str(asset.get('browser_download_url', '')).startswith(DOWNLOAD_PREFIX)}
        if best is None or version > best[0]:
            best = (version, Release(number, tag, assets))
    return best[1] if best else None


class ReleaseFeed:
    """Fetches the release list; uses ETag so unchanged answers (HTTP 304) are free."""

    def __init__(self):
        self.etag = None
        self.cached = []

    def fetch(self):
        request = urllib.request.Request(API, headers={
            'User-Agent': USER_AGENT, 'Accept': 'application/vnd.github+json'})
        token = os.environ.get('HASTE2_GITHUB_TOKEN')   # CI only: avoids the shared-IP rate limit
        if token:
            request.add_header('Authorization', 'Bearer ' + token)
        if self.etag:
            request.add_header('If-None-Match', self.etag)
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT, context=_context()) as response:
                self.cached = json.loads(response.read().decode('utf-8'))
                self.etag = response.headers.get('ETag')
        except urllib.error.HTTPError as error:
            if error.code != 304:
                raise
        return self.cached


def check(feed, suffix, current):
    """The newer release for this platform, or None if we are up to date."""
    release = newest_release(feed.fetch(), suffix)
    if release is None:
        return None
    have, found = parse_version(current), parse_version(release.version)
    return release if have and found and found > have else None


def _open(url):
    if not url.startswith(DOWNLOAD_PREFIX):
        raise ValueError('Unexpected download URL')
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    return urllib.request.urlopen(request, timeout=TIMEOUT, context=_context())


def download(url, destination):
    with _open(url) as response, open(destination, 'wb') as out:
        while True:
            chunk = response.read(1 << 16)
            if not chunk:
                break
            out.write(chunk)


def fetch_text(url):
    with _open(url) as response:
        return response.read(4096).decode('ascii', 'replace')


def verify_sha256(path, expected_text):
    match = re.match(r'\s*([0-9a-fA-F]{64})', expected_text)
    if not match:
        raise ValueError('Malformed checksum file')
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    if digest.hexdigest() != match.group(1).lower():
        raise ValueError('Checksum mismatch: the download is corrupted')


class UpdateState:
    """What the UI shows: nothing found / update available / applying / failed."""

    def __init__(self):
        self.lock = threading.Lock()
        self.available = None
        self.busy = False
        self.failed = False

    def snapshot(self):
        with self.lock:
            return self.available, self.busy, self.failed

    def set_available(self, release):
        with self.lock:
            self.available = release

    def begin(self):
        with self.lock:
            if self.busy or self.available is None:
                return None
            self.busy, self.failed = True, False
            return self.available

    def finish(self, ok):
        with self.lock:
            self.busy = False
            self.failed = not ok
