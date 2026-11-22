# Vietnamese lyric review preview

Diagnostic PoC using the actual `vi-001` audio and author-loader alignment. No new
model/dependency is needed. Media, lyric payloads and outputs stay under `.poc/`.

## Reproduce from repository root

```powershell
./.poc/venv-asr/Scripts/python.exe poc/render/prepare_lyrics_review.py
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-03/vi-lyrics-review/resources --timeout 900 -- node poc/render/render-lyrics-review.mjs
./.poc/venv-asr/Scripts/python.exe poc/render/validate_lyrics_review.py
```

Requires the existing render npm environment/browser and private alignment output.
FFmpeg preparation and ffprobe validation use native binaries inside the PoC tools.

## Fixture and interpretation

- Source range: **43.0–76.9s**; 33.9s, 720×1280, 30FPS, 1,017 frames.
- Includes full reference cues 3–9: six word drafts and cue 5 sentence fallback.
- Audio is cropped from the original copied M4A and decoded to stereo PCM16/48kHz.
- The same source-time mapping controls all lyric state: `43 + frame/30`.
- Word mode shows the complete line and highlights only the active aligned word.
  Gaps between words have no active highlight. Fallback shows the full cue without
  inventing per-word timings. On-screen labels and review instructions are Vietnamese.
- Exact timing boundaries, fallback behavior and a real active-word frame are checked
  before rendering. The half-open interval `[start,end)` prevents stale cue selection.

## Evidence

`.poc/evidence/poc-03/vi-lyrics-review/` contains:

- `vi-lyrics-review.mp4`, `word.png`, `fallback.png`: review artifacts.
- `input.json`, `provenance.json`: private lyric/timing inputs, hashes and crop command.
- `render-result.json`, `resources/`: elapsed time, code hashes and RAM samples.
- `ffprobe.json`, `validation.json`: real output integrity and audio checks.

Validation fully decodes the video, checks codec/dimensions/FPS/duration and verifies
the gold active-word underline at the word frame and its absence in the fallback
lyric region. Geometric run length distinguishes it from colored font-edge pixels
caused by subpixel antialiasing or lossy video encoding.
Cross-correlation compares the cropped reference audio against decoded AAC in three
2s windows; this checks preservation of the audio crop, not whether the model's word
timestamps are acoustically correct. Do not claim human timing review from these checks.

Cue 5 is visible approximately **10.61–15.00s within the preview**; all its words remain
static in sentence mode. Use this region and the word-mode regions for listening review.
The video remains a draft. It does not replace the planned 36-preset render matrix,
300s stress tests, interactive editor or release acceptance.
