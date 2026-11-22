# Matched Vietnamese ASR model screening

Use the existing ASR venv; no new dependencies or cloud inference. Preserve prior
drafts, reference evaluations and the user-accepted alignment preview.

## Prepare and run

From the repository root:

```powershell
./.poc/venv-asr/Scripts/python.exe poc/lyrics/prepare.py --download-model --model medium
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-01/vi-001-small-seeded/resources --timeout 960 -- ./.poc/venv-asr/Scripts/python.exe -X utf8 poc/lyrics/transcribe.py --sample vi-001 --model small --run-id vi-001-small-seeded --no-vad --seed 42
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-01/vi-001-medium-seeded/resources --timeout 960 -- ./.poc/venv-asr/Scripts/python.exe -X utf8 poc/lyrics/transcribe.py --sample vi-001 --model medium --run-id vi-001-medium-seeded --no-vad --seed 42
./.poc/venv-asr/Scripts/python.exe -X utf8 poc/lyrics/compare_models.py
./.poc/venv-asr/Scripts/python.exe -X utf8 poc/lyrics/evaluate.py --sample vi-001 --runs vi-001-small-seeded vi-001-medium-seeded --evaluation-id vi-001-model-comparison-reference
```

Run models sequentially after downloads complete. The supervisor stops a job if the
process tree exceeds 12 GiB private memory, system available RAM remains below 2 GiB
for 10s, or the timebox expires. Keep any failure/partial output as evidence; never
report incomplete inference as a fast successful run.

## Comparison contract

- Same source M4A hash and full 296.681361s source range.
- CPU INT8, 4 threads, beam size 5, VAD off, previous-text conditioning off, seed 42.
- Same resolved library environment and complete decode-options record.
- The reference SRT is used only for evaluation; no lyrics prompt, prefix or hotwords
  are passed to ASR. This evaluates the audio-only path.
- Same reference hash, NFC/lowercase/punctuation normalization, whitespace-unit error
  rate and non-space CER retaining Vietnamese accents. Keep the full source text,
  including any ASR insertions outside reference cue times.

`compare_models.py` rejects mismatched input hashes/options or failed runs. It records
WER/CER edit counts, model revisions, model-load and decode/inference/partial-write
times, RTF, timestamp issues, sampled peak private memory and minimum available RAM.

## Evidence and limits

Raw outputs: `.poc/evidence/poc-01/vi-001-{small,medium}-seeded/`.
Comparison: `.poc/evidence/poc-01/vi-001-model-comparison/comparison.json`.
Per-cue review: `.poc/evidence/poc-01/vi-001-model-comparison-reference/lyric-review.tsv`.
All recordings, lyrics, model binaries and raw evidence remain Git-ignored.

These are matched single-song screening runs, not held-out validation or a cold/warm
median. Prior runs without an explicit seed remain historical evidence and must not
be silently substituted for the new paired baseline. Recording a seed does not prove
bitwise determinism across versions/hardware. Correction time, general singing quality
and instrumental hallucination behavior need their own tests before final selection.
