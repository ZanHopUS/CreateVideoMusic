"""Run the four remaining planned stress cases sequentially, with resource gates."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / '.poc/evidence/poc-04'
CASES = [('TPL01', '9-16'), ('TPL02', '9-16'), ('TPL03', '16-9'), ('TPL03', '1-1')]


def main():
    summary_path = EVIDENCE / 'remaining-stress-batch.json'
    assert not summary_path.exists(), 'Preserve the completed batch; do not overwrite it'
    started = time.perf_counter()
    rows = []
    batch = {'cases': rows, 'state': 'running', 'planned': len(CASES),
             'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}

    def save():
        batch['wall_s'] = time.perf_counter() - started
        summary_path.write_text(json.dumps(batch, indent=2), encoding='utf-8')

    save()
    for template, ratio in CASES:
        name = f'{template.lower()}-{ratio}-300s-1080p60'
        directory = EVIDENCE / name
        row = {'name': name, 'template': template, 'ratio': ratio, 'state': 'rendering'}
        rows.append(row)
        save()
        print(json.dumps(row), flush=True)
        command = [sys.executable, str(ROOT / 'poc/monitor.py'), '--out', str(directory / 'resources'),
                   '--timeout', '3000', '--', 'node', str(ROOT / 'poc/render/render-stress.mjs'),
                   '--template', template, '--ratio', ratio]
        render = subprocess.run(command, cwd=ROOT)
        if render.returncode:
            row.update(state='render-failed', exit_code=render.returncode)
            batch['state'] = 'stopped-on-failure'
            save()
            raise SystemExit(render.returncode)
        row['state'] = 'validating'
        save()
        validation = subprocess.run([sys.executable, str(ROOT / 'poc/monitor.py'), '--out',
            str(directory / 'validation-resources'), '--timeout', '300', '--', sys.executable,
            str(ROOT / 'poc/render/validate_stress.py'), '--template', template, '--ratio', ratio], cwd=ROOT)
        if validation.returncode:
            row.update(state='validation-failed', exit_code=validation.returncode)
            batch['state'] = 'stopped-on-failure'
            save()
            raise SystemExit(validation.returncode)
        validated = json.loads((directory / 'validation.json').read_text(encoding='utf-8'))
        assert validated['all_passed']
        result = json.loads((directory / 'render-result.json').read_text(encoding='utf-8'))
        resources = json.loads((directory / 'resources/resources.json').read_text(encoding='utf-8'))
        row.update(state='passed', render_seconds=result['renderSeconds'], rtf=result['rtf'],
            peak_private_gib=max(s['private_bytes'] for s in resources['samples']) / 1024**3,
            min_available_gib=min(s['system_available_bytes'] for s in resources['samples']) / 1024**3,
            decoded_frames=validated['decoded_frames'], max_av_delta_ms=validated['max_av_delta_ms'])
        save()
        print(json.dumps(row), flush=True)
    batch['state'] = 'completed'
    save()
    print(json.dumps(batch), flush=True)


if __name__ == '__main__':
    main()
