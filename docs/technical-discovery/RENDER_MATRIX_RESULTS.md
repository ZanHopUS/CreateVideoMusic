# Render Preset Matrix Results

Ngày: **22/11/2026 (Asia/Saigon)**. POC-03 trên Windows 11, i7-13620H, RAM 16 GB.
Chỉ là harness local; chưa triển khai editor hoặc chốt kiến trúc sản phẩm.

## 1. Kết luận

**36/36 MP4 đạt kiểm tra preset video, decode và marker AV tổng hợp**. Tổng cộng
**24.300 video frames**, không phát hiện lỗi timestamp CFR. Không OOM hoặc chạm
ngưỡng dừng tài nguyên. Có thể tiếp tục PoC stress, nhưng **chưa đóng R1/R2/R3**
hoặc đánh FR-408/E2E-30 Verified.

Điểm cần xử lý trước kết luận duration đầy đủ: video đúng **15.000s**, nhưng audio
và container **15.019s**. Phần chênh 19ms nhỏ hơn một frame ở 30FPS nhưng lớn hơn
một frame ở 60FPS; không được gộp vào tuyên bố mọi duration đều đạt ≤1 frame.
Chưa xác minh nguyên nhân phần đuôi hoặc ảnh hưởng khi phát/nối nhiều clip.

## 2. Cấu hình và dữ liệu

- Remotion **4.0.545**, React **19.3.1**, Node **24.14.1**; local Chrome Headless
  đã chuẩn bị từ POC-00. Dependencies giữ nguyên, không cài thêm cho matrix.
- H.264/AAC, 4:2:0, x264 `ultrafast`, hardware encoding disabled;
  concurrency **2**, offthread video threads **1**, cache **64 MiB**.
  Không cần GPU rời trên máy thử; chưa đo đường GPU/software của Chromium.
- Ba fixture tự tạo, mỗi output **15s**: TPL01 ảnh/text, TPL02 một artwork/card/progress,
  TPL03 video test pattern/highlight minh họa. Click và flash cùng mốc **0/5/10s**.
  Không dùng bài hát cá nhân hoặc lời ASR để chấm matrix.
- Mỗi fixture chạy đủ sáu kích thước bên dưới × **30/60FPS**, tổng **36 output**.

| Ratio | Preset thấp | Preset cao |
|---|---|---|
| 9:16 | 720×1280 | 1080×1920 |
| 16:9 | 1280×720 | 1920×1080 |
| 1:1 | 720×720 | 1080×1080 |

Source fingerprint và file hashes được lưu riêng. Inventory được ghi trong lúc chạy
và kiểm lại sau render; không thay assets. Không có resume trong lượt đo này.
Đây là một lượt mỗi case, chưa phải cold/warm repetitions hoặc cấu hình finalist.

## 3. Kiểm tra output

| Phép đo | Kết quả |
|---|---|
| ffprobe dimensions/H.264/AAC/FPS/video duration/frame count | 36/36 đúng |
| Decode toàn video và audio bằng PyAV | 36/36 hoàn tất |
| Frame count | 450 ở 30FPS; 900 ở 60FPS; tổng 24.300 |
| Timestamp từng frame so với `index/FPS` | 0 lỗi, dung sai 1 microsecond |
| Audio | AAC stereo, 48 kHz, có đủ ba click |
| Flash ở 0/5/10s | Đúng mốc ở 36/36 file |
| Max click–flash delta | Khoảng 0.0417ms theo sample/timestamp detector |
| Video duration | 15.000s ở mọi output |
| Audio/container duration | 15.019s ở mọi output |
| Container duration lệch ≤1 frame | 18/36; 18 bản 60FPS vượt ngưỡng này |

Marker delta chỉ đo tín hiệu tổng hợp tại ba mốc, không phải timing lời hát hoặc
độ chính xác cảm nhận 0.0417ms. Không suy ra drift dài hạn hay interactive preview fidelity.
Validator ghi riêng cờ duration container; exit code thành công chỉ bao gồm các
assertion video/preset/decode/markers, **không nghĩa container duration 60FPS đạt**.

