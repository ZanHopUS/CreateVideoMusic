"""Verify evidence and summarize the five planned generated stress outputs."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / '.poc/evidence/poc-04'
CASES = [('TPL01', '9-16'), ('TPL02', '9-16'), ('TPL03', '9-16'), ('TPL03', '16-9'), ('TPL03', '1-1')]


def file_digest(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    batch = json.loads((EVIDENCE / 'remaining-stress-batch.json').read_text(encoding='utf-8'))
    assert batch['state'] == 'completed' and len(batch['cases']) == 4
    assert all(row['state'] == 'passed' for row in batch['cases'])
    rows = []
    for template, ratio in CASES:
        name = f'{template.lower()}-{ratio}-300s-1080p60'
        directory = EVIDENCE / name
        read = lambda filename: json.loads((directory / filename).read_text(encoding='utf-8'))
        result, validation = read('render-result.json'), read('validation.json')
        resources, validation_resources = read('resources/resources.json'), read('validation-resources/resources.json')
        assert validation['all_passed'] and all(validation['checks'].values()), name
        for record in [resources, validation_resources]:
            assert record['exit_code'] == 0 and record['abort_reason'] is None, name
        for output, expected in validation['output_hashes'].items():
            assert file_digest(directory / f'{output}.mp4') == expected, (name, output)
        inventory = read('run-config.json')['inventory']
        for entry in inventory:
            source = directory / 'source-snapshot' / entry['path']
            assert file_digest(source) == entry['sha256'], (name, entry['path'])
        samples = resources['samples']
        peak_private = max(sample['private_bytes'] for sample in samples) / 1024**3
        minimum_available = min(sample['system_available_bytes'] for sample in samples) / 1024**3
        row = {'name': name, 'template': template, 'ratio': ratio, 'settings': result['settings'],
               'render_seconds': result['renderSeconds'], 'render_rtf': result['rtf'],
               'finalize_seconds': result['finalized']['wall_s'], 'supervisor_wall_seconds': resources['wall_s'],
               'peak_private_gib': peak_private, 'min_available_gib': minimum_available,
               'r0_sampled_pass': peak_private <= 12 and minimum_available >= 2,
               'r3_render_time_pass': result['renderSeconds'] <= 3000,
               'validation_wall_seconds': validation_resources['wall_s'],
               'decoded_frames': validation['decoded_frames'], 'timestamp_errors': validation['timestamp_errors'],
               'duration_s': validation['duration_s'], 'max_av_delta_ms': validation['max_av_delta_ms'],
               'tail_reference_correlation': validation['audio_windows'][-1]['reference_final_correlation'],
               'tail_final_raw_rms_ratio': validation['audio_windows'][-1]['rms_ratio_final_raw'],
               'bounded_bytes': (directory / 'bounded.mp4').stat().st_size,
               'output_hashes': validation['output_hashes'], 'validation_pass': True}
        rows.append(row)
    summary = {'cases': rows, 'completed': len(rows), 'decoded_frames': sum(row['decoded_frames'] for row in rows),
               'all_validation_passed': True, 'all_r0_sampled_pass': all(row['r0_sampled_pass'] for row in rows),
               'all_r3_render_time_pass': all(row['r3_render_time_pass'] for row in rows),
               'interactive_editor_tested': False, 'perceptual_audio_accepted': False,
               'collector_sha256': file_digest(Path(__file__))}
    (EVIDENCE / 'stress-suite-results.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
