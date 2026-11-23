"""Experimental SQLite runtime + independent manual/recovery + portable ZIP policy."""
import hashlib
import json
import math
import ntpath
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import stat
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SANDBOX = (ROOT / '.poc/state-storage').resolve()
FORMAT = 'poc-portable-1'
MAX_ENTRY = 16 * 1024**2
MAX_TOTAL = 64 * 1024**2


def owned(path):
    path = Path(path).resolve()
    if not path.is_relative_to(SANDBOX): raise ValueError('Outside disposable PoC root')
    return path


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def decoded(data):
    return json.loads(data, parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Non-finite JSON')))


def digest(value): return hashlib.sha256(encoded(value)).hexdigest()


def file_hash(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''): result.update(block)
    return result.hexdigest()


def asset_path(value):
    if not isinstance(value, str) or not re.fullmatch(r'assets/[0-9a-f]{64}\.(mp4|wav|png|svg)', value):
        raise ValueError('Asset path must be managed, relative and content-addressed')
    return value


def validate_project(project, catalog):
    keys = {'schemaVersion', 'id', 'name', 'template', 'width', 'height', 'fps', 'durationInFrames',
            'items', 'markerFrames', 'uiState', 'originTemplateId'}
    if not isinstance(project, dict) or set(project) - keys or project.get('schemaVersion') != 'poc-fidelity-1': raise ValueError('Unsupported project schema')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', project['id']): raise ValueError('Invalid ID')
    fps, duration = project['fps'], project['durationInFrames']
    if not isinstance(fps, int) or fps <= 0 or not isinstance(duration, int) or not 0 < duration / fps <= 300: raise ValueError('Invalid duration')
    allowed = {'id', 'type', 'asset', 'start', 'duration', 'sourceStart', 'speed', 'z', 'box', 'text', 'seekNudgeFrames'}
    ids = set()
    for item in project['items']:
        if set(item) - allowed or item['id'] in ids: raise ValueError('Unknown field or duplicate ID')
        ids.add(item['id'])
        for key in ['start', 'duration', 'sourceStart', 'speed', 'z', 'seekNudgeFrames']:
            if key in item and (not isinstance(item[key], (int, float)) or not math.isfinite(item[key])): raise ValueError('Non-finite item')
        if item['start'] < 0 or item['duration'] <= 0 or item['start'] + item['duration'] > duration or item.get('speed', 1) <= 0: raise ValueError('Invalid range')
        if item['type'] not in {'image', 'video', 'audio', 'lyrics', 'caption'}: raise ValueError('Unknown item type')
        if item['type'] in {'image', 'video', 'audio'}:
            path = asset_path(item['asset'])
            if path not in catalog: raise ValueError('Missing asset reference')
            prefix = {'image':'image/', 'video':'video/', 'audio':'audio/'}[item['type']]
            if not catalog[path]['mime'].startswith(prefix): raise ValueError('Asset kind/MIME mismatch')
            if item.get('sourceStart', 0) < 0: raise ValueError('Negative source offset')
            if 'duration_s' in catalog[path] and item['type'] != 'image':
                end = (item.get('sourceStart', 0) + item['duration'] * item.get('speed', 1)) / fps
                if end > catalog[path]['duration_s'] + 1/fps: raise ValueError('Source window outside media')
    if any(id not in ids for id in project.get('uiState', {}).get('selectedIds', [])): raise ValueError('Dangling selected item')
    encoded(project)
    return project


def references(project): return {i['asset'] for i in project['items'] if 'asset' in i}


def validate_assets(project, catalog, library):
    validate_project(project, catalog)
    library = owned(library)
    for name in references(project):
        file = owned(library / asset_path(name))
        if not file.is_relative_to(library) or file.is_symlink() or not file.is_file(): raise ValueError('Missing or escaping asset')
        entry = catalog[name]
        if file.stat().st_size != entry['bytes'] or file_hash(file) != entry['sha256']: raise ValueError('Asset checksum mismatch')


class Runtime:
    def __init__(self, path):
        self.path = owned(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=.1, isolation_level=None)
        version = self.db.execute('PRAGMA user_version').fetchone()[0]
        if version not in (0, 1): self.db.close(); raise ValueError('Unsupported runtime version')
        self.db.execute('PRAGMA foreign_keys=ON'); self.db.execute('PRAGMA journal_mode=WAL'); self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''CREATE TABLE IF NOT EXISTS assets(path TEXT PRIMARY KEY, body TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, revision INTEGER NOT NULL, body TEXT NOT NULL, hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS refs(project_id TEXT REFERENCES projects(id) ON DELETE CASCADE, asset_path TEXT REFERENCES assets(path), PRIMARY KEY(project_id,asset_path));
PRAGMA user_version=1;''')
    def register(self, catalog):
        for key, value in catalog.items(): self.db.execute('INSERT OR IGNORE INTO assets VALUES (?,?)', (key, encoded(value).decode('utf-8')))
    def save(self, project, catalog, hook=lambda phase: None):
        validate_project(project, catalog)
        try:
            self.db.execute('BEGIN IMMEDIATE'); hook('db_begin')
            self.db.execute('INSERT INTO projects VALUES (?,1,?,?) ON CONFLICT(id) DO UPDATE SET revision=revision+1,body=excluded.body,hash=excluded.hash',
                (project['id'], encoded(project).decode('utf-8'), digest(project)))
            self.db.execute('DELETE FROM refs WHERE project_id=?', (project['id'],))
            self.db.executemany('INSERT INTO refs VALUES (?,?)', [(project['id'], a) for a in references(project)])
            hook('db_updated'); self.db.execute('COMMIT'); hook('db_committed')
        except BaseException:
            if self.db.in_transaction: self.db.execute('ROLLBACK')
            raise
    def load(self, id):
        row = self.db.execute('SELECT body,hash FROM projects WHERE id=?', (id,)).fetchone()
        if row is None: raise KeyError(id)
        value = decoded(row[0])
        if digest(value) != row[1]: raise ValueError('Runtime snapshot hash mismatch')
        return value
    def pins(self): return {r[0] for r in self.db.execute('SELECT DISTINCT asset_path FROM refs')}
    def backup(self, target):
        target = owned(target)
        if target.exists(): raise FileExistsError(target)
        destination = sqlite3.connect(target)
        try: self.db.backup(destination); assert destination.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        finally: destination.close()
    def close(self): self.db.close()


def manual_save(path, project, catalog, library, hook=lambda phase: None):
    path = owned(path); path.parent.mkdir(parents=True, exist_ok=True)
    validate_assets(project, catalog, library)
    subset = {a: catalog[a] for a in sorted(references(project))}
    envelope = {'format': 'poc-manual-1', 'project': project, 'project_hash': digest(project), 'assets': subset}
    staging = owned(path.with_name(path.name + '.stage-' + uuid.uuid4().hex))
    with staging.open('xb') as output:
        output.write(encoded(envelope)); output.flush(); hook('manual_written')
        os.fsync(output.fileno()); hook('manual_fsynced')
    load_manual(staging, library)
    hook('manual_before_publish'); os.replace(staging, path); hook('manual_published')
    return envelope


def load_manual(path, library):
    data = decoded(owned(path).read_bytes())
    if data.get('format') != 'poc-manual-1' or digest(data['project']) != data['project_hash']: raise ValueError('Invalid manual snapshot')
    validate_assets(data['project'], data['assets'], library)
    return data


def restore_recovery(path, library, runtime, confirmed=False):
    candidate = load_manual(path, library)
    if not confirmed: raise PermissionError('Recovery restore requires explicit selection')
    runtime.register(candidate['assets']); runtime.save(candidate['project'], candidate['assets'])
    return candidate['project']


def export_package(target, project, catalog, library, hook=lambda phase: None):
    target = owned(target); target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists(): raise FileExistsError(target)
    validate_assets(project, catalog, library)
    entries = [catalog[a] for a in sorted(references(project))]
    body = encoded(project)
    manifest = {'format': FORMAT, 'project_sha256': hashlib.sha256(body).hexdigest(), 'assets': entries}
    staging = owned(target.with_name(target.name + '.stage-' + uuid.uuid4().hex))
    with staging.open('xb') as raw:
        with zipfile.ZipFile(raw, 'w', compression=zipfile.ZIP_STORED) as archive:
            archive.writestr('manifest.json', encoded(manifest)); hook('package_zip_open')
            archive.writestr('project.json', body)
            for entry in entries:
                archive.write(owned(Path(library) / entry['path']), entry['path']); hook('package_asset')
        hook('package_zip_closed'); raw.flush(); os.fsync(raw.fileno())
    inspect_package(staging)
    hook('package_before_publish'); os.replace(staging, target); hook('package_published')
    return target


def safe_member(name):
    if not name or '\\' in name or ':' in name or '\0' in name or ntpath.splitdrive(name)[0] or name.startswith('/'):
        raise ValueError('Unsafe archive path')
    parts = PurePosixPath(name).parts
    if any(p in ('.', '..') or p.endswith(('.', ' ')) or p.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]} for p in parts):
        raise ValueError('Unsafe Windows archive path')
    if name not in {'manifest.json', 'project.json'}: asset_path(name)


def inspect_package(path):
    with zipfile.ZipFile(owned(path)) as archive:
        infos = archive.infolist()
        if len(infos) > 64 or sum(i.file_size for i in infos) > MAX_TOTAL: raise ValueError('PoC archive budget exceeded')
        seen = set()
        for info in infos:
            safe_member(info.filename)
            if info.filename.casefold() in seen: raise ValueError('Duplicate/case-colliding member')
            seen.add(info.filename.casefold())
            if info.file_size > MAX_ENTRY or info.file_size / max(1, info.compress_size) > 200: raise ValueError('PoC decompression budget exceeded')
            if stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG): raise ValueError('Archive links/directories are not accepted')
        if not {'manifest.json','project.json'}.issubset(seen): raise ValueError('Missing manifest/project')
        if archive.getinfo('manifest.json').file_size > 1024**2: raise ValueError('Manifest too large')
        manifest, body = decoded(archive.read('manifest.json')), archive.read('project.json')
        if manifest.get('format') != FORMAT or hashlib.sha256(body).hexdigest() != manifest.get('project_sha256'): raise ValueError('Invalid manifest/project hash')
        catalog = {}
        for entry in manifest['assets']:
            name = asset_path(entry['path'])
            if name in catalog or entry['sha256'] not in name: raise ValueError('Duplicate asset or hash/path mismatch')
            data = archive.read(name)
            if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']: raise ValueError('Asset integrity failure')
            catalog[name] = entry
        project = decoded(body); validate_project(project, catalog)
        if set(catalog) != references(project) or {i.filename for i in infos} != {'manifest.json','project.json',*catalog}: raise ValueError('Unreferenced or missing members')
        return {'project': project, 'catalog': catalog, 'project_hash': digest(project)}


def restore_package(package, target):
    target = owned(target)
    if target.exists(): raise FileExistsError('Restore never overwrites an existing destination')
    verified = inspect_package(package)
    staging = owned(target.with_name(target.name + '.restore-' + uuid.uuid4().hex))
    staging.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(owned(package)) as archive:
        for name in verified['catalog']:
            file = owned(staging / asset_path(name))
            if not file.is_relative_to(staging): raise ValueError('Restore escape')
            file.parent.mkdir(parents=True, exist_ok=True); file.write_bytes(archive.read(name))
    (staging / 'project.json').write_bytes(encoded(verified['project']))
    validate_assets(verified['project'], verified['catalog'], staging)
    # Both resolved endpoints are inside the disposable root before moving a tree.
    owned(staging); owned(target); os.rename(staging, target)
    return verified
