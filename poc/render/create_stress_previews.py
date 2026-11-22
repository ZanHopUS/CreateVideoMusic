"""Create small 20s viewing copies after the benchmark jobs have completed."""
import json
from pathlib import Path
import subprocess

import av
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / '.poc/evidence/poc-04'
CASES = ['tpl01-9-16', 'tpl02-9-16', 'tpl03-9-16', 'tpl03-16-9', 'tpl03-1-1']

for case in CASES:
    directory = EVIDENCE / f'{case}-300s-1080p60'
    validation = json.loads((directory / 'validation.json').read_text(encoding='utf-8'))
    assert validation['all_passed'], case
    source, output = directory / 'bounded.mp4', directory / 'preview-20s-540p30.mp4'
    if not output.exists():
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-loglevel', 'error',
            '-n', '-ss', '145', '-i', str(source), '-t', '20', '-vf', 'scale=540:-2,fps=30',
            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '28', '-threads', '4',
            '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', str(output)], check=True)
    with av.open(str(output)) as container:
        assert abs(container.duration / av.time_base - 20) <= .04, case
        assert container.streams.video[0].width == 540
        assert float(container.streams.video[0].average_rate) == 30
        frames = sum(1 for _ in container.decode(video=0))
        assert frames == 600, (case, frames)
    with av.open(str(output)) as container:
        assert sum(frame.samples for frame in container.decode(audio=0)) > 0
    print(json.dumps({'case': case, 'file': str(output.relative_to(ROOT)),
                      'source_range_s': [145, 165], 'decoded_frames': frames,
                      'bytes': output.stat().st_size}), flush=True)
