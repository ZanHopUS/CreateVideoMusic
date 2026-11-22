# Preview and Render Fidelity Results

Ngày: **23/11/2026 (Asia/Saigon)**. POC-03/04 local trên máy Windows 11/RAM 16 GB.
Đã dùng **Remotion Player thật**, cùng component và snapshot với renderer; chưa
triển khai editor hoặc chọn các workaround làm mặc định sản phẩm.

## Phương pháp

Ba project TPL01/02/03, mỗi project **12 items**, bốn nhóm background/music/lyrics/
caption, 12s, 1280×720, 30FPS. Có PNG alpha, layer chồng nhau, fade/translation,
caption/lyrics dấu Việt, source offset, itemStart khác 0 và rate 0.8/1.25.
TPL03 có CFR và VFR tự tạo; source VFR thực tế có PTS delta 33.3/66.7/100ms.

Player được mount trong Chromium local, điều khiển pause/seek qua PlayerRef.
Mỗi probe chờ frame state, media seek/readiness, images, fonts và animation frames,
rồi capture viewport bằng CDP. Renderer xuất PNG cùng frame và MP4 thực; decode
toàn bộ MP4, đối chiếu với Player tại **27 mốc/project**, gồm trước/sau boundaries.
Component dùng chung không được coi là tự chứng minh fidelity.

Oracle Python độc lập đọc snapshot: tính active item IDs, source time
`sourceStart/fps + (frame-itemStart)/fps*speed` và audio events từ WAV đã biết mốc.
Ngưỡng sàng lọc đặt trước: **PSNR ≥30dB**, source/AV deviation ≤100ms, video duration
≤1 frame. PSNR là heuristic kỹ thuật, không phải nghiệm thu hình ảnh bằng mắt.

## Kết quả baseline đầy đủ

`full-02`: **81 cặp frame** (27×3), sau khi sửa adapter source offset.

| Project | Frame checks | Min Player/PNG PSNR | Min Player/MP4 PSNR | Max AV delta |
|---|---:|---:|---:|---:|
| TPL01 | 27/27 đạt | 69.56dB | 37.04dB | 46.17ms |
| TPL02 | 27/27 đạt | 69.83dB | 36.39dB | 15.96ms |
| TPL03 direct VFR | **24/27 đạt** | **12.47dB** | **12.48dB** | 0.0417ms |

Cả ba MP4 decode đủ 360 frames/file, không lỗi timestamp; video/audio/container
12.000s. Active item sets, source-time oracle, export audio và flash/click checks
đạt. Audio offsets riêng sau rate transform vẫn trong tolerance 100ms.

**Baseline R2 còn No-Go cho direct VFR:** frames **210/240/300** (timeline 7/8/10s)
lệch hình rõ dù DOM currentTime gần đúng 4.0/4.8/6.4s. Browser trả về các giá trị
3.999999/4.799999/6.399999; dữ liệu gợi ý lỗi chọn frame tại ranh giới seek/rounding,
chưa quy nguyên nhân cho một bug upstream cụ thể. Metadata thời gian đúng chưa đủ.

## Thử nghiệm khắc phục tách biệt

- Adapter ban đầu chia source offset cho rate: sai 2.0→1.6s và 3.2→4.0s.
  Đã sửa `trimBefore` dùng source offset trực tiếp, giữ baseline lỗi `smoke-03`.
- **CFR proxy đơn thuần chưa giải quyết**: `proxy-smoke-01` vẫn fail frame 210,
  PSNR 16.91dB. Không đề xuất proxy như giải pháp đã chứng minh.
- Nhánh **`--seek-nudge`**, default off: chỉ video items thêm **0.0003 frame =10µs**
  tại timebase 30FPS vào adapter. `sourceStart` gốc và oracle không đổi.
  `nudge-full-01` giữ direct VFR và đạt **27/27 mốc + MP4**, min PNG PSNR **37.72dB**,
  min MP4 PSNR **31.79dB**; source/AV checks và decode 360 frames đều đạt.

Đây là candidate cho fixture này, không là bảo đảm mọi codec/FPS/browser. Chưa thử
source sát EOF, timebase khác, media độc lập hoặc nhiều máy. Không nâng baseline
thành 81/81 single-run pass: 54 mốc TPL01/02 baseline và 27 mốc TPL03 candidate
thuộc **hai lượt cấu hình riêng**. Không tự chốt nudge thành kiến trúc Accepted.

## Hiệu năng quan sát

100 programmatic seeks/project sau warm-up: P95 TPL01 **49.61ms**, TPL02 **49.70ms**,
TPL03 **66.41ms**. Đây là API seek→DOM/media readiness, không phải UI drag/trim P95.
Simple Player chạy 60.0059s, có 1.800 `frameupdate` events ≈**29.997 events/s**;
không đồng nghĩa số frame thực sự được compositor/display trình bày.

Full baseline wall **151.531s**, sampled peak private **1.186 GiB**, min system
available **5.634 GiB**. Candidate TPL03 wall **32.281s**, private **0.938 GiB**,
min available **5.543 GiB**. Không abort. Candidate không lặp performance block;
chưa có cold/warm median hoặc nghiệm thu R3 của UI sản phẩm.

## Audio EOF regression

`full-01` dừng đúng khi strict finalizer thấy audio **11.989s** trong video 12s ở
rate 1.25, thay vì báo thành công. PoC finalizer thêm `apad=whole_dur` trước trim:
case này thành video/audio/container **12.000s**. Pad chỉ thêm silence khi thiếu,
không khôi phục nội dung đã mất hoặc chứng minh chất lượng audio.

Regression riêng trên raw stress 300s giữ video packet hash, duration 300.000s;
last 50ms so bản bounded cũ có correlation **1.0**, RMS ratio **1.0**, RMS **0.037464**.
Không ghi đè bằng chứng stress cũ. Nghe A/B và một-pass AAC từ lossless còn cần thử.

## Bằng chứng và kết luận

Raw dưới `.poc/evidence/poc-03/fidelity/`, Git-ignored:
[summary](../../.poc/evidence/poc-03/fidelity/summary.json),
[baseline validation](../../.poc/evidence/poc-03/fidelity/full-02/validation-with-av.json),
[candidate validation](../../.poc/evidence/poc-03/fidelity/nudge-full-01/validation.json),
[proxy negative](../../.poc/evidence/poc-03/fidelity/proxy-smoke-01/validation.json),
[audio regression](../../.poc/evidence/poc-03/fidelity/audio-pad-regression/validation.json).
Source snapshots/hash và manifest assets đã xác minh; setup/CDP failures `smoke-01/02`
giữ logs, không tính là quality evidence. [Runbook](../../poc/render/fidelity/README.md).

R2 có evidence tốt cho các fixture/candidate nêu trên nhưng chưa đóng trên corpus
rộng. R3 UI, R6 network isolation, real listening và full editor E2E còn mở.
Không sửa PRD/SRS/RTM, A–G hoặc stack đã xác nhận.
