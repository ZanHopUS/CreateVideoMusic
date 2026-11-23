# Bounded Audio and 300s Render Stress

POC-03/04 only; scripts run against generated media, outside the application.
Keep baseline matrix and accepted Vietnamese preview unchanged.

## Audio-duration experiment

`finalize_mp4.py` stream-copies H.264 and re-encodes AAC at 48 kHz/192 kbps,
with explicit audio trim and output duration. It refuses an existing destination,
checks identical video packet payload hashes, and checks video/audio/container
duration within 1ms. This is a candidate workaround, not a production default;
audio undergoes another lossy encode and needs listening review.

Follow-up fidelity testing added `apad=whole_dur` before trim to handle an observed
11ms short audio EOF at 1.25× speed. A separate regression verifies the original
300s tail signal. Padding fills missing duration with silence; it cannot restore
missing source content. See [fidelity results](../../docs/technical-discovery/PREVIEW_RENDER_FIDELITY_RESULTS.md).

```powershell
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-03/bounded-audio-matrix/resources --timeout 300 -- ./.poc/venv-asr/Scripts/python.exe poc/render/bound_matrix_audio.py
./.poc/venv-asr/Scripts/python.exe poc/render/validate.py --matrix --directory .poc/evidence/poc-03/bounded-audio-matrix --strict-container-duration
```

Run into a fresh evidence directory: the script deliberately refuses completed
results. `source_render_seconds`/`source_render_rtf` describe the earlier matrix;
`finalize_seconds` measures the new audio-only operation. Do not count it as a
second full render benchmark. Original files remain available for A/B comparison.

## Stress run

Prepare assets while no stress job is running. This creates a separate 300s WAV
with clicks every five seconds and a tone at 299.9–300s; the video is a looped
15s test pattern. It is resource/timing evidence, not 300s of independent content.

```powershell
./.poc/venv-asr/Scripts/python.exe poc/render/prepare_stress.py
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-04/tpl03-9-16-300s-1080p60/resources --timeout 3000 -- node poc/render/render-stress.mjs
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-04/tpl03-9-16-300s-1080p60/validation-resources --timeout 300 -- ./.poc/venv-asr/Scripts/python.exe poc/render/validate_stress.py
```

The renderer uses 1080×1920, 60FPS, concurrency 2, one offthread video thread,
64 MiB cache, x264 ultrafast and disabled hardware encoding. It writes `raw.mp4`,
then `bounded.mp4`, both ffprobe reports, source hashes and three PNGs. A completed
directory cannot be overwritten. `--ratio 16-9` and `--ratio 1-1` select separate
directories; pass the same ratio to the validator. They are not automatically run.

## Separate admission follow-up runs

`--run-id` creates a separate suffixed directory and bundle; pass the same ID to
the validator. Omit it to retain original case paths. Existing raw/bounded MP4,
run config or error evidence blocks another render into that directory.
Use a new ID for every retry, including admission-only denial:

```powershell
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-04/tpl03-9-16-300s-1080p60-admission-02/resources --timeout 3000 --min-start-available-gib 4 --start-samples 10 --admission-timeout 30 -- node poc/render/render-stress.mjs --run-id admission-02
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-04/tpl03-9-16-300s-1080p60-admission-02/validation-resources --timeout 300 -- ./.poc/venv-asr/Scripts/python.exe poc/render/validate_stress.py --run-id admission-02
```

Run validation only after a completed render. Admission exit 4 means no child
started, not a render quality failure or pass. Stable ≥4 GiB startup headroom is
a candidate harness policy; R0 remains available ≥2 GiB during execution.
Inspect `r0_sampled_pass` independently of completion. Do not run parallel stress
jobs or regenerate shared input assets while a job is active.

## Four remaining planned cases

`--template TPL01|TPL02|TPL03` selects the fixture; default is TPL03.
TPL01 is image/caption; TPL02 contains two generated artworks and a Music Card;
TPL03 is the looped video fixture. TPL01/02 stress is limited to portrait as planned.
Use matching template/ratio arguments for validation.

```powershell
node poc/render/preflight-stress.mjs
./.poc/venv-asr/Scripts/python.exe poc/render/run_remaining_stress.py
```

The batch runs TPL01 portrait, TPL02 portrait, TPL03 landscape, then TPL03 square,
with a 3000s render timebox and a 300s validation timebox per case. It stops on
failure and preserves evidence. It refuses an existing batch manifest, so inspect
the saved state before retrying instead of overwriting a previous attempt.
Do not modify fixture/renderer/audio assets while the batch is running.

Each render stores a verified source snapshot with its inventory. The first
TPL03 portrait run was archived before extending the harness for templates.
Validation uses current files when their hashes match, otherwise the case's
archived files with the exact expected hashes. This preserves reproducibility
across harness revisions without silently accepting changed sources.

After all four new cases pass, verify all five full outputs and create small
viewing copies outside the benchmark measurements:

```powershell
./.poc/venv-asr/Scripts/python.exe poc/render/collect_stress_results.py
./.poc/venv-asr/Scripts/python.exe poc/render/create_stress_previews.py
```

The collector verifies original source snapshots, output hashes and successful
resource/validation records. Each viewing copy is 20s from source time 145–165s,
540 pixels wide at 30FPS; it is not the measured 300s/1080p60 export. The preview
script decodes all 600 preview video frames and its audio before reporting success.

The monitor samples child processes each second: stop at >12 GiB private bytes,
available RAM <2 GiB for 10s, or the 50-minute timebox. Progress percentages refer
only to the renderMedia phase, followed by finalization and validation.

## Validation scope

Decode all 18,000 final video frames, check CFR timestamps, exact dimensions,
codecs and durations. Check 60 flashes against 60 audio clicks plus the tail tone;
event timing tolerance is 100ms. Compare raw/final/generated audio in four windows
at 0–0.02s, 150–150.02s, 295–295.02s and 299.95–300s: correlation ≥0.98,
final/raw RMS ratio 0.9–1.1, final tail
RMS >0.005. These are signal screening checks, not perceptual audio acceptance.

Decoded AAC may include codec padding beyond the declared stream duration;
report decoded end separately. Do not equate padding alone with audible drift.
One run does not establish warm-run performance, UI responsiveness, network
isolation, cancel/retry, immutable snapshots, all five planned stress outputs,
VFR handling, or complete preview/export fidelity.
