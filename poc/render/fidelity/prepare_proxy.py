"""Optional CFR proxy candidate; preserve VFR source and its original manifest."""
import hashlib
import json
from pathlib import Path
import subprocess

import av
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[3]
p = ROOT / '.poc/render/fidelity-public'
source, output = p / 'vfr.mp4', p / 'vfr-cfr30.mp4'
assert not output.exists()
command = [imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-loglevel', 'error', '-n', '-i', str(source),
           '-vf', 'fps=30', '-an', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18', '-pix_fmt', 'yuv420p', str(output)]
subprocess.run(command, check=True)
with av.open(str(output)) as container:
    times = [float(f.pts * f.time_base) for f in container.decode(video=0)]
assert len(times) == 450 and all(abs((b-a)-1/30) < .000001 for a,b in zip(times,times[1:]))
manifest = {'method': 'FFmpeg fps=30; generated video-only proxy, source untouched', 'command': command,
    'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'proxy_sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'decoded_frames': len(times)}
(p / 'proxy-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest))
