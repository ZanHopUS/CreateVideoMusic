# SRS v1.0 — AI Music Video Studio

**Trạng thái:** Baseline chức năng v1.0 (22/11/2026). Ký hiệu **C = MVP Core; M = MVP Complete; L = Later; P = phải kiểm chứng qua PoC**. Ngôn ngữ UI: tiếng Việt; local-first; một người dùng; ngân sách dịch vụ bắt buộc 0 đồng.

## 1. Định nghĩa hệ thống và ranh giới
Ứng dụng local web bao gồm UI/editor, backend local, media storage, job worker, AI services optional và renderer. Local backend chỉ chấp nhận yêu cầu từ nguồn được cho phép, kiểm tra quyền truy cập file. Trình duyệt không được giả định có quyền ghi bất kỳ đường dẫn nào. Dữ liệu project giữ reference tới media, timeline, template, captions, lyrics và export presets. Vercel và cloud worker thuộc giai đoạn sau.

## 2. Vai trò và tác nhân
**User:** duy nhất, tạo/chỉnh/lưu/xuất project. **AI provider:** local hoặc internet được bật rõ. **Render worker:** xử lý job theo snapshot. **Drive desktop:** cơ chế đồng bộ file bản sao, không phải API trực tiếp trong MVP.

## 3. Functional Requirements — có mã ổn định
| ID | Phân hệ / yêu cầu có thể kiểm thử | Phạm vi | AC / Test |
|---|---|---|---|
| FR-101 | Xem/chọn ba nhóm template TPL-01/02/03; workflow template-first | C | AC-01 / E2E-01 |
| FR-102 | Tạo project từ template và mở editor bản nháp | C | AC-01 / E2E-01 |
| FR-103 | Nhập nhiều ảnh/video, sắp xếp thứ tự và thời lượng | C | AC-02 / E2E-02 |
| FR-104 | Caption thủ công, chỉnh sửa và gợi ý AI nếu cấu hình | C | AC-03 / IT-03 |
| FR-105 | Thư viện nhạc cá nhân, chọn thủ công hoặc gợi ý từ nội dung có sẵn | C(P gợi ý) | AC-04 / IT-04 |
| FR-106 | Video draft giữ layer chỉnh sửa, không chỉ xuất video phẳng | C | AC-05 / E2E-01 |
| FR-107 | Template từ project, đánh dấu placeholder và tái sử dụng | C | AC-06 / IT-06 |
| FR-108 | Template từ trang trống, thêm layer/placeholder, save/open/reuse | M | AC-07 / E2E-07 |
| FR-109 | Cho phép đổi bố cục/font/hiệu ứng template không sửa template gốc | C | AC-06 / IT-06 |
| FR-201 | Nhận dạng tiếng Việt/Anh từ audio bằng pipeline thật (giới hạn chất lượng theo PoC) | C(P) | AC-08 / AI-01 |
| FR-202 | Duyệt, chỉnh lời và mốc thời gian trước khi dùng | C | AC-09 / IT-09 |
| FR-203 | Nhập tay và import LRC/SRT có báo lỗi định dạng | C | AC-10 / UT-10 |
| FR-204 | Căn lyrics theo câu; ưu tiên theo từ nếu tin cậy; fallback câu | C(P) | AC-11 / AI-02 |
| FR-205 | Nhận đầu vào rap/remix/sped-up/slowed/multiple voices/instrumental; báo giới hạn, không bịa lyrics | C(P) | AC-12 / AI-03 |
| FR-206 | Đề xuất nhiều đoạn nhạc và nghe thử; luôn cho trim thủ công | C(P) | AC-13 / IT-13 |
| FR-207 | Text/lyrics nhiều font dấu Việt, màu, viền, shadow, position, animation | C cơ bản; M phong phú | AC-14 / IT-14 |
| FR-208 | Gợi ý style lyrics theo mood/template và cho user override | M(P) | AC-15 / IT-15 |
| FR-301 | Editor multi-track media, audio, lyrics, caption/text; playhead và seek | C | AC-16 / E2E-16 |
| FR-302 | Kéo thả/trim/đổi duration; undo/redo; lưu trạng thái | C | AC-17 / IT-17 |
| FR-303 | Split, duplicate, snapping, lock/hide track | M | AC-18 / IT-18 |
| FR-304 | Crop/fit/blur, brightness cơ bản; zoom/pan/rotate/filter nâng cao | C/M | AC-19 / IT-19 |
| FR-305 | Hiệu ứng fade/slide/scale trong Core; presets mở rộng ở M | C/M | AC-20 / IT-20 |
| FR-306 | Music Card: cover, song/artist, progress; chỉnh layout/color nâng cao | C/M | AC-21 / E2E-21 |
| FR-307 | Preview và export dùng một timeline canonical, thống nhất z-order và timing | C | AC-22 / IT-22 |
| FR-401 | Tạo/đổi tên/mở/xóa project, chọn folder lưu, lưu thủ công | C | AC-23 / E2E-23 |
| FR-402 | Khôi phục timeline, lyrics, effects, template và references khi mở lại | C | AC-24 / E2E-24 |
| FR-403 | Báo dirty-state, cảnh báo rời project khi chưa lưu | C | AC-25 / IT-25 |
| FR-404 | Recovery snapshot riêng, hỏi trước khi restore; không ghi đè manual save | C | AC-26 / IT-26 |
| FR-405 | Thư viện media tái sử dụng, metadata/thumbnail/search, không xóa asset dùng chung | C | AC-27 / IT-27 |
| FR-406 | Chọn thư mục project và thư mục export; xử lý missing media/relink | C | AC-28 / IT-28 |
| FR-407 | Drive desktop sync qua **snapshot/project package nhất quán**, không live DB | C (workflow hỗ trợ) | AC-29 / IT-29 |
| FR-408 | MP4 H.264/AAC, presets 720/1080p, 30/60fps, 9:16/16:9/1:1 | C | AC-30 / E2E-30 |
| FR-409 | Render worker, progress, cancel, retry, output preview/download/open-folder | C | AC-31 / E2E-31 |
| FR-410 | Quản lý temp, xử lý thiếu dung lượng, xác minh metadata output | C | AC-32 / IT-32 |
| FR-501 | API abstraction local/Gemini/OpenAI; provider optional có thể disable | C (interface); M (nhiều adapter) | AC-33 / IT-33 |
| FR-502 | Không làm gián đoạn edit/render nếu cloud AI thất bại/offline | C | AC-34 / IT-34 |
| FR-503 | Không gửi media/caption lên cloud khi chưa có đồng ý rõ | C | AC-35 / SEC-35 |
| FR-504 | Build/deploy frontend Vercel, đánh giá Local Agent/cloud worker | L | AC-36 / ARCH-36 |

