"""Full decode and AV/tail-signal checks for one generated 300s render."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import wave

import av
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RATE = 48000
WINDOWS = [(0, .02), (150, 150.02), (295, 295.02), (299.95, 300)]


def audio_measurements(path):
    windows = [np.zeros(round((end - start) * RATE), dtype=np.float32) for start, end in WINDOWS]
    filled = [np.zeros(len(window), dtype=bool) for window in windows]
    events, frames, maximum_end = [], 0, 0
    with av.open(str(path)) as container:
        stream = container.streams.audio[0]
        assert stream.codec_context.sample_rate == RATE
        for frame in container.decode(audio=0):
            assert frame.format.name == 'fltp', frame.format.name
            frames += 1
            values = frame.to_ndarray().mean(axis=0)
            first = round(float(frame.pts * frame.time_base) * RATE)
            maximum_end = max(maximum_end, (first + len(values)) / RATE)
            hits = np.flatnonzero(np.abs(values) > .01)
            if hits.size:
                at = (first + int(hits[0])) / RATE
                if not events or at - events[-1] > 1:
                    events.append(at)
            for index, (start, end) in enumerate(WINDOWS):
                lower, upper = max(first, round(start * RATE)), min(first + len(values), round(end * RATE))
                if lower < upper:
                    out_start = lower - round(start * RATE)
                    windows[index][out_start:out_start + upper - lower] = values[lower - first:upper - first]
                    filled[index][out_start:out_start + upper - lower] = True
    assert all(np.all(mask) for mask in filled), 'Missing decoded audio window samples'
    return {'decoded_audio_frames': frames, 'decoded_audio_end_s': maximum_end,
            'events_s': events}, windows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--template', choices=['TPL01', 'TPL02', 'TPL03'], default='TPL03')
    parser.add_argument('--ratio', choices=['9-16', '16-9', '1-1'], default='9-16')
    parser.add_argument('--run-id', default='')
    args = parser.parse_args()
    if args.run_id and not re.fullmatch(r'[a-z0-9-]+', args.run_id): parser.error('Invalid run ID')
    suffix = f'-{args.run_id}' if args.run_id else ''
    directory = ROOT / '.poc/evidence/poc-04' / f'{args.template.lower()}-{args.ratio}-300s-1080p60{suffix}'
    config = json.loads((directory / 'run-config.json').read_text(encoding='utf-8'))
    settings = config['settings']
    verified_sources = {}
    for entry in config['inventory']:
        current = ROOT / entry['path']
        snapshot = directory / 'source-snapshot' / entry['path']
        selected = current if current.is_file() and hashlib.sha256(current.read_bytes()).hexdigest() == entry['sha256'] else snapshot
        assert hashlib.sha256(selected.read_bytes()).hexdigest() == entry['sha256'], entry['path']
        verified_sources[entry['path']] = 'current' if selected == current else 'snapshot'
    assert settings.get('template', 'TPL03') == args.template
    result = {'settings': settings, 'flashes_s': [], 'timestamp_errors': 0, 'decoded_frames': 0}
    with av.open(str(directory / 'bounded.mp4')) as container:
        video, audio = container.streams.video[0], container.streams.audio[0]
        assert (video.width, video.height) == (settings['width'], settings['height'])
        assert float(video.average_rate) == 60 and video.codec_context.name == 'h264'
        assert audio.codec_context.name == 'aac'
        result['duration_s'] = {'video': float(video.duration * video.time_base),
                                'audio': float(audio.duration * audio.time_base),
                                'container': container.duration / av.time_base}
        for frame in container.decode(video=0):
            time = float(frame.pts * frame.time_base)
            if abs(time - result['decoded_frames'] / 60) > .000001:
                result['timestamp_errors'] += 1
            result['decoded_frames'] += 1
            assert frame.format.name in ('yuv420p', 'yuvj420p')
            y = np.frombuffer(frame.planes[0], dtype=np.uint8).reshape(frame.height, frame.planes[0].line_size)
            u = np.frombuffer(frame.planes[1], dtype=np.uint8).reshape(frame.height // 2, frame.planes[1].line_size)
            v = np.frombuffer(frame.planes[2], dtype=np.uint8).reshape(frame.height // 2, frame.planes[2].line_size)
            if (y[5:15, frame.width - 15:frame.width - 5].min() > 230
                    and np.abs(u[3:7, frame.width // 2 - 7:frame.width // 2 - 3].astype(int) - 128).max() < 8
                    and np.abs(v[3:7, frame.width // 2 - 7:frame.width // 2 - 3].astype(int) - 128).max() < 8):
                result['flashes_s'].append(time)
    result['bounded_audio'], after = audio_measurements(directory / 'bounded.mp4')
    result['raw_audio'], before = audio_measurements(directory / 'raw.mp4')
    with wave.open(str(ROOT / '.poc/render/stress-public/control.wav')) as source:
        reference = []
        for start, end in WINDOWS:
            source.setpos(round(start * RATE))
            reference.append(np.frombuffer(source.readframes(round((end - start) * RATE)), dtype='<i2').astype(float) / 32768)
    result['audio_windows'] = [{'start_s': bounds[0], 'end_s': bounds[1],
        'raw_final_correlation': float(np.corrcoef(raw, final)[0, 1]),
        'reference_final_correlation': float(np.corrcoef(ref, final)[0, 1]),
        'final_rms': float(np.sqrt(np.mean(final ** 2))),
        'rms_ratio_final_raw': float(np.sqrt(np.mean(final ** 2) / np.mean(raw ** 2)))}
        for bounds, raw, final, ref in zip(WINDOWS, before, after, reference)]
    expected = list(range(0, 300, 5))
    events = result['bounded_audio']['events_s']
    result['checks'] = {
        'frame_count': result['decoded_frames'] == 18000,
        'cfr_timestamps': result['timestamp_errors'] == 0,
        'duration': all(abs(value - 300) <= 1 / 60 for value in result['duration_s'].values()),
        'flash_count': len(result['flashes_s']) == 60,
        'audio_events_count': len(events) == 61,
        'flash_times': len(result['flashes_s']) == 60 and all(abs(a - b) <= .1 for a, b in zip(result['flashes_s'], expected)),
        'audio_times': len(events) == 61 and all(abs(a - b) <= .1 for a, b in zip(events, [*expected, 299.9])),
        'audio_windows': all(w['raw_final_correlation'] >= .98 and w['reference_final_correlation'] >= .98
                             and .9 <= w['rms_ratio_final_raw'] <= 1.1 for w in result['audio_windows']),
        'tail_signal_present': result['audio_windows'][-1]['final_rms'] > .005,
    }
    if len(events) == 61 and len(result['flashes_s']) == 60:
        result['max_av_delta_ms'] = max(abs(a - b) * 1000 for a, b in zip(events[:60], result['flashes_s']))
    result['all_passed'] = all(result['checks'].values())
    result['validator_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['source_inventory_verified'] = True
    result['source_inventory_origin'] = verified_sources
    result['output_hashes'] = {}
    for name in ['raw', 'bounded']:
        digest = hashlib.sha256()
        with (directory / f'{name}.mp4').open('rb') as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(chunk)
        result['output_hashes'][name] = digest.hexdigest()
    result['interactive_preview_tested'] = False
    result['perceptual_audio_quality_accepted'] = False
    (directory / 'validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    if not result['all_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
