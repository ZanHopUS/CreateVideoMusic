# Player Fidelity and Render Lifecycle PoC

Run from repository root on Windows with the existing ASR venv and pinned
Remotion dependencies/browser. No dependency install, model download or cloud
request is part of these scripts. This is a harness, not the application editor.

## Assets and snapshots

`prepare.py` needs the generated `.poc/render/public/background.mp4` and
`control.wav` from the earlier render smoke. It writes a separate public directory
with SVG, RGBA PNG, CFR video, genuine VFR video and WAV plus hashes. Run setup
while no fidelity/lifecycle job is active. Do not mutate assets/bundles mid-job.

```powershell
./.poc/venv-asr/Scripts/python.exe -X utf8 poc/render/fidelity/prepare.py
New-Item -ItemType Directory -Force .poc/evidence/poc-03/fidelity | Out-Null
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-03/fidelity/full-02-resources --timeout 1200 -- node poc/render/fidelity/run.mjs --run-id full-02
./.poc/venv-asr/Scripts/python.exe -X utf8 poc/render/fidelity/validate.py --run-id full-02 --output-name validation-with-av.json
```

Use a fresh run ID: existing evidence directories are deliberately not overwritten.
Each snapshot contains 12 items and uses the same `FidelityScene` in Player/export.
`sourceStart` uses project-FPS time units, not a physical VFR frame ordinal.
The baseline renders three 12s/1280×720/30FPS MP4s, captures 27 Player/PNG pairs
per project, measures 100 programmatic seeks/project and a 60s simple playback.
Do not interpret event throughput as compositor/display FPS or editor UI latency.

Python independently checks active IDs/source time, decodes MP4s, detects audio
clicks/flashes and compares pixels. Thresholds: PSNR ≥30dB; source/AV timing ≤100ms;
duration ≤1 output frame. A failed check exits 1 and retains measured results.
`--quick` uses five probes, skips MP4/performance, and records skipped checks null.

**The baseline is expected to expose a fidelity failure** on the current VFR
fixture at frames 210/240/300. Preserve it as a negative test. Setup failures
smoke-01/02 and the earlier offset bug smoke-03 are not positive quality evidence.

## Optional candidates, default off

```powershell
./.poc/venv-asr/Scripts/python.exe -X utf8 poc/render/fidelity/prepare_proxy.py
node poc/render/fidelity/run.mjs --run-id proxy-smoke-01 --quick --proxy-vfr
./.poc/venv-asr/Scripts/python.exe -X utf8 poc/render/fidelity/validate.py --run-id proxy-smoke-01
node poc/render/fidelity/run.mjs --run-id nudge-full-01 --seek-nudge
./.poc/venv-asr/Scripts/python.exe -X utf8 poc/render/fidelity/validate.py --run-id nudge-full-01
```

Keep resource monitoring when running these commands outside a short preflight;
use the same monitor pattern above with a fresh `--out`. Proxy/nudge runs select
only TPL03 and skip performance repetitions. Proxy alone failed in the measured
smoke. Seek-nudge adds 0.0003 source frame (10µs at 30FPS) in the adapter, while
the original sourceStart and time oracle stay unchanged. It passed the measured
27-probe/MP4 case; it is not an approved production policy.

The harness uses the pinned renderer's internal CDP wrapper for screenshots;
that wrapper returns `{value, size}`. Bundler output must retain `bundle.js`.
Neither assumption is promised compatible with future versions.

## Real cancellation and immutable snapshot

Run after fidelity jobs stop; the worker uses the prepared render bundle:

```powershell
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-04/lifecycle/run-02-resources --timeout 480 -- ./.poc/venv-asr/Scripts/python.exe -X utf8 poc/render/fidelity/lifecycle.py --run-id run-02 --fidelity-run-id full-02
```

The controller sends cancel after ≥30 rendered frames, tracks owned process
identities by PID/create time, and checks API response ≤5s/tree exit ≤10s. With
supervision it can terminate only those owned identities after a 2s grace period
once cancellation is acknowledged. Forced cleanup is recorded explicitly.
`--api-only` disables that fallback to reproduce the measured ~30s worker linger;
the deadline assertion is expected to fail in that scenario.

Retry uses a fresh directory, freezes an input snapshot and edits a separate
working copy while rendering. Frame 150 must match the original reference
(PSNR ≥30dB) and exceed the edited reference by >3dB. Progress stays <100 until
final publish. `.partial` files are evidence and never counted as final success.
The 180s per-job test watchdog kills its own child tree if the test hangs.

Only render-phase cancellation is covered; finalization cancellation, crash,
disk-full, complete temp cleanup, actual editor undo/template state remain open.

## Audio EOF regression and evidence

`regress_audio_pad.py` uses the retained failed `full-01/TPL02` output and the
first generated 300s stress source. It checks the 11ms EOF-short case and the
last 50ms signal of the 300s output; it refuses an existing regression directory.
This script needs those earlier local fixtures, not personal recordings.

Raw configs, screenshots, MP4s, original failures, resource samples, measurements
and source hashes stay under `.poc/evidence/poc-03/fidelity/` and
`.poc/evidence/poc-04/lifecycle/`, Git-ignored. Source snapshots for the full
baseline/candidate and validator copies retain the versions used for measurement.

Reports: [fidelity](../../../docs/technical-discovery/PREVIEW_RENDER_FIDELITY_RESULTS.md),
[lifecycle](../../../docs/technical-discovery/JOB_LIFECYCLE_RESULTS.md).
