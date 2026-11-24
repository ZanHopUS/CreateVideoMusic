# Requirement Traceability Matrix (RTM) v1.0

**Baseline:** 22/11/2026. **Cập nhật triển khai:** 24/11/2026, S2–S6 được giao triển khai; xem [kết quả](docs/planning/S2_S6_RESULTS.md). Chưa có nghiệm thu Core/release.
Mỗi FR liên kết tới test/AC trong SRS. Các phần chưa làm giữ **Not implemented**; Partial chỉ có evidence cho slice được ghi, không phải Verified. C/M/L/P: xem SRS.

| Requirement ID | Yêu cầu rút gọn | Scope | Acceptance/Test | Implementation | Verification |
|---|---|---|---|---|---|
| FR-101 | Xem/chọn ba nhóm template TPL-01/02/03; workflow template-first | C | AC-01 / E2E-01 | Partial — Ba mẫu chọn được; TPL-03 lyrics workflow mới | Browser draft/review tested; full three-template MP4 pending |
| FR-102 | Tạo project từ template và mở editor bản nháp | C | AC-01 / E2E-01 | Partial — Editable draft TPL-01/02/03 | Browser tested; full AC pending |
| FR-103 | Nhập nhiều ảnh/video, sắp xếp thứ tự và thời lượng | C | AC-02 / E2E-02 | Partial — TPL-01 nhiều ảnh/video, import/reorder/trim | S2 slice tested; full AC pending |
| FR-104 | Caption thủ công, chỉnh sửa và gợi ý AI nếu cấu hình | C | AC-03 / IT-03 | Partial — Caption tay; cloud adapters disabled | Manual/offline boundary tested; configured suggestions pending |
| FR-105 | Thư viện nhạc cá nhân, chọn thủ công hoặc gợi ý từ nội dung có sẵn | C(P gợi ý) | AC-04 / IT-04 | Partial — Library search/tags/reuse/listen; energy heuristics | Catalog/browser tested; useful corpus pending |
| FR-106 | Video draft giữ layer chỉnh sửa, không chỉ xuất video phẳng | C | AC-05 / E2E-01 | Partial — TPL-01 layers giữ khi save/open | Slice tested; full AC pending |
| FR-107 | Template từ project, đánh dấu placeholder và tái sử dụng | C | AC-06 / IT-06 | Partial — Typed slots/immutable template/new instance IDs | API/browser isolation tested; full AC pending |
| FR-108 | Template từ trang trống, thêm layer/placeholder, save/open/reuse | M | AC-07 / E2E-07 | Not implemented | Not run |
| FR-109 | Cho phép đổi bố cục/font/hiệu ứng template không sửa template gốc | C | AC-06 / IT-06 | Partial — Shared styles; personal template instances | Domain/browser tested; full effect/layout acceptance pending |
| FR-201 | Nhận dạng tiếng Việt/Anh từ audio bằng pipeline thật (giới hạn chất lượng theo PoC) | C(P) | AC-08 / AI-01 | Integrated — Faster-whisper worker offline + job/review | Missing-model/admission/cancel tested; real inference blocked RAM |
| FR-202 | Duyệt, chỉnh lời và mốc thời gian trước khi dùng | C | AC-09 / IT-09 | Partial — Edit/review/apply/draft save and reopen job results | Browser real UI; AI responses transport fixture; quality pending |
| FR-203 | Nhập tay và import LRC/SRT có báo lỗi định dạng | C | AC-10 / UT-10 | Implemented parser/UI — LRC/SRT and manual cues | Unit negative cases + browser workflow; full AC pending |
| FR-204 | Căn lyrics theo câu; ưu tiên theo từ nếu tin cậy; fallback câu | C(P) | AC-11 / AI-02 | Integrated — WhisperX cue-window alignment + sentence fallback | Time mapping tested; real model application run pending RAM |
| FR-205 | Nhận đầu vào rap/remix/sped-up/slowed/multiple voices/instrumental; báo giới hạn, không bịa lyrics | C(P) | AC-12 / AI-03 | Partial — Draft/no-clear-lyrics states; review mandatory | Genre/instrumental quality corpus not verified |
| FR-206 | Đề xuất nhiều đoạn nhạc và nghe thử; luôn cho trim thủ công | C(P) | AC-13 / IT-13 | Partial — Local energy segments/listen/explicit trim | Algorithm/UI code; 6-track usefulness review pending |
| FR-207 | Text/lyrics nhiều font dấu Việt, màu, viền, shadow, position, animation | C cơ bản; M phong phú | AC-14 / IT-14 | Partial — Font/color/stroke/shadow/position/animation + lyrics | Domain/browser styles tested; output/glyph matrix pending |
| FR-208 | Gợi ý style lyrics theo mood/template và cho user override | M(P) | AC-15 / IT-15 | Not implemented | Not run |
| FR-301 | Editor multi-track media, audio, lyrics, caption/text; playhead và seek | C | AC-16 / E2E-16 | Partial — Image/video/audio/text/lyrics tracks, seek/playhead/zoom | UI 12/100 clip measurements; full AC pending |
| FR-302 | Kéo thả/trim/đổi duration; undo/redo; lưu trạng thái | C | AC-17 / IT-17 | Partial — Per-clip trim/reorder/remove/Undo/Redo | S2 slice tested; full AC pending |
| FR-303 | Split, duplicate, snapping, lock/hide track | M | AC-18 / IT-18 | Not implemented | Not run |
| FR-304 | Crop/fit/blur, brightness cơ bản; zoom/pan/rotate/filter nâng cao | C/M | AC-19 / IT-19 | Partial — Fit/crop position/blur/brightness; advanced M pending | Schema/browser; real new output regression pending |
| FR-305 | Hiệu ứng fade/slide/scale trong Core; presets mở rộng ở M | C/M | AC-20 / IT-20 | Partial — Shared fade/slide/scale, audio fade | Typecheck/browser style; full output tests pending RAM |
| FR-306 | Music Card: cover, song/artist, progress; chỉnh layout/color nâng cao | C/M | AC-21 / E2E-21 | Partial — Role metadata/style/progress follows music clip | Historical MP4 evidence; changed scene production regression pending |
| FR-307 | Preview và export dùng một timeline canonical, thống nhất z-order và timing | C | AC-22 / IT-22 | Partial — Shared scene/source mapping for all templates | Trim/rate/lyrics domain tests; VFR/full fidelity pending |
| FR-401 | Tạo/đổi tên/mở/xóa project, chọn folder lưu, lưu thủ công | C | AC-23 / E2E-23 | Partial — Create/rename/open/save/delete UI + editor lease | API/browser + two-tab takeover tested; full AC pending |
| FR-402 | Khôi phục timeline, lyrics, effects, template và references khi mở lại | C | AC-24 / E2E-24 | Partial — Content plus playhead/selection/zoom/panels | Recovery/portable/browser + 300s immutable render/current dirty-state tested; full AC pending |
| FR-403 | Báo dirty-state, cảnh báo rời project khi chưa lưu | C | AC-25 / IT-25 | Partial — Dirty hash/warnings; full acceptance pending | Slice tested; full AC pending |
| FR-404 | Recovery snapshot riêng, hỏi trước khi restore; không ghi đè manual save | C | AC-26 / IT-26 | Partial — Independent recovery/30s loop/cap/confirmed restore | Revision/hash/cap + real child crash after publish; all phases pending |
| FR-405 | Thư viện media tái sử dụng, metadata/thumbnail/search, không xóa asset dùng chung | C | AC-27 / IT-27 | Partial — Search/tags/thumbnail/listen/reuse; shared bytes retained | API/browser; explicit source GC + working/manual/recovery/template/job/history pins tested; conservative legacy pins |
| FR-406 | Chọn thư mục project và thư mục export; xử lý missing media/relink | C | AC-28 / IT-28 | Partial — Native folder grants and same-SHA relink | Forged path rejected; 4 real native chooser cases passed (Unicode/cancel/media/package) |
| FR-407 | Drive desktop sync qua **snapshot/project package nhất quán**, không live DB | C (workflow hỗ trợ) | AC-29 / IT-29 | Partial — Direct Drive per ADR-0002; templates backup/restore added | 2 real cloud round-trips with generated media/templates + hash/manual-dirty preservation; cross-PC/quota pending |
| FR-408 | MP4 H.264/AAC, presets 720/1080p, 30/60fps, 9:16/16:9/1:1 | C | AC-30 / E2E-30 | Partial — 12 preset selector/worker/metadata validation | 36/36 real outputs independently decoded; full acceptance/listening pending |
| FR-409 | Render worker, progress, cancel, retry, output preview/download/open-folder | C | AC-31 / E2E-31 | Partial — Render/ASR/alignment/package jobs; cancel/retry/read outputs | Cancel/normal-root-exit/crash ownership + stage-copy/fsync faults tested; full phase fault matrix pending |
| FR-410 | Quản lý temp, xử lý thiếu dung lượng, xác minh metadata output | C | AC-32 / IT-32 | Partial — Disk estimate/validate/publish-last/temp preview + consent | Source GC pins/locked-file rollback, cache quotas, temp cleanup and publish faults tested; real full-disk audit pending |
| FR-501 | API abstraction local/Gemini/OpenAI; provider optional có thể disable | C (interface); M (nhiều adapter) | AC-33 / IT-33 | Partial — Provider protocol/local runtime/disabled cloud adapters | Disabled providers no-egress tested; local small/medium/align vi/en runtime passed on development samples |
| FR-502 | Không làm gián đoạn edit/render nếu cloud AI thất bại/offline | C | AC-34 / IT-34 | Partial — Missing-model/failed AI retains editable draft | Browser transport failure + API missing-model tested; full offline E2E pending |
| FR-503 | Không gửi media/caption lên cloud khi chưa có đồng ý rõ | C | AC-35 / SEC-35 | Partial — No cloud AI network implementation; disabled adapters | Explicit provider requests rejected without egress; broader security audit pending |
| FR-504 | Build/deploy frontend Vercel, đánh giá Local Agent/cloud worker | L | AC-36 / ARCH-36 | Not implemented | Not run |

