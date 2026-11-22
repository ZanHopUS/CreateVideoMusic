"""Experimental PoC finalizer: copy H.264 and re-encode bounded AAC audio."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import av
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[2]


def video_digest(path):
    digest = hashlib.sha256()
    count = 0
    with av.open(str(path)) as container:
        for packet in container.demux(video=0):
            if packet.size:
                digest.update(bytes(packet))
                count += 1
    return {"packets": count, "sha256": digest.hexdigest()}


def finalize(source, output, seconds):
    source, output = Path(source).resolve(), Path(output).resolve()
    assert source.is_file() and source != output
    assert output.is_relative_to(ROOT / '.poc') and not output.exists()
    assert source.suffix == output.suffix == '.mp4' and 0 < seconds <= 300
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-loglevel', 'error',
               '-n', '-i', str(source), '-map', '0:v:0', '-map', '0:a:0',
               '-c:v', 'copy', '-c:a', 'aac', '-ar', '48000', '-b:a', '192k',
               '-af', f'atrim=duration={seconds},asetpts=PTS-STARTPTS',
               '-t', str(seconds), '-movflags', '+faststart', str(output)]
    began = time.perf_counter()
    subprocess.run(command, check=True)
    before, after = video_digest(source), video_digest(output)
    assert before == after, 'H.264 packet payload changed'
    with av.open(str(output)) as container:
        video, audio = container.streams.video[0], container.streams.audio[0]
        measured = {'video_s': float(video.duration * video.time_base),
                    'audio_s': float(audio.duration * audio.time_base),
                    'container_s': container.duration / av.time_base}
        assert video.codec_context.name == 'h264' and audio.codec_context.name == 'aac'
        assert all(abs(value - seconds) <= .001 for value in measured.values()), measured
    result = {'command': command, 'wall_s': time.perf_counter() - began,
              'duration_s': measured, 'video_payload': after,
              'audio_reencoded': True, 'audio_quality_accepted': False}
    output.with_suffix('.finalize.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=float, required=True)
    args = parser.parse_args()
    print(json.dumps(finalize(args.input, args.output, args.seconds)))
