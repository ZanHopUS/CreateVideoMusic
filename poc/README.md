# Local Proof of Concept

State/Undo/Redo, template reuse và SQLite/manual/recovery/portable local:
[state-storage/README.md](state-storage/README.md). Có functional evidence; render
restore từng fail R0 RAM, một lượt admission follow-up đã đạt sampled R0.
Đọc giới hạn trước chạy lại.

Forced alignment CPU và loader Việt: [poc/alignment/README.md](alignment/README.md).

Preview lời Việt với audio và timing thật: [render/LYRICS_REVIEW.md](render/LYRICS_REVIEW.md).

Benchmark ASR `small`/`medium` cùng điều kiện: [lyrics/MODEL_COMPARISON.md](lyrics/MODEL_COMPARISON.md).

Audio duration và stress 300s: [render/STRESS_RENDER.md](render/STRESS_RENDER.md).

Kết quả đủ năm stress outputs: [RENDER_STRESS_SUITE_RESULTS.md](../docs/technical-discovery/RENDER_STRESS_SUITE_RESULTS.md).

Player fidelity và cancel/retry/snapshot: [render/fidelity/README.md](render/fidelity/README.md).

Chỉ dùng cho thử nghiệm đã duyệt ngày 22/11/2026; không phải application chính thức.
Cloud inference tắt. Không commit/push khi chưa được yêu cầu.

## Artifacts

`.poc/` tại root giữ venv, model, cache, media và raw evidence; đã được ignore khỏi Git.
`poc/lyrics/requirements.txt` pin các dependency trực tiếp; pip freeze và install report
ghi dependencies thực tế trong evidence. Không sửa Python global.

## Lyrics executable smoke

Chạy từ repository root trên PowerShell:

```powershell
python -m venv .poc/venv-asr
./.poc/venv-asr/Scripts/python.exe -m pip install -r poc/lyrics/requirements.txt
./.poc/venv-asr/Scripts/python.exe poc/lyrics/prepare.py --download-model
./.poc/venv-asr/Scripts/python.exe poc/lyrics/smoke.py
```

`prepare.py` đọc môi trường, kiểm FFmpeg độc lập và tải small multilingual từ revision
đã resolve; ghi SHA-256 từng file. `smoke.py` chỉ dùng silence/tone/noise tự tạo,
CPU INT8, 4 threads, tiếng Việt/Anh, VAD on/off. Không tự áp dụng lyrics.
Kết quả này không chứng minh chất lượng hát hoặc khả năng phát hiện instrumental.
Offline flags ngăn Hugging Face tải model; chưa thay thế kiểm thử network isolation.

Mẫu user đầu tiên được copy thành `.poc/data/user/vi-001.m4a` với manifest riêng.
Chạy lại đối chứng không VAD (không ghi đè bản VAD-on):

```powershell
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-01/vi-001-no-vad/resources --timeout 960 -- ./.poc/venv-asr/Scripts/python.exe -X utf8 poc/lyrics/transcribe.py --sample vi-001 --run-id vi-001-no-vad --no-vad
```

TXT/SRT là draft với ASR segment timing, chưa forced alignment hoặc review.
Không dùng bản draft làm ground truth để tính WER/CER.

Đánh giá với SRT user cung cấp đã copy thành `.poc/data/user/vi-001.reference.srt`:

```powershell
./.poc/venv-asr/Scripts/python.exe -X utf8 poc/lyrics/evaluate.py --self-test
./.poc/venv-asr/Scripts/python.exe -X utf8 poc/lyrics/evaluate.py
```

Script dùng whitespace-unit edit rate và CER giữ dấu; lưu raw evaluation và bảng
review theo cue vào `.poc/evidence/poc-01/vi-001-reference-evaluation/`. Cue overlap
chỉ hỗ trợ review, không là forced alignment hoặc phép đo word timing accuracy.

Mẫu Anh `en-001` có audio 301.418s; chạy cùng baseline trên 300s đầu, giữ nguồn:

```powershell
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-01/en-001/resources --timeout 960 -- ./.poc/venv-asr/Scripts/python.exe -X utf8 poc/lyrics/transcribe.py --sample en-001 --max-seconds 300
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-01/en-001-no-vad/resources --timeout 960 -- ./.poc/venv-asr/Scripts/python.exe -X utf8 poc/lyrics/transcribe.py --sample en-001 --run-id en-001-no-vad --no-vad --max-seconds 300
./.poc/venv-asr/Scripts/python.exe -X utf8 poc/lyrics/evaluate.py --sample en-001 --exclude-cues 1,2,6,9,11,12,107,108,111
```

`--exclude-cues` chỉ thêm phép đo bổ sung cho các cue non-verbal đã được phân loại;
điểm so nguyên SRT vẫn giữ. Không dùng danh sách của mẫu Anh cho reference khác.
Evaluator từ chối chấm nếu reference nằm ngoài phần audio đã xử lý.

## Dữ liệu từ TikTok/YouTube

Nguồn dự kiến là file do người dùng cung cấp có quyền dùng: bản gốc của chính mình,
file tác giả cho phép hoặc bản có license phù hợp. Mục đích cá nhân phi thương mại
không được dùng làm bằng chứng thay cho quyền của từng recording/lyrics.
Không có URL downloader trong PoC.

Với YouTube, có thể tìm clip được gắn Creative Commons Attribution, kiểm tra người
đăng có quyền với nội dung và ghi attribution/license; ưu tiên file do tác giả cung
cấp. [YouTube license guidance](https://support.google.com/youtube/answer/2797468).

Đặt file được phép vào `.poc/data/user/` và ghi source URL, tác giả, license/permission,
language, đoạn cần thử và lyrics chuẩn. Chưa có file/manifest hợp lệ thì quality gates
L1–L4/L6 vẫn Not run. Không dùng lời ASR sinh ra làm ground truth.

## Rendering

`poc/render/` là harness riêng, không phải editor app. Dependencies được pin trong
package.json/package-lock.json; outputs và generated assets nằm dưới `.poc/`.
Chỉ test fixtures tự tạo; lyric highlight minh họa không phải forced alignment.
Các bản xuất smoke không thay cho đo interactive preview, 300s stress hay E2E release.

```powershell
./.poc/venv-asr/Scripts/python.exe poc/render/prepare_assets.py
npm.cmd ci --prefix poc/render
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-03/resources --timeout 900 -- node poc/render/render.mjs
./.poc/venv-asr/Scripts/python.exe poc/render/validate.py
```

`render.mjs` mặc định chạy ba fixture 720p30; `--matrix` mở rộng 36 trường hợp theo
plan, lưu riêng để giữ smoke ban đầu. Lệnh chạy, resume và giới hạn phép đo:
[render/RENDER_MATRIX.md](render/RENDER_MATRIX.md). Giữ RAM safety monitor khi chạy.
