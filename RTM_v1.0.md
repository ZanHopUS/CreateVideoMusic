# Requirement Traceability Matrix (RTM) v1.0

**Baseline:** 22/11/2026. **Cập nhật triển khai:** 23/11/2026, S0/S1 đã bắt đầu sau PO duyệt ADR/contracts.
Mỗi FR liên kết tới test/AC trong SRS. Các phần chưa làm giữ **Not implemented**; Partial chỉ có evidence cho slice được ghi, không phải Verified. C/M/L/P: xem SRS.

| Requirement ID | Yêu cầu rút gọn | Scope | Acceptance/Test | Implementation | Verification |
|---|---|---|---|---|---|
| FR-101 | Xem/chọn ba nhóm template TPL-01/02/03; workflow template-first | C | AC-01 / E2E-01 | Partial — TPL-01 UI; TPL-02/03 pending | Slice tested; full AC pending |
| FR-102 | Tạo project từ template và mở editor bản nháp | C | AC-01 / E2E-01 | Partial — TPL-01 editable draft | Slice tested; full AC pending |
| FR-103 | Nhập nhiều ảnh/video, sắp xếp thứ tự và thời lượng | C | AC-02 / E2E-02 | Partial — TPL-01 nhiều ảnh/video, import/reorder/trim | S2 slice tested; full AC pending |
| FR-104 | Caption thủ công, chỉnh sửa và gợi ý AI nếu cấu hình | C | AC-03 / IT-03 | Partial — Caption nhập tay; AI pending | Slice tested; full AC pending |
| FR-105 | Thư viện nhạc cá nhân, chọn thủ công hoặc gợi ý từ nội dung có sẵn | C(P gợi ý) | AC-04 / IT-04 | Not implemented | Not run |
| FR-106 | Video draft giữ layer chỉnh sửa, không chỉ xuất video phẳng | C | AC-05 / E2E-01 | Partial — TPL-01 layers giữ khi save/open | Slice tested; full AC pending |
| FR-107 | Template từ project, đánh dấu placeholder và tái sử dụng | C | AC-06 / IT-06 | Not implemented | Not run |
| FR-108 | Template từ trang trống, thêm layer/placeholder, save/open/reuse | M | AC-07 / E2E-07 | Not implemented | Not run |
| FR-109 | Cho phép đổi bố cục/font/hiệu ứng template không sửa template gốc | C | AC-06 / IT-06 | Not implemented | Not run |
| FR-201 | Nhận dạng tiếng Việt/Anh từ audio bằng pipeline thật (giới hạn chất lượng theo PoC) | C(P) | AC-08 / AI-01 | Not implemented | Not run |
| FR-202 | Duyệt, chỉnh lời và mốc thời gian trước khi dùng | C | AC-09 / IT-09 | Not implemented | Not run |
| FR-203 | Nhập tay và import LRC/SRT có báo lỗi định dạng | C | AC-10 / UT-10 | Not implemented | Not run |
| FR-204 | Căn lyrics theo câu; ưu tiên theo từ nếu tin cậy; fallback câu | C(P) | AC-11 / AI-02 | Not implemented | Not run |
| FR-205 | Nhận đầu vào rap/remix/sped-up/slowed/multiple voices/instrumental; báo giới hạn, không bịa lyrics | C(P) | AC-12 / AI-03 | Not implemented | Not run |
| FR-206 | Đề xuất nhiều đoạn nhạc và nghe thử; luôn cho trim thủ công | C(P) | AC-13 / IT-13 | Not implemented | Not run |
| FR-207 | Text/lyrics nhiều font dấu Việt, màu, viền, shadow, position, animation | C cơ bản; M phong phú | AC-14 / IT-14 | Partial — Caption size/color; lyric styles pending | Slice tested; full AC pending |
| FR-208 | Gợi ý style lyrics theo mood/template và cho user override | M(P) | AC-15 / IT-15 | Not implemented | Not run |
| FR-301 | Editor multi-track media, audio, lyrics, caption/text; playhead và seek | C | AC-16 / E2E-16 | Partial — Nhiều image/video/music/text clips; lyrics pending | S2 slice tested; full AC pending |
| FR-302 | Kéo thả/trim/đổi duration; undo/redo; lưu trạng thái | C | AC-17 / IT-17 | Partial — Per-clip trim/reorder/remove/Undo/Redo | S2 slice tested; full AC pending |
| FR-303 | Split, duplicate, snapping, lock/hide track | M | AC-18 / IT-18 | Not implemented | Not run |
| FR-304 | Crop/fit/blur, brightness cơ bản; zoom/pan/rotate/filter nâng cao | C/M | AC-19 / IT-19 | Partial — Cover/contain; crop/blur/brightness pending | S2 fit/persistence tested; full AC pending |
| FR-305 | Hiệu ứng fade/slide/scale trong Core; presets mở rộng ở M | C/M | AC-20 / IT-20 | Not implemented | Not run |
| FR-306 | Music Card: cover, song/artist, progress; chỉnh layout/color nâng cao | C/M | AC-21 / E2E-21 | Partial — TPL-02 two-image card, editable song/artist, progress preview/render | Functional MP4 test passed at test-only 3 GiB; production 4 GiB admission and full AC pending |
| FR-307 | Preview và export dùng một timeline canonical, thống nhất z-order và timing | C | AC-22 / IT-22 | Partial — Shared TPL-01 image/video scene; full fidelity pending | Sparse CFR source/order checks; full AC pending |
| FR-401 | Tạo/đổi tên/mở/xóa project, chọn folder lưu, lưu thủ công | C | AC-23 / E2E-23 | Partial — Create/rename/save/open; delete UI pending | Slice tested; full AC pending |
| FR-402 | Khôi phục timeline, lyrics, effects, template và references khi mở lại | C | AC-24 / E2E-24 | Partial — TPL-01 content/playhead; full state pending | Slice tested; full AC pending |
| FR-403 | Báo dirty-state, cảnh báo rời project khi chưa lưu | C | AC-25 / IT-25 | Partial — Dirty hash/warnings; full acceptance pending | Slice tested; full AC pending |
| FR-404 | Recovery snapshot riêng, hỏi trước khi restore; không ghi đè manual save | C | AC-26 / IT-26 | Not implemented | Not run |
| FR-405 | Thư viện media tái sử dụng, metadata/thumbnail/search, không xóa asset dùng chung | C | AC-27 / IT-27 | Partial — Managed import/catalog; search/thumbnail UI pending | Slice tested; full AC pending |
| FR-406 | Chọn thư mục project và thư mục export; xử lý missing media/relink | C | AC-28 / IT-28 | Partial — Folder grants/native picker; relink pending | Slice tested; full AC pending |
| FR-407 | Drive desktop sync qua **snapshot/project package nhất quán**, không live DB | C (workflow hỗ trợ) | AC-29 / IT-29 | Not implemented | Not run |
| FR-408 | MP4 H.264/AAC, presets 720/1080p, 30/60fps, 9:16/16:9/1:1 | C | AC-30 / E2E-30 | Partial — 720p30 dọc, MP4 2s; other presets pending | Slice tested; full AC pending |
| FR-409 | Render worker, progress, cancel, retry, output preview/download/open-folder | C | AC-31 / E2E-31 | Partial — Queue/render/cancel/retry subset | Slice tested; full AC pending |
| FR-410 | Quản lý temp, xử lý thiếu dung lượng, xác minh metadata output | C | AC-32 / IT-32 | Partial — Basic disk check/validate; quota/temp cleanup pending | Slice tested; full AC pending |
| FR-501 | API abstraction local/Gemini/OpenAI; provider optional có thể disable | C (interface); M (nhiều adapter) | AC-33 / IT-33 | Not implemented | Not run |
| FR-502 | Không làm gián đoạn edit/render nếu cloud AI thất bại/offline | C | AC-34 / IT-34 | Not implemented | Not run |
| FR-503 | Không gửi media/caption lên cloud khi chưa có đồng ý rõ | C | AC-35 / SEC-35 | Partial — Cloud disabled; consent/provider integration pending | Slice tested; full AC pending |
| FR-504 | Build/deploy frontend Vercel, đánh giá Local Agent/cloud worker | L | AC-36 / ARCH-36 | Not implemented | Not run |

