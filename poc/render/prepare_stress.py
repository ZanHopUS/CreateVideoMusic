"""Prepare generated-only 300s assets in a separate public directory."""
import hashlib
import json
from pathlib import Path
import shutil
import wave

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
destination = ROOT / '.poc/render/stress-public'
destination.mkdir(parents=True, exist_ok=True)
rate, seconds = 48000, 300
with wave.open(str(destination / 'control.wav'), 'wb') as output:
    output.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
    for second in range(seconds):
        indices = np.arange(second * rate, (second + 1) * rate)
        active = (indices % (rate * 5) < rate * .02) | (indices >= int(299.9 * rate))
        values = np.where(active, .25 * np.sin(2 * np.pi * 880 * indices / rate), 0)
        output.writeframes((values * 32767).astype('<i2').tobytes())
source = ROOT / '.poc/render/public/background.mp4'
shutil.copyfile(source, destination / 'background.mp4')
manifest = {'origin': 'generated locally; no personal media', 'seconds': seconds,
            'audio_rate': rate, 'clicks_s': list(range(0, seconds, 5)),
            'tail_tone_s': [299.9, 300], 'background': '15s generated testsrc2, looped',
            'files': [{'name': p.name, 'bytes': p.stat().st_size,
                       'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                      for p in sorted(destination.glob('*')) if p.suffix in ('.wav', '.mp4')]}
(destination / 'provenance.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest))
