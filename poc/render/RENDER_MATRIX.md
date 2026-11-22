# Render Preset Matrix

Harness cho POC-03, chạy local trên Windows; không phải editor hoặc template sản phẩm.
Ba fixture tự tạo × ba ratios × hai resolutions × hai FPS = **36 MP4, mỗi file 15s**.
Không dùng nhạc hoặc lyrics cá nhân trong matrix này.

## Chuẩn bị

Dùng môi trường và dependencies đã pin theo [README](../README.md). Chỉ chạy
`prepare_assets.py` khi chưa có job render; script ghi lại assets tự tạo.
Không thay renderer, fixture, dependencies hoặc assets trong lúc chạy/resume.

## Chạy từ repository root

```powershell
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-03/preset-matrix/resources --timeout 3600 -- node poc/render/render.mjs --matrix --concurrency 2
./.poc/venv-asr/Scripts/python.exe poc/render/validate.py --matrix
```

Concurrency chỉ nhận 1 hoặc 2; mặc định 1. Monitor dừng nếu process-tree private
bytes >12 GiB, available RAM <2 GiB liên tục 10s hoặc hết timebox. Log và kết quả
lưu riêng trong `.poc/evidence/poc-03/preset-matrix/`; smoke ba file ban đầu và
preview lời Việt đã duyệt nằm ở thư mục khác.

Nếu job bị gián đoạn, kiểm tra `error.json`, logs và resources trước khi tiếp tục:

```powershell
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/evidence/poc-03/preset-matrix/resources-resume-01 --timeout 3600 -- node poc/render/render.mjs --matrix --concurrency 2 --resume
```

Resume yêu cầu cùng fingerprint của renderer/fixture/package-lock và cùng concurrency;
kiểm metadata file đã hoàn tất trước khi bỏ qua. Assets cũng phải giữ nguyên; fingerprint
hiện chưa bao gồm asset bytes. File của case chưa hoàn tất được tạo lại. Giữ logs của
từng attempt riêng; thời gian resume không phải thời gian chạy mới toàn matrix.

## Kiểm tra và giới hạn

Renderer dùng ffprobe kiểm H.264/AAC, kích thước, FPS, duration và frame count trước
khi ghi nhận case hoàn tất. Validator yêu cầu đủ 36 tên riêng biệt, decode toàn bộ
video/audio, kiểm timestamp CFR từng frame, audio 48 kHz và ba marker flash/click
tại 0/5/10s, lệch tuyệt đối và tương đối ≤100ms. Metadata và validation lưu JSON.
Duration container được ghi riêng với cờ `container_duration_within_one_frame`;
exit code thành công không chứng minh cờ này đúng ở mọi case. Xem báo cáo để
phân biệt video duration và đuôi audio/container.
PNG tại giây 5 hỗ trợ xem bố cục; không thay review video hoặc interactive preview.

TPL01 là ảnh/text, TPL02 là card/progress một ảnh, TPL03 là test video/highlight
minh họa. Chưa có đầy đủ hai ảnh, trim/rate/transition, VFR, state multi-track,
undo/redo, cancel/retry ứng dụng hoặc stress 300s. Vì vậy kết quả chỉ sàng lọc
preset encoder; không đánh FR-408/E2E-30 Verified hay fidelity gate R2 hoàn tất.
