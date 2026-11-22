# Five-Case 300s Render Stress Results

Ngày tổng hợp: **23/11/2026 (Asia/Saigon)**; các lượt chạy 22–23/11/2026.
Phạm vi POC-04: **5/5 output stress đạt validation**, gồm bốn mẫu mới user yêu cầu
và TPL03 dọc đã chạy trước đó. Chưa nghiệm thu ứng dụng hoặc chốt kiến trúc.

## Kết quả

Mọi output cuối là H.264/AAC, 60FPS; video/audio/container đều **300.000s**.
Đơn vị thời gian dưới đây là renderMedia, không gồm setup/still/finalize/validation.

| Fixture | Kích thước | Render | RTF | Peak private GiB | Min available GiB | Validation |
|---|---|---:|---:|---:|---:|---|
| TPL01 ảnh/caption dọc | 1080×1920 | 713.376s ≈11:53 | 2.378 | 1.043 | 5.335 | Đạt |
| TPL02 hai artwork/Music Card dọc | 1080×1920 | 728.659s ≈12:09 | 2.429 | 1.060 | 5.533 | Đạt |
| TPL03 video nền dọc, lượt trước | 1080×1920 | 1,043.061s ≈17:23 | 3.477 | 2.111 | 3.844 | Đạt |
| TPL03 video nền ngang | 1920×1080 | 1,031.293s ≈17:11 | 3.438 | 1.552 | 4.659 | Đạt |
| TPL03 video nền vuông | 1080×1080 | 820.623s ≈13:41 | 2.735 | 1.483 | 4.717 | Đạt |

Batch **bốn mẫu mới** hoàn tất tuần tự trong **3,402.121s ≈56 phút 42 giây**,
gồm setup/render/stills/finalize/probe/validation. Cả năm render RTF <10, trong
ngưỡng ≤50 phút/file; không OOM hoặc bị monitor dừng. Sampling xấp xỉ một giây
có thể bỏ sót peak ngắn; private bytes không đồng nghĩa RAM vật lý riêng một process.

Đây là **một lượt/case**, không phải cold/warm repetitions. Các fixture khác độ
phức tạp; power/background load/OS cache chưa được kiểm soát đầy đủ. Không suy
speedup, median/SLA hoặc nguyên nhân khác biệt RAM từ bảng. Chưa đo CPU/disk I/O/
peak temp đầy đủ và chưa chạy AI cùng renderer.

## Cấu hình và nguồn

Windows 11/i7-13620H/RAM 16 GB; Remotion 4.0.545, React 19.3.1, Node 24.14.1,
browser local đã có. Concurrency 2, offthread video thread 1, cache 64 MiB, x264
ultrafast, hardware encoding disabled. Không cài thêm dependency/model hoặc gọi cloud.

TPL01 dùng SVG/caption tự tạo; TPL02 dùng **hai artwork SVG**/card/progress.
TPL03 lặp test pattern **360×640, 30FPS, 15s**, crop/upscale ra preset; chưa thử
input gốc 1080p60 hoặc video 5 phút độc lập/VFR. Audio WAV mono 48 kHz tự tạo,
click mỗi 5s và tone 299.9–300s. Clock/progress chạy theo composition 300s.
Không dùng media cá nhân; highlight minh họa không phải AI alignment.

Lượt TPL03 dọc dùng harness trước khi mở rộng TPL01/02. Nguồn của lượt đó đã được
archive đúng hash; bốn lượt mới dùng cùng bản harness mở rộng. Không ghi đè output
cũ. Collector kiểm lại toàn bộ source snapshots và output hashes.

## Kiểm tra thực tế

- **18.000 frames/file; tổng 90.000**, full video/audio decode thành công;
  **0 lỗi** timestamp so `index/60`, tolerance 1µs.
- Mỗi file đủ **60 flash/click** tại 0/5/.../295s và tail tone 299.9s;
  max measured AV delta khoảng **0.0417ms**, trong ngưỡng 100ms.
- Bốn audio windows 0–0.02s, 150–150.02s, 295–295.02s, 299.95–300s đạt
  correlation ≥0.98, final/raw RMS ratio 0.9–1.1 và tail RMS >0.005.
