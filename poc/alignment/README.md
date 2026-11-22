# Local alignment harness

PoC only, Windows/Python 3.12, CPU. Uses supplied reference text inside supplied SRT
cue windows. This is not an application editor or an ASR replacement. No cloud inference.

## Setup

Run from repository root. Keep the ASR venv unchanged:

```powershell
python -m venv .poc/venv-align
./.poc/venv-align/Scripts/python.exe -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0+cpu torchaudio==2.8.0+cpu torchvision==0.23.0+cpu
./.poc/venv-align/Scripts/python.exe -m pip install --index-url https://pypi.org/simple -r poc/alignment/requirements.txt
./.poc/venv-align/Scripts/python.exe poc/alignment/prepare_models.py
./.poc/venv-asr/Scripts/python.exe poc/alignment/prepare_audio.py
```

Model preparation downloads required model/config/tokenizer files and the Vietnamese
author's reviewed `model_handling.py`, with fixed revisions and SHA-256 checksums.
It also prepares NLTK data under `.poc/`. It performs no
inference. The Vietnamese checkpoint is CC BY-NC 4.0 for the approved personal
non-commercial PoC; the English checkpoint is Apache 2.0. Record source/license
from the model inventories before considering redistribution or another purpose.

The Vietnamese model has a custom `feature_transform` layer. Its default loader here
uses the author's class, checks source SHA-256 before execution, and rejects missing,
unexpected or mismatched weights. No automatic remote-code loading is enabled.
The generic WhisperX loader ignored this layer in the baseline and produced very low
scores; that baseline is retained separately. `--vi-loader standard --run-id vi-001-standard`
reproduces the generic-loader candidate without overwriting the author-loader result.
See the pinned [author model source](https://huggingface.co/nguyenvulebinh/wav2vec2-base-vi-vlsp2020/blob/50a30dadb3ec98a0d4cdb1eb1ea315aff538f7c2/model_handling.py).

## Run

```powershell
./.poc/venv-asr/Scripts/python.exe poc/alignment/run.py --self-test
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-02/vi-001-smoke-resources --timeout 240 -- ./.poc/venv-align/Scripts/python.exe -X utf8 poc/alignment/run.py --sample vi-001 --limit-cues 3
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-02/vi-001-author/resources --timeout 900 -- ./.poc/venv-align/Scripts/python.exe -X utf8 poc/alignment/run.py --sample vi-001 --run-id vi-001-author
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-02/en-001/resources --timeout 900 -- ./.poc/venv-align/Scripts/python.exe -X utf8 poc/alignment/run.py --sample en-001
./.poc/venv-asr/Scripts/python.exe poc/alignment/validate.py
```

Run samples sequentially. Preflight requires 3.25 GiB system RAM available; supervisor
stops the job if available RAM stays below 2 GiB for 10s or private workload exceeds
12 GiB. Model threads: 4. Offline flags/local files are used during inference;
implicit NLTK downloads are rejected. No network isolation claim is made without
an independent network test.

## Outputs and interpretation

`.poc/evidence/poc-02/<run-id>/` contains `alignment.json`, `review.tsv` and
`hybrid-draft.srt`. Smoke runs use separate directories and do not overwrite full
results. Raw text, audio, models, environments and outputs remain Git-ignored.

- `word_draft`: all reference whitespace units have finite, ordered, in-window timing
  and scores >=0.25; this uncalibrated screening score is not accuracy/confidence.
- `sentence_fallback`: retain the user-supplied cue timing when the word checks fail;
  do not fabricate word timestamps. `interpolate_method="ignore"` is explicit.
- Original references and excluded non-verbal English cues remain intact. Parenthetical
  Vietnamese backing lyrics are included. Every output still requires timing review.
- Cue windows constrain the result, so similarity to the SRT is not independent
  evidence of timing accuracy. Word MAE/P95 remain unknown without manual annotations.

Per-run reports preserve model revisions/versions and errors. Do not label requirements
Verified merely because all words received timestamps or SRT export succeeded.
