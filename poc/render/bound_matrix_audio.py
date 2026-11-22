"""Create bounded-audio copies; never replace the original 36-case evidence."""
import json
from pathlib import Path

from finalize_mp4 import finalize

ROOT = Path(__file__).resolve().parents[2]
source = ROOT / '.poc/evidence/poc-03/preset-matrix'
destination = ROOT / '.poc/evidence/poc-03/bounded-audio-matrix'
destination.mkdir(parents=True, exist_ok=True)
assert not (destination / 'render-results.json').exists(), 'Use a fresh experiment directory'
settings = json.loads((source / 'render-results.json').read_text(encoding='utf-8'))
for index, case in enumerate(settings):
    result = finalize(source / f"{case['name']}.mp4",
                      destination / f"{case['name']}.mp4", case['seconds'])
    case['source_render_seconds'] = case.pop('renderSeconds')
    case['source_render_rtf'] = case.pop('rtf')
    case['operation'] = 'audio-only finalization; video packets copied'
    case['finalize_seconds'] = result['wall_s']
    print(json.dumps({'completed': index + 1, 'total': len(settings),
                      'name': case['name'], 'finalize_seconds': result['wall_s']}), flush=True)
(destination / 'render-results.json').write_text(json.dumps(settings, indent=2), encoding='utf-8')
