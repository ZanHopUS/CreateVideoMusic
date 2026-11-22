"""Independent snapshot/time oracle and pixel comparisons for the actual Player."""
import argparse
import hashlib
import json
from pathlib import Path

import av
import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def image(path):
    with av.open(str(path)) as container:
        return next(container.decode(video=0)).to_ndarray(format='rgb24')


def score(a, b):
    assert a.shape == b.shape, (a.shape, b.shape)
    delta = a.astype(np.float32) - b.astype(np.float32)
    mse = float(np.mean(delta ** 2))
    return {'psnr_db': 100 if mse == 0 else float(10 * np.log10(255 ** 2 / mse)),
            'mean_absolute_error': float(np.abs(delta).mean())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--output-name', default='validation.json')
    args = parser.parse_args()
    assert all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.run_id)
    assert args.output_name.endswith('.json') and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789-.' for c in args.output_name)
    directory = ROOT / '.poc/evidence/poc-03/fidelity' / args.run_id
    config = json.loads((directory / 'config.json').read_text(encoding='utf-8'))
    results = json.loads((directory / 'results.json').read_text(encoding='utf-8'))
    rows = []
    for case in results['cases']:
        project = next(p for p in config['projects'] if p['id'] == case['projectId'])
        assert len(project['items']) == 12
        folder = directory / project['id']
        row = {'project': project['id'], 'comparisons': [], 'audio_events_s': [], 'flash_times_s': []}
        decoded = {}
        if not config['quick']:
            wanted = {p['frame'] for p in case['probes']}
            with av.open(str(folder / 'export.mp4')) as container:
                row['video_duration_s'] = float(container.streams.video[0].duration * container.streams.video[0].time_base)
                row['container_duration_s'] = container.duration / av.time_base
                count, errors = 0, 0
                for frame in container.decode(video=0):
                    if abs(float(frame.pts * frame.time_base) - count / 30) > .000001: errors += 1
                    assert frame.format.name in ('yuv420p', 'yuvj420p')
                    planes = [np.frombuffer(p, dtype=np.uint8).reshape(p.height, p.line_size) for p in frame.planes]
                    if (planes[0][5:15, frame.width-15:frame.width-5].min() > 230
                        and all(np.abs(p[3:7, frame.width//2-7:frame.width//2-3].astype(int)-128).max() < 8 for p in planes[1:])):
                        row['flash_times_s'].append(float(frame.pts * frame.time_base))
                    if count in wanted: decoded[count] = frame.to_ndarray(format='rgb24')
                    count += 1
                row['decoded_frames'], row['timestamp_errors'] = count, errors
            with av.open(str(folder / 'export.mp4')) as container:
                for frame in container.decode(audio=0):
                    values = np.max(np.abs(frame.to_ndarray()), axis=0)
                    hits = np.flatnonzero(values > .01)
                    if hits.size:
                        at = float(frame.pts * frame.time_base) + int(hits[0]) / frame.sample_rate
                        if not row['audio_events_s'] or at - row['audio_events_s'][-1] > 1: row['audio_events_s'].append(at)
            music = next(i for i in project['items'] if i['type'] == 'audio')
            expected = [(pulse - music['sourceStart'] / 30) / music['speed'] + music['start'] / 30 for pulse in [0, 5, 10]]
            expected = [at for at in expected if 0 <= at < 12]
            row['audio_expected_s'] = expected
            row['audio_timing_pass'] = len(expected) == len(row['audio_events_s']) and all(abs(a-b) <= .1 for a, b in zip(expected, row['audio_events_s']))
            flashes = [f/30 for f in project['markerFrames']]
            row['flash_timing_pass'] = len(flashes) == len(row['flash_times_s']) and all(abs(a-b) < .000001 for a, b in zip(flashes, row['flash_times_s']))
            row['av_marker_pass'] = len(row['flash_times_s']) == len(row['audio_events_s']) and all(abs(a-b) <= .1 for a,b in zip(row['flash_times_s'],row['audio_events_s']))
            row['max_av_delta_ms'] = max((abs(a-b)*1000 for a,b in zip(row['flash_times_s'],row['audio_events_s'])),default=None)
        for probe in case['probes']:
            frame = probe['frame']
            active = [i for i in project['items'] if i['start'] <= frame < i['start'] + i['duration']]
            ids = sorted(i['id'] for i in active)
            png_score = score(image(folder / f'player-{frame}.png'), image(folder / f'render-{frame}.png'))
            timing = []
            for item in active:
                if item['type'] != 'video': continue
                expected = item['sourceStart'] / 30 + (frame - item['start']) / 30 * item['speed']
                actual = next((v['time'] for v in probe['videos'] if v['src'].split('#')[0] == item['asset']), None)
                timing.append({'asset': item['asset'], 'expected_s': expected, 'actual_s': actual,
                               'pass': actual is not None and abs(actual - expected) <= .1})
            comparison = {'frame': frame, 'active_items_pass': ids == probe['activeIds'],
                'png': png_score, 'source_times': timing,
                'png_pass': png_score['psnr_db'] >= 30,
                'source_time_pass': all(t['pass'] for t in timing)}
            if frame in decoded:
                comparison['mp4'] = score(image(folder / f'player-{frame}.png'), decoded.pop(frame))
                comparison['mp4_pass'] = comparison['mp4']['psnr_db'] >= 30
            row['comparisons'].append(comparison)
        row['all_frame_checks_pass'] = all(c['active_items_pass'] and c['png_pass'] and c['source_time_pass'] and c.get('mp4_pass', True) for c in row['comparisons'])
        if case.get('seekSamples'):
            samples = [s['elapsedMs'] for s in case['seekSamples']]
            row['seek_samples'] = len(samples)
            row['seek_p95_ms'] = float(np.percentile(samples, 95))
        rows.append(row)
    final = {'quick': config['quick'], 'cases': rows,
        'all_frame_checks_pass': all(r['all_frame_checks_pass'] for r in rows),
        'all_export_audio_pass': None if config['quick'] else all(r['audio_timing_pass'] for r in rows),
        'all_av_markers_pass': None if config['quick'] else all(r['flash_timing_pass'] and r['av_marker_pass'] for r in rows),
        'all_export_structure_pass': None if config['quick'] else all(r['decoded_frames'] == 360 and r['timestamp_errors'] == 0
            and abs(r['container_duration_s'] - 12) <= 1/30 for r in rows)}
    if results.get('simplePlayerPlayback'):
        final['simplePlayerPlayback'] = results['simplePlayerPlayback']
        final['simplePlayerPlayback']['event_fps'] = results['simplePlayerPlayback']['frameEvents'] / (results['simplePlayerPlayback']['elapsedMs'] / 1000)
    final['validator_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (directory / args.output_name).write_text(json.dumps(final, indent=2), encoding='utf-8')
    (directory / args.output_name).with_suffix('.validator.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k: final[k] for k in final if k != 'cases'}))
    for row in rows:
        print(json.dumps({'project': row['project'], 'checks_pass': row['all_frame_checks_pass'],
            'min_png_psnr': min(c['png']['psnr_db'] for c in row['comparisons']), 'audio_events_s': row['audio_events_s'],
            'failing_frames': [c for c in row['comparisons'] if not (c['png_pass'] and c['source_time_pass'] and c['active_items_pass'] and c.get('mp4_pass', True))]}))
    if any(final[k] is False for k in ['all_frame_checks_pass', 'all_export_audio_pass', 'all_export_structure_pass', 'all_av_markers_pass']): raise SystemExit(1)


if __name__ == '__main__': main()
