# First 300s Render Stress Results

Ngày: **22/11/2026 (Asia/Saigon)**. POC-04, fixture TPL03-style video nền,
**300s, 1080×1920, 60FPS** trên Windows 11/i7-13620H/RAM 16 GB.
Đây là **1/5 output stress dự kiến**, chưa nghiệm thu editor hoặc chọn stack.

**Cập nhật 23/11/2026:** đã chạy và kiểm xong cả bốn mẫu còn lại; xem
[RENDER_STRESS_SUITE_RESULTS.md](RENDER_STRESS_SUITE_RESULTS.md). Số liệu bên dưới
giữ nguyên cho lượt TPL03 dọc đầu tiên.

## Kết luận

Lượt này **đạt ngưỡng render/tài nguyên và các phép đo tín hiệu đã đặt**:
decode đủ 18.000 frames, không lỗi timestamp, duration final 300.000s,
không mất tín hiệu trong cửa sổ 50ms cuối. Render RTF **3.477**, thấp hơn ngưỡng
sàng lọc ≤10, không bị RAM monitor dừng. Có thể tiếp tục mở rộng PoC.

Chưa đóng toàn bộ R3: chưa đo preview FPS, UI latency hoặc editor khi render.
Không đánh FR/E2E Verified; đây là single-run generated-media harness.

## Cấu hình và dữ liệu

- Remotion 4.0.545/React 19.3.1/Node 24.14.1, browser local đã chuẩn bị.
- H.264/AAC, x264 ultrafast, hardware encoding disabled, concurrency 2,
  một offthread video thread, cache 64 MiB. Không chạy AI cùng job.
- Video test pattern tự tạo **360×640, 30FPS, 15s** được lặp và upscale trong
  composition 300s/1080p60; chưa thử decode input gốc 1080p60, media độc lập
  5 phút hoặc VFR input.
- Audio WAV mono 48 kHz tự tạo, click mỗi 5 giây từ 0 đến 295s và tone
  299.9–300s. Text Việt/highlight/progress là minh họa, không phải AI alignment.
- Giữ cả `raw.mp4` và `bounded.mp4`. Bản bounded dùng
  [audio finalizer thử nghiệm](AUDIO_DURATION_RESULTS.md); hash packet payload
  video không thay đổi. Không sửa matrix gốc hoặc preview Việt đã duyệt.

## Hiệu năng và tài nguyên

| Chỉ số | Kết quả một lượt |
|---|---:|
| RenderMedia | **1.043,061s ≈17 phút 23 giây** |
| Render RTF | **3.477** |
| Audio finalize, gồm kiểm video payload/duration | **3.196s** |
| Supervisor wall gồm setup/stills/probe/finalize | **1.064,250s ≈17 phút 44 giây** |
| Peak process-tree private sampled | **2.111 GiB** |
| Peak process-tree RSS sum | **2.805 GiB** |
| Min system available | **3.844 GiB** |
| Resource samples / dưới 2 GiB | **1.053 / 0** |
| Abort/OOM | Không ghi nhận |
| Raw / bounded bytes | 582.444.961 / 570.724.728 |

RSS sum có thể đếm chung shared pages; private bytes không đồng nghĩa RAM vật lý
của riêng model/browser. Sampling xấp xỉ một giây có thể bỏ sót peak ngắn.
Chưa kiểm soát power/background load hoặc lặp cold/warm; không là SLA hoặc
bằng chứng tăng tốc so lượt 15s khác fixture. Chưa đo peak temp/disk I/O đầy đủ.

## Validation

| Phép đo | Kết quả |
|---|---|
| Full video decode | **18.000/18.000 frames** |
| CFR timestamps so `index/60`, tolerance 1µs | **0 lỗi** |
| Final codec/dimensions/FPS | H.264/AAC, 1080×1920, 60FPS đúng |
| Raw video / AAC/container duration | 300.000s / 300.011s |
| Bounded video / AAC / container duration | **300.000s / 300.000s / 300.000s** |
| Flash và click | 60 flash, 60 click đúng mốc; thêm tail tone 299.9s |
| Max measured click–flash delta | Khoảng **0.0417ms** |
| Four audio windows | Tất cả correlation ≥0.98, RMS ratio final/raw 0.9–1.1 |
| Last 50ms reference/final correlation | **0.999867** |
| Last 50ms raw/final correlation | **0.999997** |
| Last 50ms final/raw RMS ratio | **0.997497** |
| Last 50ms final RMS | **0.037464**, vượt ngưỡng >0.005 |

Các cửa sổ là 0–0.02s, 150–150.02s, 295–295.02s, 299.95–300s. Tín hiệu cuối
được kiểm đến sample boundary giây 300; không chỉ dựa metadata duration.
Marker result không là độ chính xác lời hát hoặc ngưỡng cảm nhận của con người.
AAC decoded samples có thể còn codec padding ngoài stream duration; validator
ghi decoded end **300.010667s** ở cả raw/bounded, trong khi final stream/container
duration là 300.000s. Không tự coi phần decoded padding là drift hoặc cắt mất nội dung.

Validation hoàn tất trong khoảng **27.047s**. Đã xem PNG giây 299.9: text dấu Việt,
highlight, đồng hồ 299.90/300.00 và progress hiển thị ở ảnh đó. Chưa nghe đánh giá
chất lượng audio lossy hoặc xem/nghe đầu–giữa–cuối toàn bộ file. Chưa so sánh
interactive Player với export tại 20 mốc/project.

## Phần còn lại và quyết định

1. Chạy bốn stress outputs còn lại: TPL01/02 dọc, TPL03 ngang/vuông, rồi repetitions
   cho finalist. Không suy kết quả một fixture sang tất cả templates/presets.
2. Bổ sung fidelity fixtures hai ảnh, source offset/trim/rate, transition/z-order,
   VFR; thử lifecycle/cancel/retry và resource contention khi edit/render.
3. Đánh giá audio bằng nghe; thử chỉ encode AAC một lần từ nguồn lossless trước
   khi đề xuất pipeline sản phẩm. Workaround hiện tại vẫn là candidate PoC.

Không cần thay A–G hoặc yêu cầu GPU từ kết quả này. Chưa đủ bằng chứng để phê
duyệt kiến trúc sản phẩm, đóng toàn bộ R0–R6 hay coi Core đã hoàn thành.

## Artifacts và trạng thái Git

Raw evidence được Git-ignore tại `.poc/evidence/poc-04/tpl03-9-16-300s-1080p60/`:
[summary](../../.poc/evidence/poc-04/tpl03-9-16-300s-1080p60/summary.json),
[render result](../../.poc/evidence/poc-04/tpl03-9-16-300s-1080p60/render-result.json),
[validation](../../.poc/evidence/poc-04/tpl03-9-16-300s-1080p60/validation.json),
[resources](../../.poc/evidence/poc-04/tpl03-9-16-300s-1080p60/resources/resources.json),
[bounded MP4](../../.poc/evidence/poc-04/tpl03-9-16-300s-1080p60/bounded.mp4).
Nguồn, cấu hình và output hashes nằm trong raw JSON. Tái lập:
[STRESS_RENDER.md](../../poc/render/STRESS_RENDER.md).

Checkpoint `c3affcc` đã push `dev` theo yêu cầu user. Harness/báo cáo audio duration
và stress tạo sau checkpoint chưa commit/push. Commit đề xuất:
`test(render): bound AAC duration and validate 300-second stress output`.
