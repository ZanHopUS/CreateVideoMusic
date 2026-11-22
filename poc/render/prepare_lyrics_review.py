"""Prepare a short private Vietnamese review clip with real alignment timings."""
import hashlib
import json
from pathlib import Path
import subprocess

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".poc"
source = LOCAL / "evidence/poc-02/vi-001-author/alignment.json"
alignment = json.loads(source.read_text(encoding="utf-8"))
start, end, fps = 43.0, 76.9, 30
frames = round((end - start) * fps)
rows = [row for row in alignment["rows"]
        if row["cue"]["start_s"] < end and row["cue"]["end_s"] > start]
assert [row["cue"]["cue_id"] for row in rows] == list(range(3, 10))
assert [row["cue"]["cue_id"] for row in rows if row["decision"]["mode"] == "sentence_fallback"] == [5]
public = LOCAL / "render/lyrics-review-public"
output = LOCAL / "evidence/poc-03/vi-lyrics-review"
public.mkdir(parents=True, exist_ok=True)
output.mkdir(parents=True, exist_ok=True)
command = [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
           "-i", str(LOCAL / "data/user/vi-001.m4a"), "-ss", str(start), "-t", str(end-start),
           "-vn", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(public / "review-audio.wav")]
subprocess.run(command, check=True)
payload = {"sourceStart": start, "sourceEnd": end, "fps": fps, "frames": frames,
           "width": 720, "height": 1280, "audioFile": "review-audio.wav",
           "rows": [{"cue": row["cue"], "mode": row["decision"]["mode"],
                     "words": row["decision"]["accepted_words"] if row["decision"]["mode"] == "word_draft" else []}
                    for row in rows],
           "reviewRequired": True}
(output / "input.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
(output / "provenance.json").write_text(json.dumps({
    "sample": "vi-001", "alignment_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "audio_sha256": hashlib.sha256((public / "review-audio.wav").read_bytes()).hexdigest(),
    "source_audio_sha256": alignment["source_audio_sha256"], "clip_start_s": start, "clip_end_s": end,
    "frames": frames, "fps": fps, "cue_ids": [row["cue"]["cue_id"] for row in rows],
    "fallback_cue_ids": [5], "audio_command": command,
    "timing_mapping": "sourceTime = 43 + frame/30; audio crop starts at source 43s",
}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"duration_s": frames/fps, "frames": frames, "cues": len(rows), "fallback_cues": [5]}))
