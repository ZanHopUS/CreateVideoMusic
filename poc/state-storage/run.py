"""Real disposable storage experiments: crash workers, round trips and corruption."""
import argparse
import copy
import ctypes
import errno
import json
import os
from pathlib import Path
import shutil
import sqlite3
import statistics
import subprocess
import sys
import time
import zipfile

from gc_policy import collect, pins
from storage import (ROOT, SANDBOX, Runtime, decoded, digest, encoded, export_package, file_hash,
    inspect_package, load_manual, manual_save, owned, references, restore_package, restore_recovery,
    validate_assets)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', default='run-01')
    args = parser.parse_args()
    assert args.run_id and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.run_id)
    directory = owned(SANDBOX / args.run_id)
    assert not (directory / 'results.json').exists()
    catalog = {a['path']: a for a in decoded((directory / 'catalog.json').read_bytes())}
    fixtures = decoded((directory / 'state-fixtures.json').read_bytes())
    state = decoded((directory / 'state-results.json').read_bytes())
    assert state['allPassed']
    library = directory / 'library'
    records, timings = [], []
    def passed(id, **details):
        records.append({'id': id, 'status': 'passed', **details})
        print(json.dumps(records[-1], ensure_ascii=True), flush=True)
    def reject(id, action):
        try: action()
        except (ValueError, KeyError, zipfile.BadZipFile, FileExistsError, PermissionError) as error:
            passed(id, rejected_with=type(error).__name__, message=str(error)); return
        raise AssertionError(f'Unsafe operation accepted: {id}')
    runtime = Runtime(directory / 'runtime/runtime.sqlite'); runtime.register(catalog)
    for case in fixtures['cases']:
        validate_assets(case['initial'], catalog, library)
        json_times, db_times = [], []
        path = directory / 'manual' / f"{case['id']}.json"
        for n in range(5):
            project = case['initial'] if n % 2 == 0 else case['edited']
            began = time.perf_counter()
            manual_save(path, project, catalog, library)
            assert load_manual(path, library)['project'] == project
            json_times.append((time.perf_counter() - began) * 1000)
            began = time.perf_counter(); runtime.save(project, catalog)
            assert runtime.load(project['id']) == project
            db_times.append((time.perf_counter() - began) * 1000)
        timings.append({'case':case['id'], 'samples':5, 'json_manual_save_load_median_ms':statistics.median(json_times),
                        'sqlite_working_save_load_median_ms':statistics.median(db_times),
                        'scope':'different operations: manual JSON includes asset verification/fsync; SQLite is working-state transaction'})
    passed('json_and_sqlite_six_scenarios', cases=6, iterations_per_backend=30)
    chosen = next(c for c in fixtures['cases'] if c['id']=='TPL03-12')
    a, b = chosen['initial'], chosen['edited']

    # Restore elsewhere must contain bytes, not merely point at the managed library.
    rounds = []
    for n in range(10):
        case = fixtures['cases'][n % len(fixtures['cases'])]
        project = case['edited']
        package = directory / 'packages' / f'round-{n:02}.pocpkg'
        export_package(package, project, catalog, library)
        target = directory / 'restored' / f'Khôi phục {n:02} — thư mục khác'
        restored = restore_package(package, target)
        assert restored['project'] == project and restored['project_hash'] == digest(project)
        validate_assets(project, restored['catalog'], target)
        rounds.append({'project':project['id'], 'project_hash':digest(project), 'assets':len(restored['catalog'])})
    passed('portable_round_trips', count=10, semantic_and_asset_hashes_match=True)

    # Actual process termination at save/transaction/package boundaries.
    phases = {'db':['db_begin','db_updated','db_committed'],
              'manual':['manual_written','manual_fsynced','manual_before_publish','manual_published'],
              'package':['package_zip_open','package_asset','package_zip_closed','package_before_publish','package_published']}
    faults = []
    payload = directory / 'fault-input.json'; payload.write_bytes(encoded({'project':b,'catalog':catalog}))
    for action, points in phases.items():
        for phase in points:
            for repeat in range(2):
                folder = directory / 'faults' / f'{phase}-{repeat}'; folder.mkdir(parents=True)
                if action=='db':
                    db = Runtime(folder / 'runtime.sqlite'); db.register(catalog); db.save(a, catalog); db.close()
                elif action=='manual': manual_save(folder / 'manual.json', a, catalog, library)
                else: export_package(folder / 'old.pocpkg', a, catalog, library)
                old_hash = file_hash(folder / 'old.pocpkg') if action=='package' else None
                process = subprocess.run([sys.executable, str(ROOT/'poc/state-storage/fault_worker.py'),
                    '--folder',str(folder),'--library',str(library),'--input',str(payload),
                    '--action',action,'--crash-at',phase], capture_output=True, text=True, encoding='utf-8')
                assert process.returncode==77,(phase,process.returncode,process.stderr)
                if action=='db':
                    db = Runtime(folder / 'runtime.sqlite')
                    expected = b if phase=='db_committed' else a
                    assert db.load(a['id'])==expected
                    assert db.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'; db.close()
                elif action=='manual': assert load_manual(folder / 'manual.json', library)['project']==(b if phase=='manual_published' else a)
                else:
                    assert file_hash(folder / 'old.pocpkg')==old_hash
                    assert inspect_package(folder / 'old.pocpkg')['project']==a
                    assert (folder/'new.pocpkg').exists()==(phase=='package_published')
                    if phase=='package_published': assert inspect_package(folder/'new.pocpkg')['project']==b
                faults.append({'action':action,'phase':phase,'repeat':repeat,'process_exit':77,'old_or_new_valid':True})
    passed('process_crash_boundaries', fault_runs=len(faults), phases=12, corrupt_canonical_saves=0)

    # Pause real manual save after fsync while the working DB receives a new edit.
    folder = directory/'inflight'; folder.mkdir()
    manual_save(folder/'manual.json',a,catalog,library)
    process = subprocess.Popen([sys.executable,str(ROOT/'poc/state-storage/fault_worker.py'),
        '--folder',str(folder),'--library',str(library),'--input',str(payload),
        '--action','manual','--pause-at','manual_fsynced'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    deadline=time.monotonic()+8
    while not (folder/'paused.signal').exists():
        if process.poll() is not None: raise AssertionError(process.communicate())
        if time.monotonic()>deadline: process.kill(); process.wait(); raise TimeoutError('Save did not pause')
        time.sleep(.01)
    c=copy.deepcopy(b); c['name']='Bản C — chỉnh trong lúc đang lưu'; runtime.save(c,catalog)
    (folder/'continue.signal').write_text('continue',encoding='utf-8')
    _, error=process.communicate(timeout=15); assert process.returncode==0,error
    assert load_manual(folder/'manual.json',library)['project']==b and runtime.load(c['id'])==c
    assert digest(runtime.load(c['id']))!=load_manual(folder/'manual.json',library)['project_hash']
    passed('manual_save_inflight_edit', manual='B',working='C',dirty=True)

    # Recovery requires a selection and never replaces manual save.
    recovery=directory/'recovery/recovery.json'; manual=directory/'recovery/manual.json'
    manual_save(manual,a,catalog,library); manual_save(recovery,b,catalog,library)
    manual_hash=file_hash(manual); before=runtime.load(a['id'])
    reject('recovery_without_confirmation',lambda:restore_recovery(recovery,library,runtime))
    assert runtime.load(a['id'])==before and file_hash(manual)==manual_hash
    assert restore_recovery(recovery,library,runtime,True)==b and runtime.load(b['id'])==b
    assert file_hash(manual)==manual_hash and recovery.exists()
    passed('recovery_selected_into_working', manual_unchanged=True,recovery_retained=True)

    # Backup API, not a copy of a live WAL database.
    runtime.db.execute('PRAGMA wal_autocheckpoint=0')
    runtime.save(b,catalog); backup=directory/'runtime/closed-backup.sqlite'; runtime.backup(backup)
    runtime.save(c,catalog); copydb=Runtime(backup)
    assert copydb.load(b['id'])==b and runtime.load(c['id'])==c; copydb.close()
    passed('sqlite_backup_api_snapshot', later_working_edit_does_not_mutate_backup=True)

    # Real SQLite SQLITE_FULL in a bounded disposable DB; never fill the host disk.
    full=Runtime(directory/'disk-full/runtime.sqlite'); full.register(catalog); full.save(a,catalog)
    full.db.execute('CREATE TABLE filler(payload BLOB)')
    pages=full.db.execute('PRAGMA page_count').fetchone()[0]
    full.db.execute(f'PRAGMA max_page_count={pages+1}')
    try:
        full.db.execute('BEGIN IMMEDIATE')
        full.db.execute('UPDATE projects SET body=?,hash=? WHERE id=?',(encoded(b).decode('utf-8'),digest(b),a['id']))
        full.db.execute('INSERT INTO filler VALUES(zeroblob(1048576))')
        raise AssertionError('Expected SQLITE_FULL')
    except sqlite3.DatabaseError as error:
        assert error.sqlite_errorcode==sqlite3.SQLITE_FULL,error
        if full.db.in_transaction: full.db.execute('ROLLBACK')
    assert full.load(a['id'])==a and full.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'; full.close()
    passed('bounded_real_sqlite_full', sqlite_errorcode=sqlite3.SQLITE_FULL, old_state_preserved=True)

    # File/package ENOSPC is explicitly injected rather than exhausting a real volume.
    enospc=directory/'enospc'; enospc.mkdir(); manual_save(enospc/'manual.json',a,catalog,library)
    export_package(enospc/'old.pocpkg',a,catalog,library)
    manual_hash, package_hash=file_hash(enospc/'manual.json'),file_hash(enospc/'old.pocpkg')
    def no_space(phase):
        if phase in {'manual_fsynced','package_asset'}: raise OSError(errno.ENOSPC,'Injected disposable quota failure')
    for operation in [lambda:manual_save(enospc/'manual.json',b,catalog,library,no_space),
                      lambda:export_package(enospc/'new.pocpkg',b,catalog,library,no_space)]:
        try: operation(); raise AssertionError('Expected ENOSPC')
        except OSError as error: assert error.errno==errno.ENOSPC
    assert file_hash(enospc/'manual.json')==manual_hash and file_hash(enospc/'old.pocpkg')==package_hash and not (enospc/'new.pocpkg').exists()
    passed('injected_file_enospc', injections=2, previous_manual_and_package_preserved=True)

    # A real Windows deny-sharing handle blocks replace until closed.
    assert os.name=='nt','This PoC run targets Windows'
    locked=directory/'locked/manual.json'; manual_save(locked,a,catalog,library); old_hash=file_hash(locked)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
    kernel.CreateFileW.restype=ctypes.c_void_p
    kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=kernel.CreateFileW(str(locked),0x80000000,0,None,3,0,None)
    assert handle!=ctypes.c_void_p(-1).value,ctypes.get_last_error()
    try:
        try: manual_save(locked,b,catalog,library); raise AssertionError('Expected sharing violation')
        except PermissionError: pass
    finally: kernel.CloseHandle(handle)
    assert file_hash(locked)==old_hash
    manual_save(locked,b,catalog,library); assert load_manual(locked,library)['project']==b
    passed('real_windows_locked_file', old_save_preserved=True,retry_after_unlock=True)

    security_tests(directory,catalog,library,a,reject,passed)
    shared_and_missing(directory,catalog,library,a,b,fixtures,passed,reject)
    runtime.close()
    result={'all_passed':True,'state':state,'tests':records,'faults':faults,'round_trips':rounds,
            'timings':timings,'sqlite_version':sqlite3.sqlite_version,
            'scope':'PoC schemas/ZIP only; no production driver selection, UI acceptance, power-loss or Google Drive verification',
            'drive_tested':False,'power_loss_tested':False}
    (directory/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'all_passed':True,'checks':len(records),'crash_runs':len(faults),'round_trips':len(rounds)}),flush=True)


