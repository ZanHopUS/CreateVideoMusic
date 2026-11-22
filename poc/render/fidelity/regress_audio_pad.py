"""Check the EOF fix and retain the independently generated 300s tail signal."""
import importlib.util
import json
from pathlib import Path
import sys

import av
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'poc/render'))
from finalize_mp4 import finalize

spec = importlib.util.spec_from_file_location('stress_measurement', ROOT / 'poc/render/validate_stress.py')
measurement = importlib.util.module_from_spec(spec)
spec.loader.exec_module(measurement)
directory = ROOT / '.poc/evidence/poc-03/fidelity/audio-pad-regression'
directory.mkdir(parents=True, exist_ok=False)
old_short = ROOT / '.poc/evidence/poc-03/fidelity/full-01/TPL02/export.mp4'
with av.open(str(old_short)) as container:
    audio = container.streams.audio[0]
    before = float(audio.duration * audio.time_base)
short = finalize(ROOT / '.poc/evidence/poc-03/fidelity/full-01/TPL02/raw.mp4', directory / 'bounded-12.mp4', 12)
source = ROOT / '.poc/evidence/poc-04/tpl03-9-16-300s-1080p60'
long = finalize(source / 'raw.mp4', directory / 'bounded-300.mp4', 300)
_, previous = measurement.audio_measurements(source / 'bounded.mp4')
_, current = measurement.audio_measurements(directory / 'bounded-300.mp4')
correlation = float(np.corrcoef(previous[-1], current[-1])[0, 1])
rms_ratio = float(np.sqrt(np.mean(current[-1] ** 2) / np.mean(previous[-1] ** 2)))
result = {'short_audio_before_s': before, 'short_after_s': short['duration_s'],
          'long_after_s': long['duration_s'], 'last_50ms_old_new_correlation': correlation,
          'last_50ms_old_new_rms_ratio': rms_ratio,
          'last_50ms_rms': float(np.sqrt(np.mean(current[-1] ** 2)))}
result['all_passed'] = abs(before - 11.989) < .001 and correlation >= .98 and .9 <= rms_ratio <= 1.1 and result['last_50ms_rms'] > .005
(directory / 'validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
assert result['all_passed']
