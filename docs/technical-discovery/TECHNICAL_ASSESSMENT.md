# Technical Assessment — AI Music Video Studio

Ngày đánh giá: **22/11/2026 (Asia/Saigon)**. Trạng thái: **đề xuất Technical Discovery; chưa phê duyệt kiến trúc; chưa chạy PoC**.

**Cập nhật xác nhận 22/11/2026:** Product Owner đã xác nhận 18 định hướng và điều kiện trong [OPEN_QUESTIONS.md](../../OPEN_QUESTIONS.md), gồm SQLite runtime + portable snapshot và cloud tắt mặc định. Các nhận xét “chưa xác nhận” bên dưới phản ánh lúc khảo sát trước cập nhật này; trạng thái mới trong OPEN_QUESTIONS được ưu tiên. Chưa phê duyệt chạy PoC, checkpoint/license, corpus/ngưỡng cụ thể, Remotion hoặc thay đổi layout; không coi toàn bộ TD-01–07 đã được duyệt.

## 1. Kết luận và giới hạn bằng chứng

Đủ cơ sở lập PoC local CPU cho Lyrics AI và Video Rendering. **Chưa đủ bằng chứng chọn stack, model hoặc xác nhận sản phẩm đáp ứng Windows 11/RAM 16 GB.** Khả năng do upstream công bố được phân biệt với chất lượng hát Việt/Anh và hiệu năng trên máy đích.

Chỉ nghiên cứu và tạo năm tài liệu trong thư mục này. Không cài dependency, tải model/media, gọi API inference, viết application code hoặc sửa baseline. Tất cả benchmark là **Not run**. Xem [POC_PLAN.md](POC_PLAN.md) để biết thứ tự, phép đo và cổng quyết định.

## 2. Tài liệu thực tế đã đọc

`docs/requirements/` và `docs/decisions/` chưa tồn tại tại thời điểm khảo sát. Đã đọc toàn bộ tài liệu tương ứng ở root:

| Nguồn thực tế | Vai trò |
|---|---|
| [PRD_v1.0.md](../../PRD_v1.0.md) | A–G, scope Core/Complete/Later, G1–G5 |
| [SRS_v1.0.md](../../SRS_v1.0.md) | 38 FR, 14 NFR, BR, AC/test catalogue |
| [RTM_v1.0.md](../../RTM_v1.0.md) | 38 FR và trạng thái kiểm chứng |
| [OPEN_QUESTIONS.md](../../OPEN_QUESTIONS.md) | 18 câu hỏi chưa chốt |
| [AGENTS.md](../../AGENTS.md) | Quy trình `dev`, phê duyệt commit, technical principles |

Không tìm thấy ADR đã phê duyệt. Next.js/TypeScript/Tailwind trong AGENTS là ưu tiên có điều kiện; SQLite/Remotion và model cụ thể chưa phải quyết định đã chốt. Không di chuyển hoặc sửa tài liệu nguồn.

## 3. Rà soát đầy đủ và nhất quán

