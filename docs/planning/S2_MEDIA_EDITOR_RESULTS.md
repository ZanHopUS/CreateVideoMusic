# S2 — Multiple Media Editor and Launcher Follow-up

Ngày: **23/11/2026**. Phạm vi: **task đầu S2**, FR-103/301/302/307 và phần fit
cơ bản FR-304, cùng sửa lỗi launcher đã quan sát thực tế. Chưa hoàn tất S2/Core;
Music Card, lyrics nhập tay, effects/typography mở rộng còn ở bước tiếp theo.
Không đổi A–G/process boundary/schema timebase; không thêm dependency/model.

## Đã triển khai

- Chọn nhiều ảnh/video/nhạc trong một batch; server probe media thật. File lỗi có
  báo tên, các file hợp lệ vẫn được thêm thành một history transaction. Chặn thao
  tác async chồng nhau/chuyển nhầm project trong lúc import.
- Batch hình ảnh/video đầu chia project duration, không vượt video source; các
  batch tiếp theo nối sau clip đã có, tăng project duration tới tối đa 300s.
  Không tự thay/xóa clip đã chỉnh. Nhạc là các clip riêng, video nền muted.
- Chọn/kéo clip theo frame; inspector hỗ trợ source trim video/audio, duration,
  fit cover/contain; hiển thị tên media. Reorder xếp montage liền nhau trong track,
  giữ IDs/sourceStart/duration/style; gỡ clip chỉ bỏ refs, không xóa library bytes.
- Undo/Redo, optimistic working save, manual checkpoint và reopen giữ clips/order/
  trim/style. Frontend kiểm source windows/kind như backend, có xét playback rate.
  Project v1 cũ vẫn hợp lệ; không migrate hoặc viết lại project user khi nâng cấp.
- Backend render TPL-01 nhận cả image/video/audio/text; scene/time adapter chung
  Player/export được giữ. Preset hiện tại vẫn chỉ 720×1280/30FPS.

## Launcher

Windows mutex chỉ cho một launcher/workspace. API/Next được tạo suspended, gán
vào Job Object kill-on-close trước khi resume primary thread, nên venv launcher
không tạo Python child ngoài phạm vi ở thời điểm gán ownership. Khi root launcher
bị kết thúc đột ngột, OS dọn API/Next và descendants. Default browser không thuộc
job; restart chỉ kết thúc đúng handle owner đã đối chiếu PID/create-time/cwd/script,
không quét và kill browser/user processes.

Thêm `start.ps1 -Restart` và `stop.ps1`; owner record chỉ có PID/create-time,
không chứa session token. Đã chạy smoke khởi–dừng–khởi hai lần và restart thật
từ một phiên NoBrowser. Project/media local giữ nguyên. Đây là sửa lifecycle
launcher, không đóng toàn bộ gate render cancel/recovery/TOCTOU ở S4.

## Verification

| Kiểm tra | Kết quả |
|---|---|
| Vitest | **17 pass**, gồm 6 case mới cho batch, append atomic, reorder/ref/source bounds |
| pytest | **14 pass**, gồm singleton, parent exit thật dọn child/grandchild, forged owner không dừng process khác |
| Browser E2E | **2 pass** trong suite render: montage mới và TPL-01 regression |
| Browser partial-error case | **1 pass riêng**, batch một file hỏng không mất clip/chỉnh sửa cũ |
| Build/typecheck/format/lint | Đạt; không thêm dependency |
| Output độc lập | Montage 3s: **90 frames**; regression 2s: **60 frames**, 0 timestamp errors, H.264/AAC và audio decode |

E2E dùng PNG/WAV và video CFR 180×320/30FPS/4s tự tạo, upscale output 720p.
Riêng OS picker trong browser E2E là fixture grants; native picker đã có evidence
S0/S1, không gọi fixture này là kiểm native picker mới.

Montage sau reorder là ảnh → video → ảnh. Kiểm sparse RGB ngoài vùng caption ở
frames 15/45/75 so nguồn: mean absolute error **1.17 / 3.44 / 0.78**, đạt ngưỡng
≤20; điểm video dùng source t=1.0s với trimStart=0.5s. So theo tâm texel sau scale;
so tọa độ cạnh ban đầu làm sample chạm mép color bars và đã được sửa phép đo,
không tăng threshold hoặc chỉnh output để đạt. Đây không là full-frame/perceptual
fidelity hoặc bằng chứng VFR/100ms cho mọi input.

Peak private children render/finalize khoảng **1.011 GiB**, min global available
**3.700 GiB** ở montage; chỉ sampled child scope, chưa đo API/editor/UI P95/FPS.
Không thay stress PoC bằng E2E 3s hoặc đánh FR Verified từ các fixtures này.

Raw evidence: [summary](../../.local/evidence/s2-media/summary.json),
screenshots/source/output inventories trong `.local/evidence/s2-media/`;
run IDs và hashes giữ riêng, không ghi đè S0/S1 hoặc media user. Tests/lệnh chạy
ở [README](../../README.md). Giữ A–G, lyrics quality/Drive/S4 release blockers.

Git: `dev`. Commit đề xuất tại thời điểm kiểm thử:
`feat(editor): support multiple media clips and safe launcher restart`.
