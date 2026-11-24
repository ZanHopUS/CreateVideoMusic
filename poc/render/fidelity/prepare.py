"""Generated-only assets for preview/export fidelity; no dependencies are installed."""
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import zlib

import av
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[3]
directory = ROOT / '.poc/render/fidelity-public'
directory.mkdir(parents=True, exist_ok=True)
for source, target in [('background.mp4', 'cfr.mp4'), ('control.wav', 'control.wav')]:
    shutil.copy2(ROOT / '.poc/render/public' / source, directory / target)
svg = '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720"><rect width="1280" height="720" fill="#163c54"/><rect x="640" width="640" height="720" fill="#395c78"/><circle cx="340" cy="300" r="180" fill="#8dc8c4"/></svg>'
(directory / 'image.svg').write_text(svg, encoding='utf-8')
def chunk(kind, payload):
    return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload))
rows = b''.join(b'\0' + b''.join(bytes((255, 40, 80, 128 if (x // 16 + y // 16) % 2 else 0))
                               for x in range(128)) for y in range(128))
(directory / 'alpha.png').write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 128, 128, 8, 6, 0, 0, 0))
    + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))
vfr = directory / 'vfr.mp4'
if not vfr.exists():
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-loglevel', 'error', '-n',
        '-i', str(directory / 'cfr.mp4'), '-vf',
        "select='if(lt(t,5),not(mod(n,3)),if(lt(t,10),not(mod(n,2)),1))'",
        '-fps_mode', 'vfr', '-an', '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', str(vfr)], check=True)
with av.open(str(vfr)) as container:
    times = [float(frame.pts * frame.time_base) for frame in container.decode(video=0)]
deltas = sorted(set(round(b - a, 6) for a, b in zip(times, times[1:])))
assert len(deltas) >= 3, deltas
manifest = {'origin': 'generated local assets; no personal media', 'vfr_pts_deltas_s': deltas,
    'vfr_decoded_frames': len(times), 'audio_clicks_s': [0, 5, 10],
    'files': [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
              for p in sorted(directory.iterdir()) if p.is_file() and p.name != 'manifest.json']}
(directory / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest))