| ID | Phát hiện | Ảnh hưởng / xử lý đề xuất |
|---|---|---|
| GAP-01 | Đường dẫn trong AGENTS khác layout; SRS trỏ `../decisions/OPEN_QUESTIONS.md` | Dùng nguồn root trên; xin duyệt chuẩn hóa layout riêng |
| GAP-02 | RTM có đủ 38 mã FR của SRS, nhưng AC-01–36 mới là catalogue nhóm | Cần test case độc lập có input/action/expected, đặc biệt lỗi và khôi phục; chưa thể tuyên bố traceability hoàn chỉnh |
| GAP-03 | A–G xác nhận yêu cầu; PRD nói chưa duyệt kiến trúc; RTM ghi Proposed/Approved chung | Giữ A–G; lập decision log để tách yêu cầu đã duyệt, cách triển khai và giả thuyết |
| GAP-04 | “Từng từ” tiếng Việt chưa định nghĩa âm tiết, từ ngữ nghĩa hay đơn vị highlight | Đề nghị PoC báo đơn vị tách bằng khoảng trắng và CER; user duyệt cách hiển thị trước schema cuối |
| GAP-05 | “Hỗ trợ” rap/remix/nhiều giọng/instrumental chưa có ngưỡng riêng | Nhận input không đồng nghĩa nhận dạng chính xác; kiểm chứng và báo giới hạn, không tự cắt scope FR-205 |
| GAP-06 | NFR-04/05/06 là mục tiêu thử nghiệm, NFR-07 chưa có ngưỡng | Ngưỡng trong PoC chỉ dùng sàng lọc, chờ ACC-01; không gán ≤100 ms cho ASR |
| GAP-07 | 720/1080p cho ba tỷ lệ chưa chốt kích thước; chưa chốt codec input, VFR, track/file caps | Duyệt matrix đề xuất trong PoC, đo trước giới hạn công bố; giữ đủ các lựa chọn E |
| GAP-08 | Manual save/recovery rõ, nhưng ownership asset, atomic package, migration/conflict/GC chưa chi tiết | Thử crash/restore và shared asset ở POC-05; không coi SQLite đã được chọn |
| GAP-09 | Cloud opt-in có, nhưng phạm vi consent, thời hạn, revoke và log chưa chốt | Mặc định tắt; chỉ thử dữ liệu tổng hợp sau phê duyệt riêng |
| GAP-10 | FR-206 yêu cầu gợi ý ≥2 đoạn khi có thể, nhưng chưa định nghĩa chất lượng và clip quá ngắn | Bổ sung khảo sát heuristics cục bộ và so với chọn tay; không coi năng lượng âm thanh là “đoạn hay” |
| GAP-11 | FR-107 Core rõ trong SRS/RTM; PRD nói “nếu cần cho Core” | Kế hoạch giữ save-as-template/reuse trong Core; xin xác nhận wording, không chuyển sang Complete |
| GAP-12 | Blank builder, advanced effects, split/duplicate/snap/lock-hide thuộc Complete | Giữ backlog và khả năng mở rộng dữ liệu; không đưa UI Complete vào PoC/Core |
| GAP-13 | AGENTS dừng tại `### AI` | Không suy diễn quy tắc thiếu; áp dụng PRD/SRS và yêu cầu trực tiếp |

Baseline A–G được giữ: editor ưu tiên; template-first/draft editable; lyrics Việt/Anh có review; manual save; offline local/CPU 16 GB/300 giây; không login app; Drive snapshot; dịch vụ trả phí không bắt buộc; Vercel Later. Drive/provider có tài khoản bên ngoài không đồng nghĩa thêm login cho app.

## 4. Lyrics AI: các phương án cần đo

| Phương án | Lợi ích dự kiến | Đổi lại / bằng chứng thiếu | Đề xuất |
|---|---|---|---|
| faster-whisper, checkpoint multilingual `small`, CPU INT8 | Baseline nhẹ; API transcription và timestamp sẵn | Speech benchmark không đại diện singing; INT8 vẫn cần đo lỗi và RAM | Thử đầu tiên |
| Multilingual `medium`, CPU INT8 | Ứng viên ưu tiên chất lượng | Có thể chậm hoặc cạnh tranh RAM với browser | Chỉ mở rộng khi baseline thiếu chất lượng và còn ngân sách máy |
| whisper.cpp quantized | Đường thay thế khi packaging Python có vấn đề | Tích hợp/định dạng model khác; không tự có forced alignment tương đương | Dự phòng có điều kiện |
| WhisperX forced alignment | Căn transcript đã duyệt vào audio; tách lỗi ASR khỏi lỗi timing | Phụ thuộc model theo ngôn ngữ, tokenizer và bộ thư viện native | Thử English và Vietnamese riêng |
| Segment timing + nhập tay/LRC/SRT | Giữ workflow khi alignment lỗi | User cần sửa câu; không cung cấp word timing giả | Fallback bắt buộc, vẫn phải đo sentence timing |