Đã xem PNG giây 5 của TPL01 dọc 1080p30, TPL02 ngang 720p30 và TPL03 vuông 1080p30:
chữ Việt hiển thị, card/progress/highlight có mặt ở ảnh được xem. Chưa xem/nghe
đầu–giữa–cuối cả 36 video hoặc audit fonts/layout toàn bộ.

## 4. Hiệu năng và tài nguyên

| Fixture | Cases | RenderMedia nhanh nhất–chậm nhất | RTF range |
|---|---:|---:|---:|
| TPL01 | 12 | 12.95–39.41s | 0.863–2.628 |
| TPL02 | 12 | 13.55–38.65s | 0.903–2.577 |
| TPL03 | 12 | 19.37–52.49s | 1.291–3.499 |

Các range so các preset khác nhau, không phải độ biến thiên lặp cùng cấu hình.
Không dùng để tính speedup so smoke concurrency 1 trước đó hoặc dự báo tuyến tính 300s.

- Tổng supervisor wall **1.038,906s ≈17 phút 19 giây**, gồm bundle/still/probe/setup;
  tổng các lần `renderMedia` **994,458s**.
- Process-tree peak private sampled **1.143 GiB**; peak RSS sum **1.813 GiB**.
  RSS sum có thể đếm chung shared pages, không đồng nghĩa RAM vật lý duy nhất.
- Min system available **4.793 GiB**, **0** mẫu dưới 2 GiB, **1.029** resource samples;
  monitor xấp xỉ mỗi giây, có thể bỏ sót peak ngắn. Không chạy ASR cùng renderer.
- MP4 tổng **217.833.359 bytes ≈207.74 MiB**. Chưa đo peak temp/disk I/O/CPU đầy đủ.

## 5. Gate và bước tiếp

| Gate | Trạng thái trong lượt này |
|---|---|
| R0 | Đạt ngưỡng sampling cho workload render tuần tự này; chưa nghiệm thu concurrent AI/editor |
| R1 | Video preset/decode/markers đạt 36/36; duration container 60FPS và fixtures đầy đủ còn mở |
| R2 | Chưa đủ: chưa đối chiếu interactive preview/render 20 mốc/project |
| R3 | Chưa thử 300s/1080p60, preview FPS hoặc UI latency |
| R4/R5 | Chưa thử lifecycle ứng dụng, cancel/retry, immutable snapshot, undo/reuse |
| R6 | Assets local; chưa kiểm network isolation, chưa công bố offline gate đạt |

Tiếp theo: kiểm duration/audio tail bằng fixture riêng trước mở stress dài;
bổ sung trim/source offset/rate, hai ảnh, z-order/transition và VFR cho fidelity.
Sau đó chạy stress 300s/1080p60 theo POC_PLAN, giữ giám sát RAM và timebox.
Không thay đổi A–G, bỏ preset 60FPS hay tự nâng yêu cầu phần cứng.

## 6. Bằng chứng và Git

Raw files nằm trong `.poc/evidence/poc-03/preset-matrix/`, được Git-ignore:
[summary](../../.poc/evidence/poc-03/preset-matrix/summary.json),
[render results](../../.poc/evidence/poc-03/preset-matrix/render-results.json),
[validation](../../.poc/evidence/poc-03/preset-matrix/validation.json),
[resources](../../.poc/evidence/poc-03/preset-matrix/resources/resources.json),
[input inventory](../../.poc/evidence/poc-03/preset-matrix/input-inventory.json),
[output hashes](../../.poc/evidence/poc-03/preset-matrix/output-inventory.json).
Lệnh chạy và resume: [RENDER_MATRIX.md](../../poc/render/RENDER_MATRIX.md).

Preview Việt đã được user duyệt vẫn khớp SHA-256 cũ; smoke ban đầu được giữ riêng.
Thay đổi trên `dev`, chưa commit/push. Commit đề xuất:
`test(render): validate 36 local MP4 presets and document duration limits`.
