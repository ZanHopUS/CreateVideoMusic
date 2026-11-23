"""Exercise real Windows directory junctions using only generated disposable files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from gc_policy import collect
from storage import (ROOT, SANDBOX, Runtime, decoded, export_package, file_hash,
                     manual_save, owned, restore_package, validate_assets)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', default='junction-01')
    args = parser.parse_args()
    if not args.run_id or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.run_id):
        parser.error('Invalid run ID')
    if os.name != 'nt': parser.error('Real Windows junction test requires Windows')
    directory = owned(SANDBOX / args.run_id)
    # Separate canary deliberately sits outside storage SANDBOX, inside workspace .poc.
    canary_root = (ROOT / '.poc/path-canaries').resolve()
    assert canary_root.is_relative_to((ROOT / '.poc').resolve())
    canary = (canary_root / args.run_id).resolve()
    assert canary.is_relative_to(canary_root) and not canary.is_relative_to(SANDBOX)
    if directory.exists() or canary.exists(): raise FileExistsError('Use a fresh run ID')
    directory.mkdir(parents=True); canary.mkdir(parents=True)
    origin = owned(SANDBOX / 'run-01')
    catalog = {a['path']: a for a in decoded((origin/'catalog.json').read_bytes())}
    project = next(c['edited'] for c in decoded((origin/'state-fixtures.json').read_bytes())['cases']
                   if c['id'] == 'TPL03-12')
    (canary/'assets').mkdir()
    for name in catalog: shutil.copy2(origin/'library'/name, canary/name)
    (canary/'sentinel.txt').write_text('generated escape canary; must remain unchanged', encoding='utf-8')

    def inventory(folder):
        return {p.relative_to(folder).as_posix(): file_hash(p) for p in folder.rglob('*') if p.is_file()}

    before = inventory(canary)
    junctions, checks = [], []

    def junction(link, target):
        # Verify intended lexical parent and resolved destination before creating alias.
        assert link.parent.resolve().is_relative_to(directory)
        assert target.resolve().is_relative_to((ROOT/'.poc').resolve())
        result = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(link), str(target)],
                                capture_output=True, text=True, timeout=15)
        if result.returncode: raise RuntimeError(f'Junction creation failed: {result.returncode}')
        assert link.is_junction() and link.resolve() == target.resolve()
        junctions.append({'link':str(link.relative_to(ROOT)), 'target':str(target.relative_to(ROOT))})

    def blocked(name, action):
        try: action()
        except ValueError as error:
            checks.append({'id':name, 'rejected_with':type(error).__name__, 'message':str(error)})
            return
        raise AssertionError(f'Junction escape accepted: {name}')

    escape = directory/'outside'; junction(escape, canary)
    package = origin/'packages/round-00.pocpkg'
    blocked('owned_outside_root', lambda: owned(escape/'new.txt'))
    blocked('sqlite_write_outside_root', lambda: Runtime(escape/'runtime.sqlite'))
    blocked('manual_write_outside_root', lambda: manual_save(escape/'manual.json', project, catalog, origin/'library'))
    blocked('package_write_outside_root', lambda: export_package(escape/'new.pocpkg', project, catalog, origin/'library'))
    blocked('restore_outside_root', lambda: restore_package(package, escape/'restored'))

    library = directory/'library'; library.mkdir()
    junction(library/'assets', canary/'assets')
    blocked('asset_read_outside_root', lambda: validate_assets(project, catalog, library))
    blocked('export_asset_outside_root', lambda: export_package(directory/'bad.pocpkg', project, catalog, library))
    blocked('gc_outside_root', lambda: collect([next(iter(catalog))], catalog, library, set(), confirmed=True))

    # Same sandbox is insufficient: asset reads/deletes must also stay in that library.
    sibling = directory/'sibling'; (sibling/'assets').mkdir(parents=True)
    for name in catalog: shutil.copy2(origin/'library'/name, sibling/name)
    sibling_before = inventory(sibling)
    alias_library = directory/'alias-library'; alias_library.mkdir()
    junction(alias_library/'assets', sibling/'assets')
    blocked('asset_read_other_library', lambda: validate_assets(project, catalog, alias_library))
    blocked('gc_other_library', lambda: collect([next(iter(catalog))], catalog, alias_library, set(), confirmed=True))
    assert inventory(sibling) == sibling_before
    assert inventory(canary) == before, 'Canary modified or unexpected file written'
    result = {'all_passed':True, 'checks':checks, 'junctions':junctions,
              'canary_inventory_unchanged':True, 'canary_hashes':before,
              'sibling_library_unchanged':True,
              'scope':'Existing junctions only; no concurrent replacement/TOCTOU, service capability or full reparse audit'}
    (directory/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    source=Path(__file__).read_bytes()
    (directory/'check-junctions.py.snapshot').write_bytes(source)
    (directory/'source-sha256.txt').write_text(hashlib.sha256(source).hexdigest(),encoding='utf-8')
    print(json.dumps({'all_passed':True,'checks':len(checks),'real_junctions':len(junctions),
                      'canary_inventory_unchanged':True}))
    # Keep junctions/canaries as evidence; no recursive delete across junctions.


if __name__ == '__main__': main()
