# MP4 Audio Duration Experiment

Ngày: **22/11/2026 (Asia/Saigon)**. POC-03 follow-up trên các file local tự tạo.
Không sửa matrix gốc, preview Việt đã duyệt, PRD/SRS hoặc quyết định A–G.

## Vấn đề và phép thử

Matrix ban đầu có video **15.000s**, nhưng AAC/container **15.019s**. Vì 19ms
lớn hơn một frame 60FPS (khoảng 16.67ms), 18 bản 60FPS chưa đạt nếu chấm duration
toàn container. Đây là khác biệt duration đã đo, chưa chứng minh drift nghe được.

Thử trên bản sao TPL03 dọc 1080p60, dùng FFmpeg độc lập đã có trong venv:

| Phương án | Video | Audio/container | Kết quả |
|---|---:|---:|---|
| Copy streams, thêm `-t 15` | 15.000s | 15.019s | Không giải quyết |
| Copy video, encode lại AAC, trim và `-t 15` | 15.000s | 15.000s | Đạt phép thử duration |

Nhánh thứ hai dùng `-c:v copy -c:a aac -ar 48000 -b:a 192k`,
`-af atrim=duration=15,asetpts=PTS-STARTPTS -t 15 -movflags +faststart`.
Không sửa package trong node_modules. Source Remotion cài local có logic AAC
priming riêng; chưa quy nguyên nhân phần đuôi cho một bug upstream cụ thể.

## Đối chứng đủ 36 file

Áp dụng nhánh thứ hai vào **36 bản sao mới**, không render lại video:

- **36/36**: H.264 packet payload SHA-256 giống input; video không qua encode lại.
- **36/36**: video/audio/container 15.000s; duration container đạt ≤1 frame ở cả 30/60FPS.
- Decode **24.300 video frames** và toàn bộ audio thành công, không lỗi timestamp.
- **36/36** có đủ ba flash/click tại 0/5/10s; max AV delta khoảng **0.0417ms** theo detector.
- Supervisor wall cho toàn bước finalize **8.078s**; peak sampled private khoảng
  **0.067 GiB**, min available **6.062 GiB**. Đây là audio-only operation,
  không phải tốc độ render 36 video mới hoặc một benchmark lặp.

Validator có cờ `--strict-container-duration`; duration fail làm exit code 2.
Case manifest ghi rõ `source_render_seconds` và `finalize_seconds` để không trộn
thời gian render cũ với phép thử mới.

## Giới hạn và quyết định

Đây là **candidate workaround cho PoC**, chưa là pipeline sản phẩm được duyệt.
Audio qua thêm một thế hệ lossy encoding; chưa có listening A/B hoặc đánh giá
chất lượng trên nhạc thật. Matrix ngắn kết thúc bằng silence, nên riêng kết quả
này không chứng minh âm thanh sát cuối bài được bảo toàn.

Stress 300s đã bổ sung tín hiệu 299.9–300s và đối chiếu raw/final/reference ở đầu,
giữa, cuối, gồm 50ms cuối. Các phép đo tín hiệu đạt trên lượt đó; xem
[RENDER_STRESS_RESULTS.md](RENDER_STRESS_RESULTS.md). Chưa thay listening review.
Trước lựa chọn production nên so sánh phương án chỉ encode AAC một lần từ audio
lossless; không tự chốt workaround hiện tại thành kiến trúc.

R1 đầy đủ vẫn mở vì còn template fixtures/fidelity; 36 duration checks mới chỉ
giải quyết giới hạn đã quan sát cho các bản sao này.

## Bằng chứng và tái lập

- [A/B ffprobe — copy limit](../../.poc/evidence/poc-03/audio-duration-probe/copy-limit.ffprobe.json),
  [AAC re-encode](../../.poc/evidence/poc-03/audio-duration-probe/audio-reencode.ffprobe.json).
- [Summary](../../.poc/evidence/poc-03/bounded-audio-matrix/summary.json),
  [validation](../../.poc/evidence/poc-03/bounded-audio-matrix/validation.json),
  [resources](../../.poc/evidence/poc-03/bounded-audio-matrix/resources/resources.json).
- [Runbook](../../poc/render/STRESS_RENDER.md),
  [finalizer](../../poc/render/finalize_mp4.py),
  [batch experiment](../../poc/render/bound_matrix_audio.py).

Toàn bộ MP4/raw evidence Git-ignored. Checkpoint trước đó đã push `dev` commit
`c3affcc` theo yêu cầu user; script/báo cáo thí nghiệm mới này chưa commit/push.