def security_tests(directory,catalog,library,project,reject,passed):
    folder=directory/'malformed'; folder.mkdir()
    good=folder/'good.pocpkg'; export_package(good,project,catalog,library)
    with zipfile.ZipFile(good) as source: entries={n:source.read(n) for n in source.namelist()}
    attacks=[('traversal','../escaped.txt'),('absolute','/escaped.txt'),('drive','C:/escaped.txt'),
             ('backslash','..\\escaped.txt'),('ads','assets/file:stream'),('reserved','assets/CON')]
    for id,name in attacks:
        file=folder/f'{id}.pocpkg'
        with zipfile.ZipFile(file,'w') as z:
            for n,data in entries.items(): z.writestr(n,data)
            z.writestr(name,b'generated attack')
        target=directory/'rejected-restores'/id
        reject(f'package_{id}',lambda:restore_package(file,target)); assert not target.exists()
    variants=['duplicate','case_collision','symlink','hash_mismatch','missing_asset','unsupported_version','unreferenced','bomb']
    for id in variants:
        file=folder/f'{id}.pocpkg'; changed=dict(entries)
        asset=next(n for n in changed if n.startswith('assets/'))
        if id=='hash_mismatch': changed[asset]=b'corrupted asset'
        if id=='missing_asset': del changed[asset]
        if id=='unsupported_version':
            manifest=decoded(changed['manifest.json']); manifest['format']='future-99'; changed['manifest.json']=encoded(manifest)
        with zipfile.ZipFile(file,'w') as z:
            for name,data in changed.items(): z.writestr(name,data)
            if id=='duplicate': z.writestr('project.json',entries['project.json'])
            if id=='case_collision': z.writestr('PROJECT.JSON',entries['project.json'])
            if id=='symlink':
                info=zipfile.ZipInfo('assets/'+'1'*64+'.svg'); info.create_system=3; info.external_attr=0o120777<<16
                z.writestr(info,b'../../outside')
            if id=='unreferenced': z.writestr('assets/'+'2'*64+'.svg',b'<svg/>')
            if id=='bomb': z.writestr('assets/'+'3'*64+'.svg',b'0'*(2*1024**2),compress_type=zipfile.ZIP_DEFLATED)
        target=directory/'rejected-restores'/id
        reject(f'package_{id}',lambda:restore_package(file,target)); assert not target.exists()
    (directory/'existing-restore').mkdir()
    reject('restore_existing_destination',lambda:restore_package(good,directory/'existing-restore'))
    reject('restore_outside_capability',lambda:restore_package(good,SANDBOX.parent/'outside-restored'))
    assert not (directory/'escaped.txt').exists() and not (folder/'escaped.txt').exists()
    passed('archive_no_escape_observed', malformed_cases=len(attacks)+len(variants))