## Non-functional traceability
| NFR | Phương pháp xác minh | Trạng thái |
|---|---|---|
| NFR-01/02 | PERF-CPU, PERF-300s, đo peak RAM, CPU | Partial — 36 presets + 300s/1080p60 passed; aggregate sampled private peak 1,681 GiB, min available 2,998 GiB including admission; repetitions/ACC-01 pending |
| NFR-03 | FFprobe output matrix, playback | Partial — 36 outputs: H.264/AAC, dimensions/FPS/frame count/timestamps pass; listening pending |
| NFR-04/05 | PERF-preview, UI latency percentile | Partial — latest 12/100 UI selection P95 34,7/34,4ms, preview 29,05/29,23FPS; historical outlier retained; contention in S6 report, ACC-01 pending |
| NFR-06/07 | Sync reference timestamps, WER/CER/word timing | Partial — VFR trim/rate + 7 preview/MP4 frame comparisons pass; independent ASR/word gold and listening pending |
| NFR-08/09 | Integration cancel/progress/recovery/atomic save | Partial — API/browser recovery, root crash/orphan cleanup, publish cancel/fsync, package snapshot and editor lease tested; full fault matrix pending |
| NFR-10/11 | Offline tests, permission and secret audit | Partial — offline model flags/local workers, explicit cloud-disabled no-egress, auth/origin/path regressions; full security audit pending |
| NFR-12/13/14 | Vietnamese font audit, zero mandatory paid dependencies, restore package | Partial — Vietnamese caption/card/lyrics fixture comparison, no added paid dependency, portable/Drive round-trips; full font/license/cross-PC review pending |

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

## Evidence cập nhật — 24/11/2026

26 unit, 63 integration và 11 browser regression tests đạt; browser fidelity riêng
7/7 mốc ảnh đạt. Build/typecheck/Ruff/Prettier đạt. ASR polling browser dùng
transport fixture có ghi rõ; worker local thật được kiểm riêng: 6 development
jobs small/medium/alignment Việt/Anh, 2 instrumental no-hallucination, 2 alignment
fallback. Không dùng các mẫu này thay independent corpus/gold.

36/36 preset MP4 đã decode; VFR trim/rate đạt. Hai round-trip Drive cloud thật bằng
media/template tự tạo đạt; 4 native chooser cases đạt. Source GC/pins/cache quota
và publish/worker crash faults đã có regression. Video 300s/1080p60 đã đạt E2E và independent decode (18.000 frame/0 timestamp
errors); contention/resource metrics được trình bày trong [báo cáo S2–S6](docs/planning/S2_S6_RESULTS.md).

Không nâng FR thành Verified từ code hoặc smoke. Quality/listening, ACC-01,
full security/fault matrix và Drive cross-PC/quota vẫn mở. Không sửa scope C/M/L/P,
AC IDs hoặc các quyết định chưa duyệt.