## 4. Business Rules — các bất biến
| ID | Quy tắc |
|---|---|
| BR-01 | Workflow chuẩn bắt đầu ở template; mỗi template khai báo slots bắt buộc và tùy chọn; draft là chỉnh sửa được. |
| BR-02 | Số asset trong project có thể >1; reorder không phá reference; template gốc bất biến khi áp dụng. |
| BR-03 | Gợi ý caption/style/music không tự ghi đè lựa chọn đã xác nhận; chọn nhạc từ thư viện đã nhập/có quyền sử dụng. |
| BR-04 | Nếu AI nhận dạng không tin cậy hoặc instrumental, báo trạng thái; cho sửa/nhập tay; không bịa lời. |
| BR-05 | Timestamp từ bài hát gốc phải ánh xạ sang local time sau trim/tốc độ. Dùng một time unit thống nhất; không chia đều lời thành từ rồi coi là chính xác. |
| BR-06 | Khi thay đổi lyric style không tự đổi lyric timing; render/preview dùng cùng schema và animation logic. |
| BR-07 | Manual save là bản chính thức. Recovery không thay bản chính nếu chưa hỏi; khi có dirty state phải cảnh báo. |
| BR-08 | Các asset dùng chung không bị xóa vật lý khi chỉ gỡ khỏi project; không xóa file gốc tùy tiện. |
| BR-09 | Job render dùng snapshot bất biến; chỉnh editor khi job chạy không đổi output job đang chạy. |
| BR-10 | Project tối đa 300s; preset phải đúng metadata; xử lý lỗi/thiếu dung lượng/hủy job rõ ràng. |
| BR-11 | Cloud AI phải opt-in; key lưu tại backend/env, không nằm trong client bundle hoặc repository. |
| BR-12 | Drive đồng bộ project package/snapshot đã đóng; không copy live SQLite đang ghi hoặc temp render vào sync folder. |
| BR-13 | Không ingest nhạc từ URL bất kỳ hoặc nguồn bị hạn chế quyền; upload phải qua validation/MIME/codec và giới hạn truy cập filesystem. |

## 5. Data contracts đề xuất (chưa chốt kỹ thuật)
**Project:** id, name, schemaVersion, aspectRatio, fps, width, height, templateId, orderedTracks, manualSavedAt, lastEditedAt. **MediaAsset:** id, sourceUri/localPathRef, mediaType, checksum, durationMs, width/height, mime, ownerScope. **TimelineItem:** id, trackId, assetId?, startMs, durationMs, sourceStartMs, speed, transform, effects, style, zIndex. **LyricsSegment:** id, text, audioSourceStartMs, audioSourceEndMs, alignedWords[]?, alignmentStatus, reviewed. **LyricsWord:** text, startMs, endMs, confidence?, source. **Template:** id, schemaVersion, category, slots, layers, defaults, authorScope. **RenderJob:** id, projectSnapshotId, preset, status, progress, outputPath, error.