def shared_and_missing(directory,catalog,library,a,b,fixtures,passed,reject):
    shared=Runtime(directory/'shared/runtime.sqlite'); shared.register(catalog)
    first=copy.deepcopy(a); first['id']='shared-a'
    second=copy.deepcopy(a); second['id']='shared-b'
    shared.save(first,catalog); shared.save(second,catalog)
    shared.db.execute('DELETE FROM projects WHERE id=?',(first['id'],))
    assert references(second).issubset(shared.pins())
    shared.db.execute('DELETE FROM projects WHERE id=?',(second['id'],))
    manual=directory/'shared/manual.json'; recovery=directory/'shared/recovery.json'
    manual_save(manual,a,catalog,library); manual_save(recovery,b,catalog,library)
    template=next(t for t in fixtures['templates'] if t['project']['id']=='TPL01-12')
    alpha=next(name for name,value in catalog.items() if value['originalName']=='alpha.png')
    assert pins(shared,library,manual=[manual])==references(a)
    assert pins(shared,library,recovery=[recovery])==references(b)
    assert pins(shared,library,templates=[template])==references(template['project'])
    protected=pins(shared,library,[manual],[recovery],[template],[alpha])
    assert set(catalog).issubset(protected)
    orphan_data=b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1"/></svg>'
    import hashlib
    sha=hashlib.sha256(orphan_data).hexdigest(); orphan=f'assets/{sha}.svg'
    owned(library/orphan).write_bytes(orphan_data)
    extended={**catalog,orphan:{'path':orphan,'sha256':sha,'bytes':len(orphan_data),'mime':'image/svg+xml'}}
    reject('gc_without_confirmation',lambda:collect(list(extended),extended,library,protected))
    assert collect(list(extended),extended,library,protected,True)==[orphan]
    for name in catalog: assert file_hash(library/name)==catalog[name]['sha256']
    passed('shared_template_recovery_job_pins', shared_asset_not_deleted=True, only_confirmed_unreferenced_orphan_removed=True)
    shared.close()
    isolated=directory/'missing-library'; isolated.mkdir()
    for name in references(a):
        target=owned(isolated/name); target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(library/name,target)
    name=next(iter(references(a))); target=owned(isolated/name); target.unlink()
    reject('missing_media_detected',lambda:validate_assets(a,catalog,isolated))
    target.write_bytes(b'wrong relink bytes')
    reject('relink_wrong_checksum',lambda:validate_assets(a,catalog,isolated))
    shutil.copy2(library/name,target); validate_assets(a,catalog,isolated)
    passed('relink_validated_by_hash', original_library_unchanged=True)


if __name__=='__main__':
    try: main()
    except BaseException as error:
        # The traceback remains the primary failure evidence; do not mark partial work passed.
        print(json.dumps({'all_passed':False,'error':type(error).__name__,'message':str(error)}),flush=True)
        raise