- Tại **50ms cuối**, reference/final correlation **0.999867**, final/raw RMS ratio
  **0.997497** ở cả năm file; không phát hiện mất tín hiệu trong cửa sổ này.
- Finalizer copy H.264 packet payload, encode lại AAC; payload hash khớp raw từng
  file. Collector kiểm **10 full output hashes** và source snapshots của năm lượt.

Marker là tín hiệu tổng hợp ở mốc biết trước, không phải timing lời hát hoặc
độ chính xác cảm nhận 0.0417ms. AAC decoded padding ngoài stream duration được
ghi riêng; xem [lượt đầu](RENDER_STRESS_RESULTS.md). Encode AAC lần nữa vẫn cần
nghe A/B, chưa là production default hoặc chất lượng audio đã nghiệm thu.

Đã xem PNG preflight giây 150 của TPL01/02, PNG giây 299.9 của TPL02/TPL03
ngang/vuông: text Việt, artworks/card/highlight/clock/progress có mặt ở những ảnh
được xem. Chưa audit mọi frame hoặc xem/nghe trọn năm video.

## Gate và phần còn thiếu

| Gate | Đã có | Chưa xác minh |
|---|---|---|
| R0 | 5/5 job riêng lẻ trong RAM gates | Concurrent AI/editor và media rộng hơn |
| R1 | 36 bounded smoke và 5 stress đạt output checks trong scope | Codecs/VFR/PNG alpha và template/timeline semantics đầy đủ |
| R2 | Marker AV, một số ảnh tĩnh | Interactive preview/export ≥20 mốc/project, trim/rate/transition/z-order |
| R3 | 5/5 render RTF ≤10 | Preview ≥24FPS, UI P95 ≤200ms, finalist repetitions |
| R4/R5 | Không kết luận từ batch | Cancel/retry/cleanup, snapshot bất biến, undo/reuse |
| R6 | Asset/binary local | Network isolation/offline audit |

Đạt phần sàng lọc **render time của R3** và **tài nguyên sampled của R0** cho các
fixture này; chưa đóng toàn bộ gates hoặc đánh FR/E2E Verified. Tiếp theo là
fidelity/lifecycle harness, rồi storage/recovery theo plan. Lyrics quality/word
timing gold là nhánh độc lập; không được render stress giải quyết. Giữ A–G và phạm
vi PoC, chưa triển khai application chính thức.

## Bản xem và bằng chứng

Bản xem nhẹ là **20s từ source time 145–165s**, rộng 540 pixels, 30FPS; mỗi bản
đã decode đủ 600 frames và audio. Chúng được tạo **sau** batch, không dùng để chấm
benchmark 300s/1080p60:

| Mẫu | Bản xem 20s |
|---|---|
| TPL01 dọc | [MP4](../../.poc/evidence/poc-04/tpl01-9-16-300s-1080p60/preview-20s-540p30.mp4) |
| TPL02 dọc | [MP4](../../.poc/evidence/poc-04/tpl02-9-16-300s-1080p60/preview-20s-540p30.mp4) |
| TPL03 dọc | [MP4](../../.poc/evidence/poc-04/tpl03-9-16-300s-1080p60/preview-20s-540p30.mp4) |
| TPL03 ngang | [MP4](../../.poc/evidence/poc-04/tpl03-16-9-300s-1080p60/preview-20s-540p30.mp4) |
| TPL03 vuông | [MP4](../../.poc/evidence/poc-04/tpl03-1-1-300s-1080p60/preview-20s-540p30.mp4) |

Raw evidence Git-ignored dưới `.poc/evidence/poc-04/`:
[suite summary](../../.poc/evidence/poc-04/stress-suite-results.json),
[batch manifest](../../.poc/evidence/poc-04/remaining-stress-batch.json).
Mỗi case giữ config, source snapshot, raw/bounded MP4, ffprobe, resources,
validation và hashes. [Runbook](../../poc/render/STRESS_RENDER.md),
[batch runner](../../poc/render/run_remaining_stress.py),
[collector](../../poc/render/collect_stress_results.py).

Thay đổi trên `dev`, chưa commit/push sau checkpoint `c3affcc`. Preview Việt đã
duyệt và baseline requirements giữ nguyên. Commit đề xuất:
`test(render): validate the complete five-case 300s stress suite`.