**Thời gian:** `t_video=(t_original - t_trimStart)/playbackRate` đối với tốc độ phát cố định, khi segment thuộc vùng được chọn; đối với time remapping phức tạp phải ánh xạ từng đoạn. Timestamp lưu nhất quán bằng mili-giây hoặc ticks chính xác, không trộn thời gian nguồn và timeline.

## 6. Non-functional Requirements và đo lường
| ID | Yêu cầu | Mục tiêu / chứng minh |
|---|---|---|
| NFR-01 | Windows 11/RAM 16GB/CPU-only | test trên máy chuẩn, không bắt buộc GPU rời |
| NFR-02 | Project dài tối đa 5 phút | load/edit/export 300s, đo thời gian/RAM |
| NFR-03 | Chất lượng output | MP4 H.264/AAC; 720/1080p, 30/60FPS, 3 ratios |
| NFR-04 | Preview project đơn giản | **mục tiêu thử nghiệm** ≥24 FPS, phải benchmark |
| NFR-05 | UI response | **mục tiêu thử nghiệm** P95 ≤200ms cho thao tác UI không nặng |
| NFR-06 | Render lyrics theo timestamp đã duyệt | **mục tiêu thử nghiệm** sai lệch ≤100ms, không áp dụng ASR accuracy |
| NFR-07 | Transcription/word alignment quality | đo WER/CER, MAE timing trên bộ dữ liệu phân loại Việt/Anh, remix/rap/multiple voices; ngưỡng khóa sau PoC |
| NFR-08 | Không khóa UI khi chạy job | editor phản hồi, progress/cancel và trạng thái lỗi |
| NFR-09 | Tính toàn vẹn save/recovery | atomic save, restore riêng, không ghi đè không đồng ý |
| NFR-10 | Offline cốt lõi | editor, manual caption/lyrics, render local làm việc không mạng sau cài đặt |
| NFR-11 | Bảo mật và riêng tư | path traversal checks, allowed origins, no secrets in frontend, opt-in cloud uploads |
| NFR-12 | Tiếng Việt và fonts | giao diện Việt; glyph dấu Việt không lỗi preview/render |
| NFR-13 | Không phí bắt buộc | dependency local miễn phí; API paid không bật mặc định; Free Tier cần xác minh quota/terms |
| NFR-14 | Đảm bảo portable backups | package snapshot có manifest/checksum; recover thử ở đường dẫn khác |

## 7. Acceptance Criteria và Test Catalogue (nguồn tham chiếu RTM)
- **AC-01–07 / E2E-01,02,07:** cả ba mẫu; media reorder; caption AI fallback; nhạc từ thư viện; draft còn layer; save-as-template/reuse; blank template ở M.
- **AC-08–15 / AI-01,02,03:** AI thật; review; LRC/SRT; word-fallback; instrumental không sinh lời; đề xuất 2+ đoạn khi tìm được, nghe thử; tiếng Việt có dấu; người dùng override style.
- **AC-16–22 / E2E-16,21 & IT:** multi-track editor, trim/undo; editor advanced ở M; preview và render thống nhất.
- **AC-23–29 / E2E-23,24 & IT:** lưu thủ công, mở lại, warning dirty, recovery không overwrite, thư viện shared, folder/relink, backup package local/Drive sync.
- **AC-30–32 / E2E-30,31 & IT:** đo metadata 3 ratios×2 resolutions×2 FPS (theo ma trận hỗ trợ), audio/video/lyrics, progress/cancel/retry, temp cleanup.
- **AC-33–36 / IT/SEC/ARCH:** provider modular, offline fallback, explicit consent, kiểm thử deployment tương lai.

### E2E bắt buộc trước release Core
1. TPL-01: một ảnh → caption → nhạc → draft → edit → save/reopen → MP4.
2. TPL-02: hai ảnh → music card/progress → reorder → edit → MP4.
3. TPL-03: video nền → nhạc → transcription hoặc LRC → review timestamp → lyric style → MP4.
4. Trường hợp offline/AI lỗi; instrumental; crash recovery; mất asset; hết dung lượng; cancel render.

## 8. Các quyết định chưa chốt, ràng buộc và exit criteria
Xem `../decisions/OPEN_QUESTIONS.md`. Không viết code khi chưa chốt những câu hỏi blocker về AI pipeline, storage, local permissions và nguồn media. PoC ưu tiên: lyrics Việt/Anh; alignment từ/câu; preview-render fidelity; RAM CPU-only; snapshot Drive. **Release Core:** E2E pass, không lỗi blocker/critical, video xuất kiểm tra thực, tài liệu cài đặt/khôi phục, không phát sinh phí bắt buộc.
