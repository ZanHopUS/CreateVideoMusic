"""Real render cancellation, child exit, clean retry and immutable-snapshot probe."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import queue
import subprocess
import threading
import time

import av
import numpy as np
import psutil

ROOT = Path(__file__).resolve().parents[3]


def run_job(folder, edit_working, supervise=True):
    events, identities = [], {}
    cancel_at = terminal_at = None
    observed_edit = False
    forced_cleanup = False
    with (folder / 'stderr.log').open('w', encoding='utf-8') as stderr:
        process = subprocess.Popen(['node', str(ROOT / 'poc/render/fidelity/job-worker.mjs'), str(folder)],
            cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, text=True, encoding='utf-8')
        messages = queue.Queue()
        def read():
            for line in process.stdout:
                try: messages.put((time.monotonic(), json.loads(line)))
                except ValueError:
                    with (folder / 'non-json-stdout.log').open('a', encoding='utf-8') as log: log.write(line)
        reader = threading.Thread(target=read, daemon=True)
        reader.start()
        started = time.monotonic()
        while process.poll() is None or reader.is_alive() or not messages.empty():
            if time.monotonic() - started >= 180:
                for member in reversed(psutil.Process(process.pid).children(recursive=True)):
                    try: member.kill()
                    except psutil.NoSuchProcess: pass
                process.kill(); process.wait(timeout=10)
                raise TimeoutError('Job test exceeded timebox; owned child tree terminated')
            try:
                members = [psutil.Process(process.pid), *psutil.Process(process.pid).children(recursive=True)]
                for member in members: identities[member.pid] = member.create_time()
            except psutil.NoSuchProcess: pass
            if supervise and cancel_at and not forced_cleanup and time.monotonic() - cancel_at >= 2 and any(e['state'] == 'cancelled' for e in events) and process.poll() is None:
                # Only this worker's recorded PID/create-time identities may be killed.
                for pid, created in reversed(list(identities.items())):
                    try:
                        member = psutil.Process(pid)
                        if abs(member.create_time() - created) < .001: member.kill()
                    except psutil.NoSuchProcess: pass
                forced_cleanup = True
            try: received_at, event = messages.get(timeout=.05)
            except queue.Empty: continue
            events.append(event)
            if event['state'] == 'rendering' and event.get('renderedFrames', 0) >= 30:
                if edit_working and not observed_edit:
                    working = json.loads((folder / 'working.json').read_text(encoding='utf-8'))
                    for item in working['items']:
                        if item['type'] == 'caption': item['text'] = 'ĐÃ CHỈNH KHI RENDER'
                    (folder / 'working.json').write_text(json.dumps(working, ensure_ascii=False, indent=2), encoding='utf-8')
                    observed_edit = True
                elif not edit_working and cancel_at is None:
                    cancel_at = time.monotonic()
                    process.stdin.write('{"type":"cancel"}\n'); process.stdin.flush()
            if event['state'] in ('cancelled', 'completed', 'failed'): terminal_at = received_at
        code = process.wait(timeout=10)
    cleanup_began = cancel_at or terminal_at
    live = []
    while cleanup_began is not None:
        live = []
        for pid, created in identities.items():
            try:
                p = psutil.Process(pid)
                if abs(p.create_time() - created) < .001 and p.is_running() and p.status() != psutil.STATUS_ZOMBIE: live.append(pid)
            except psutil.NoSuchProcess: pass
        if not live or time.monotonic() - cleanup_began > 10: break
        time.sleep(.05)
    return {'exit_code': code, 'events': events, 'cancel_to_terminal_s': terminal_at - cancel_at if cancel_at and terminal_at else None,
            'cleanup_elapsed_s': time.monotonic() - cleanup_began if cleanup_began else None,
            'tracked_pids': len(identities), 'remaining_pids': live, 'working_edited_during_render': observed_edit,
            'supervisor_forced_cleanup': forced_cleanup}


def png(path):
    with av.open(str(path)) as c: return next(c.decode(video=0)).to_ndarray(format='rgb24')


def psnr(a, b):
    mse = float(np.mean((a.astype(np.float32) - b.astype(np.float32)) ** 2))
    return 100 if mse == 0 else float(10 * np.log10(255**2 / mse))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', default='run-01')
    parser.add_argument('--fidelity-run-id', default='full-02')
    parser.add_argument('--api-only', action='store_true')
    args = parser.parse_args()
    assert all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.run_id)
    folder = ROOT / '.poc/evidence/poc-04/lifecycle' / args.run_id
    folder.mkdir(parents=True, exist_ok=False)
    assert all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.fidelity_run_id)
    project = json.loads((ROOT / '.poc/evidence/poc-03/fidelity' / args.fidelity_run_id / 'TPL03/snapshot.json').read_text(encoding='utf-8'))
    for name in ['cancel', 'retry']:
        sub = folder / name; sub.mkdir()
        current = copy.deepcopy(project)
        if name == 'cancel': current['durationInFrames'] = 2700
        text = json.dumps(current, ensure_ascii=False, indent=2)
        (sub / 'snapshot.json').write_text(text, encoding='utf-8')
        (sub / 'working.json').write_text(text, encoding='utf-8')
    cancelled = run_job(folder / 'cancel', False, not args.api_only)
    (folder / 'cancel-result.json').write_text(json.dumps(cancelled, indent=2), encoding='utf-8')
    assert (cancelled['exit_code'] == 0 or cancelled['supervisor_forced_cleanup']) and cancelled['events'][-1]['state'] == 'cancelled', cancelled
    assert cancelled['cancel_to_terminal_s'] <= 5 and cancelled['cleanup_elapsed_s'] <= 10 and not cancelled['remaining_pids']
    assert not (folder / 'cancel/final.mp4').exists()
    print('Real render cancelled; child process exit verified', flush=True)
    snapshot_hash = hashlib.sha256((folder / 'retry/snapshot.json').read_bytes()).hexdigest()
    retried = run_job(folder / 'retry', True)
    (folder / 'retry-result.json').write_text(json.dumps(retried, indent=2), encoding='utf-8')
    assert retried['exit_code'] == 0 and retried['events'][-1]['state'] == 'completed' and not retried['remaining_pids'], retried
    assert retried['working_edited_during_render']
    assert hashlib.sha256((folder / 'retry/snapshot.json').read_bytes()).hexdigest() == snapshot_hash
    assert hashlib.sha256((folder / 'retry/working.json').read_bytes()).hexdigest() != snapshot_hash
    events = [e for e in retried['events'] if e['progress'] is not None]
    assert all(a['progress'] <= b['progress'] for a, b in zip(events, events[1:]))
    assert all(e['progress'] < 100 and not e['finalExists'] for e in events[:-1])
    assert events[-1]['progress'] == 100 and events[-1]['finalExists']
    subprocess.run(['node', str(ROOT / 'poc/render/fidelity/references.mjs'), str(folder / 'retry')], cwd=ROOT, check=True)
    with av.open(str(folder / 'retry/final.mp4')) as c:
        frames = list(c.decode(video=0))
        assert len(frames) == 360
        actual = frames[150].to_ndarray(format='rgb24')
    same = psnr(actual, png(folder / 'retry/reference-original.png'))
    edited = psnr(actual, png(folder / 'retry/reference-edited.png'))
    checks = {'cancel_under_5s': cancelled['cancel_to_terminal_s'] <= 5,
              'children_exit_under_10s': not cancelled['remaining_pids'] and cancelled['cleanup_elapsed_s'] <= 10,
              'cancelled_output_not_published': not (folder / 'cancel/final.mp4').exists(),
              'retry_completed': True, 'immutable_snapshot': same >= 30 and same > edited + 3,
              'progress_published_last': True}
    result = {'checks': checks, 'all_passed': all(checks.values()), 'cancel': cancelled,
              'retry': retried, 'snapshot_original_psnr': same, 'snapshot_edited_psnr': edited,
              'scope': 'harness render-phase cancellation only; application/finalize cancel and crash recovery untested'}
    (folder / 'validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'checks': checks, 'cancel_s': cancelled['cancel_to_terminal_s'], 'cleanup_s': cancelled['cleanup_elapsed_s'],
                      'original_psnr': same, 'edited_psnr': edited}))
    assert result['all_passed']


if __name__ == '__main__': main()