## Non-functional traceability
| NFR | Phương pháp xác minh | Trạng thái |
|---|---|---|
| NFR-01/02 | PERF-CPU, PERF-300s, đo peak RAM, CPU | Not run |
| NFR-03 | FFprobe output matrix, playback | Not run |
| NFR-04/05 | PERF-preview, UI latency percentile | Not run |
| NFR-06/07 | Sync reference timestamps, WER/CER/word timing | Not run |
| NFR-08/09 | Integration cancel/progress/recovery/atomic save | Not run |
| NFR-10/11 | Offline tests, permission and secret audit | Not run |
| NFR-12/13/14 | Vietnamese font audit, zero mandatory paid dependencies, restore package | Not run |

## Quy định cập nhật
Khi tạo issue, thêm cột/metadata: Issue ID, owner, commit/PR, test result, evidence path, implementation status, review date. Không đánh dấu Verified khi chỉ có unit test giả lập; E2E phải sử dụng media thực, output MP4 thực. Những yêu cầu ở M/L vẫn được trace dù chưa thuộc release Core.

## Application evidence — 23/11/2026

PO duyệt conditional S0 → S1; [ADR Accepted](docs/decisions/ADR-0001-LOCAL_MVP_ARCHITECTURE.md).
[Implementation status](docs/planning/MVP_IMPLEMENTATION_STATUS.md) ghi lệnh/results,
raw evidence và giới hạn. 11 Vitest + 11 pytest, browser E2E TPL-01 trên PNG/WAV
thật tự tạo, native folder cancel/Unicode và launcher smoke có evidence. Không có
FR nào được đánh Verified chỉ từ slice này; bảng NFR Not run là nghiệm thu đầy đủ
còn thiếu (các smoke/subchecks được ghi ở implementation status), không phủ nhận
PoC hoặc S0 measurements. Không đổi scope C/M/L/P, AC IDs hay quyết định A–G.