Upstream faster-whisper có CPU INT8; benchmark `small` chạy trên i7-12700K/8 threads, **không phải máy đích**. CTranslate2 liệt kê wheel Windows x86-64 và Visual C++ runtime. Đây chỉ là cơ sở thử tương thích. [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [CTranslate2 installation](https://opennmt.net/CTranslate2/installation.html).

WhisperX hiện ánh xạ `vi` tới `nguyenvulebinh/wav2vec2-base-vi-vlsp2020`, `en` tới Wav2Vec2; source `main` biến động và chưa bảo đảm bản release sẽ giống. Checkpoint Việt công bố **CC BY-NC 4.0**, huấn luyện/đánh giá speech. Phải khóa revision, kiểm tra license và đo singing; không suy rộng WER speech sang lyrics. [Alignment source](https://github.com/m-bain/whisperX/blob/main/whisperx/alignment.py), [model card](https://huggingface.co/nguyenvulebinh/wav2vec2-base-vi-vlsp2020).

Đề xuất pipeline kiểm chứng: giữ audio gốc → decode bản làm việc → ASR → user review → alignment trên lời đúng → kiểm tra thứ tự/range/coverage → word timing hoặc sentence timing cần review. Giữ provenance cho transcript, timestamp và các lần sửa. Điểm số aligner chỉ là tín hiệu, chưa phải xác suất chất lượng đã hiệu chuẩn.

Rap cần kiểm tra tốc độ âm tiết; remix cần kiểm tra lặp/cắt/reverb; overlap có thể mất giọng phụ. Với code-switch, thử chia đoạn ngôn ngữ và báo đoạn chưa căn được, không mặc định một aligner cho cả bài. WhisperX nêu hạn chế overlapping speech và ký tự ngoài dictionary. [WhisperX limitations](https://github.com/m-bain/whisperX#limitations-).

Sped-up/slowed cần phân biệt nguồn đã biến đổi với playbackRate trong editor. Không đoán “bản gốc” rồi ánh xạ tự động. Vocal separation chỉ là nhánh A/B có điều kiện: giữ mix gốc, đo chất lượng tăng so với thời gian/RAM/artifact; không coi stem sạch tuyệt đối. Demucs có CPU mode nhưng repo gốc đã archive, cần kiểm tra maintenance trước chọn. [Demucs](https://github.com/facebookresearch/demucs).

Instrumental/silence cần negative controls: VAD speech không đủ chứng minh có hát hoặc không hát. Chặn tự áp dụng lyrics chưa review; không đoán lời từ metadata/tên bài. Nếu chưa có ranh giới câu đáng tin thì yêu cầu nhập/sửa timing, không chia đều thành word timestamps.

## 5. Preview/render và editor

| Lựa chọn | Điểm mạnh | Chi phí / rủi ro | Điều kiện chọn |
|---|---|---|---|
| Remotion Player + composition chung + renderer local | Tái sử dụng biểu diễn React cho preview/export | Browser decoding, fonts, RAM và khác biệt rendering vẫn phải đo | POC-03/04 đạt fidelity và tài nguyên |
| FFmpeg filtergraph + browser preview | Mạnh ở decode/filter/mux; ít lớp browser ở export | Phải duy trì hai cách vẽ text/effect, dễ lệch preview | Chỉ chọn sau phép so sánh fidelity, không tự dùng fallback này làm giảm tiêu chuẩn |
| Canvas/WebGL custom editor renderer | Kiểm soát editor sâu | Công sức cao, thêm đường xuất cần duy trì | Chưa ưu tiên; xem lại nếu hai phương án đầu thất bại |

Player là thành phần embed composition, không chứng minh multi-track editor hoàn chỉnh. `renderMedia()` có progress/cancel và tham số concurrency/cache; cần worker quản lý job, lỗi và cleanup. Không cam kết GPU-free chỉ vì encode dùng CPU: đo cả browser/software rendering và iGPU thực tế. [Player](https://www.remotion.dev/docs/player), [renderMedia](https://www.remotion.dev/docs/renderer/render-media).

FFmpeg là ứng viên preprocess audio/proxy, normalize input, encode/mux và ffprobe kiểm chứng metadata; bộ codec phụ thuộc binary/build. Không giả định executable của Remotion, PyAV và FFmpeg standalone là một phiên bản. [Filters](https://ffmpeg.org/ffmpeg-filters.html), [ffprobe](https://ffmpeg.org/ffprobe.html).

Đề xuất model editor để thử, chưa phải ADR:

- Project versioned có asset IDs, ordered tracks/items, transform/effect, caption/lyrics và export preset. UI selection/zoom tách khỏi nội dung; save/reopen cần quy định phần nào là editor state phải giữ.
- Một canonical timeline, phân biệt `sourceStartMs`, `startMs`, duration và playback rate. Với tốc độ cố định: `tTimeline = itemStart + (tSource - sourceStart) / rate`; loại bỏ phần ngoài clip; duration đầu ra phải phù hợp source/rate. Quy tắc round sang frame và khoảng `[start,end)` cần test biên.
- Undo/redo qua command/transaction có giới hạn memory; trim/reorder không ghi đè asset gốc. Job đọc snapshot bất biến, không đọc state đang sửa.
- Template versioned khai báo slot/type/required/default/style; instantiate tạo project IDs mới và bind media, giữ template gốc bất biến. Thử project → template → project khác; blank builder thuộc Complete.
- Một hàng đợi nặng chạy tuần tự ban đầu để đo CPU/RAM; số worker cuối cùng phụ thuộc benchmark. Không quyết định backend language/framework trong discovery.

Remotion công bố Free License cho cá nhân/đơn vị tối đa 3 người có điều kiện; cần xem license đúng phiên bản, phân biệt paid Editor Starter. FFmpeg LGPL/GPL phụ thuộc cấu hình build; kiểm tra trước phân phối. [Remotion licensing](https://www.remotion.dev/pricing), [FFmpeg license](https://ffmpeg.org/legal.html).

## 6. Ma trận quyết định chờ phê duyệt

| ID | Đề nghị | Liên hệ Open Questions | Chủ quyết định / bằng chứng cần |
|---|---|---|---|
| TD-01 | Cho phép PoC local biệt lập theo thứ tự trong plan, gồm cài/tải có danh mục sau duyệt | AI-03/04, ACC-01 | Product Owner; môi trường và licenses được ghi trước chạy |
| TD-02 | Duyệt bộ dữ liệu có quyền dùng, đơn vị highlight Việt và ngưỡng sàng lọc | MED-02, ACC-01 | Product Owner; manifest + annotations |
| TD-03 | Thử small → medium có điều kiện, WhisperX và alignment Việt có NC license | AI-03/04/05 | Product Owner; không mặc định cho mục đích thương mại |
| TD-04 | Thử Remotion composition chung + FFmpeg utilities, đủ matrix preset | UX-01, MED-04 | Product Owner; fidelity/resource/license evidence |
| TD-05 | So sánh JSON package và SQLite runtime + package; không chọn live DB sync | ST-01/02/03/04 | Product Owner; crash + restore + Drive round trip |
| TD-06 | Giữ cloud tắt; nếu thử Gemini thì chỉ caption tổng hợp, opt-in riêng | AI-01/02/06 | Product Owner; quota, data-use, billing xác minh trong account |
| TD-07 | Chuẩn hóa layout baseline và wording FR-107 ở task riêng | GAP-01/11 | Product Owner; không sửa A–G |

Tài liệu bổ trợ: [AI_PROVIDER_COMPARISON.md](AI_PROVIDER_COMPARISON.md), [STORAGE_STRATEGY.md](STORAGE_STRATEGY.md), [RISK_ASSESSMENT.md](RISK_ASSESSMENT.md). TD-01–07 **đều chưa phê duyệt**. Dừng ở planning; không bắt đầu PoC từ việc tài liệu này tồn tại.
