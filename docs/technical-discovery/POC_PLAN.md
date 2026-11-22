# Proof of Concept Plan

Ngày: **22/11/2026 (Asia/Saigon)**. Trạng thái toàn bộ PoC: **Not run — chờ phê duyệt**. Đây là thiết kế thử nghiệm, chưa phải application implementation hoặc kiến trúc được chốt.

**Cập nhật phê duyệt thực hiện:** Product Owner đã đồng ý kế hoạch PoC local, dữ liệu có quyền dùng, mục đích cá nhân phi thương mại. Cho phép setup/cài dependency/tải model và thực hiện các thử nghiệm local; ngưỡng dùng sàng lọc, không phải release guarantee. Các câu “chưa phê duyệt/chưa chạy” bên dưới là trạng thái lúc lập kế hoạch; xem [POC_STATUS.md](POC_STATUS.md) để biết trạng thái thực hiện mới nhất. Cloud tiếp tục tắt, không commit/push.

**Cập nhật xác nhận 22/11/2026:** Định hướng và điều kiện trong [OPEN_QUESTIONS.md](../../OPEN_QUESTIONS.md) đã được Product Owner xác nhận. Phê duyệt đó chưa bao gồm bắt đầu PoC, danh mục cài/tải, corpus, checkpoint/license hoặc các ngưỡng số trong kế hoạch này. SQLite runtime + portable snapshot là hướng đã xác nhận; JSON được so sánh để kiểm tra snapshot/độ phức tạp, không tự thay hướng SQLite đã được duyệt.

## 1. Mục tiêu và điều kiện bắt đầu

Giảm bất định lớn nhất: (1) lyrics Việt/Anh có thể dùng sau review trên CPU hay không; (2) preview/export thống nhất và tạo MP4 thật trong RAM 16 GB hay không; (3) project có thể khôi phục độc lập và đồng bộ snapshot an toàn hay không.

Trước khi thử, Product Owner duyệt TD-01–05 trong [TECHNICAL_ASSESSMENT.md](TECHNICAL_ASSESSMENT.md): dữ liệu có quyền dùng, license model, ngưỡng tạm, dung lượng/thời gian, danh mục cài/tải và thư mục PoC biệt lập. Cloud TD-06 là opt-in riêng. Ghi rõ đây là cho phép PoC, không phải phê duyệt stack chính thức. Chưa có các phê duyệt này; dừng trước bước setup.

## 2. Thứ tự và timebox đề xuất

| Thứ tự | PoC | Câu hỏi và phụ thuộc | Timebox công sức dự kiến | Liên kết yêu cầu |
|---|---|---|---|---|
| 0 | POC-00: environment/data readiness | Máy đích, giấy phép và ground truth sẵn sàng? | 1 ngày + thời gian annotation riêng | NFR-01/10/11/13; MED-02/04 |
| 1 | POC-01: local ASR | Transcript hát đủ tốt để sửa? Cần POC-00 | 2 ngày | FR-201/202/205, AI-01/03; AI-03/05 |
| 2 | POC-02: forced alignment | Timing đúng với lời đã review? Cần transcript ground truth, không bắt buộc ASR pass | 2 ngày | FR-203/204/207; AI-02, UT-10; AI-04 |
| 3 | POC-03: render/fidelity smoke | Ba template xuất thật với lời đã duyệt? Không bị chặn bởi model ASR thất bại | 2 ngày | FR-106/207/306/307/408; IT-22, E2E-30 |
| 4 | POC-04: render/editor resource stress | 300s/1080p60, edit khi render, cancel và state reuse có khả thi? Cần POC-03 | 2 ngày | FR-101–109/301/302/409/410; NFR-02/04/05/08 |
| 5 | POC-05: storage/recovery/Drive | JSON vs SQLite, portable save, crash và conflict? Cần snapshot mẫu POC-03 | 2 ngày, chưa gồm chờ sync | FR-401–407; IT-26/28/29, NFR-09/14 |
| 6 | POC-06: optional cloud text | Caption hữu ích, free/privacy chấp nhận được? Cần opt-in riêng | 0.5–1 ngày | FR-104/501–503; IT-33/34, SEC-35 |
| 7 | POC-07: music segment suggestions | Hai gợi ý có ích hơn chọn tay? Có audio hợp lệ | 0.5–1 ngày | FR-105/206; IT-04/13; MED-03 |

Ưu tiên theo số thứ tự; rendering vẫn tiến hành bằng lyrics chuẩn nếu ASR chưa đạt. Timebox là ước tính công sức, không phải ngày giao hàng hoặc tốc độ chạy; nếu cần thêm model/solver/time phải báo và duyệt thay vì kéo dài vô hạn. POC-07 bảo toàn cam kết gợi ý nhiều đoạn, không đưa song recommender phức tạp vào Core. Builder UI, mobile, Vercel và speaker diarization hoàn chỉnh không phải mục tiêu thử lần này.

## 3. Bộ dữ liệu dự kiến — chưa thu thập

Không tải nhạc/lyrics từ nền tảng bị hạn chế. Dùng media user có quyền, tự tạo hoặc nguồn có license phù hợp; lưu manifest cục bộ, không commit media cá nhân lên GitHub. Lyrics và bản ghi âm cần quyền sử dụng riêng; tên bài không là bằng chứng có quyền.

| Nhóm | Số mẫu dự kiến | Nội dung |
|---|---|---|
| Vocal gốc | 24 clip × 20–40s, 12 Việt + 12 Anh | Mỗi ngôn ngữ: 4 hát rõ, 2 rap, 2 remix, 2 overlap/nhiều giọng, 2 có code-switch; ghi nhãn giọng chính/khó nghe |
| Negative controls | 8 clip × 20–40s | 4 instrumental khác thể loại, 2 silence, 2 noise/âm thanh không lời; đánh dấu đoạn không hát trong vocal clips |
| Speed variants | 8 clip từ 4 vocal gốc | Mỗi nguồn 0.8× và 1.25×; ghi tool/thuật toán/pitch preservation; không coi là 8 bài độc lập |
| Full-length | 4 input 300s, 2 Việt + 2 Anh | Bài/fixture được phép; có intro không lời và cuối bài; nếu lặp fixture để stress phải ghi rõ không dùng đánh giá chất lượng ASR |
| Editor/render | 3 project TPL-01/02/03 | Ảnh dọc/ngang/vuông, PNG alpha, video CFR và VFR, audio 44.1/48kHz, text dấu Việt và multiline |
| Storage/error | Bản sao disposable | Path Unicode/có khoảng trắng/dài, asset trùng dùng chung/missing, manifest hỏng, package thiếu và disk quota nhỏ |

Chia vocal theo **bài/nguồn**, 12 development và 12 held-out, mỗi tập 6 Việt/6 Anh, phân tầng thể loại gần tương đương. Cả variants và các đoạn cùng bài chỉ ở một tập; speed variants lấy từ development. Chia negatives 4/4, mỗi tập 2 instrumental + 1 silence + 1 noise. Khóa held-out trước tuning, chạy cấu hình cuối một lần; chỉ lặp để đo performance, không tuning sau khi xem lỗi. Full-length dành stress, không dùng nâng điểm held-out.

Ground truth: transcript thủ công cho toàn bộ vocal, ranh giới câu và vùng không hát. Word/syllable onset/end cho ít nhất 12 clip (mỗi ngôn ngữ 4 clear + 2 rap, ≥400 đơn vị/ngôn ngữ nếu đủ nội dung; không đủ thì thu thêm). Với tiếng Việt dùng đơn vị khoảng trắng làm primary score và CER giữ dấu; chưa gọi đó là từ ngữ nghĩa. Nếu thêm word-segmenter phải ghi tên/version và báo riêng.

Annotator thứ hai kiểm tra độc lập ≥20% clip, bao gồm tiếng Việt luyến âm và overlap; giải quyết bất đồng trước freeze. Nếu chỉ có một người, đánh dấu single-annotator, thực hiện review lần hai cách phiên và giảm độ mạnh kết luận. Không đo timing trên “lời chuẩn” lấy từ output model. Ground truth lưu hash/revision; báo số token/boundary thực tế.

Manifest tối thiểu: sampleId, sourceGroup, quyền dùng/attribution, language/genre/voice/speed labels, duration/sample-rate/codec, SHA-256, split, transcript/timing revision, annotator, ambiguity flag. Không lưu tên cá nhân hoặc đường dẫn private trong báo cáo public.

## 4. Thiết lập đo tái lập trên Windows 11

POC-00 sẽ ghi CPU model/cores/ISA, RAM thực, Windows build, disk loại/free space, power mode, iGPU/driver, browser, resolution, background apps; không giả định máy đang thao tác là máy đích. CPU-only nghĩa không phụ thuộc GPU rời; ghi rõ browser dùng iGPU hay software. Chọn CPU device cho model, không bật CUDA.

Sau duyệt mới khóa Python/Node/package versions tương thích thực tế, model revision/checksum/license, browser binary, FFmpeg build/config/encoders và font files. Không lấy `latest` làm bằng chứng tái lập; Node minimum upstream không đồng nghĩa runtime production nên chọn. Tách môi trường ASR/alignment và renderer nếu xung đột; ghi chi phí packaging.

Một cold start sau khi artifact đã có local + ba warm runs cho cấu hình finalist; tách download/setup, model load và inference. Với faster-whisper phải consume hết segments để đo hoàn tất. So sánh cùng audio, beam/thread count, VAD/language settings; không bật batch lớn ngay. Baseline một job nặng; thử thread 2/4 nếu CPU có, concurrency renderer 1 rồi 2 khi an toàn. Không chọn cấu hình bằng tốc độ đơn lẻ.

Sample tài nguyên mỗi 1s: CPU/process tree, private bytes và working set, RAM available toàn máy, disk I/O, free space, temp size. Ghi cả Python/Node/Chromium/FFmpeg con; không chỉ PID cha. Dữ liệu sample có thể bỏ sót peak ngắn, báo giới hạn. Lưu từng run, median, range và worst case; không tuyên bố percentile latency đáng tin từ ba lần chạy tổng.

Đo UI trên ≥100 thao tác seek/trim/drag khác nhau mỗi scenario sau warm-up, ghi event→state phản hồi; preview FPS/dropped frames trên 60s ổn định, thống kê jank. Nếu chỉ thử harness thì ghi harness, chưa nghiệm thu UX app. Sau chuẩn bị đầy đủ, chạy lại core fixtures khi ngắt mạng; ghi outbound/network failures để phát hiện font/model download ngầm.

## 5. Lyrics: phương pháp và Go/No-Go đề xuất

### Phép đo độc lập

- `WER = (substitutions + deletions + insertions) / referenceUnits`; với Việt ghi rõ whitespace-unit error rate. `CER` theo Unicode NFC giữ dấu. Primary normalization: lowercase, NFC, quy tắc bỏ punctuation thống nhất; không bỏ dấu để làm đẹp số. Báo bản gốc và normalized, từng ngôn ngữ/thể loại/clip; không gộp clean với hard rồi che lỗi.
- `RTF = processingWallSeconds / inputAudioSeconds`; báo ASR, alignment, separation riêng và tổng. Đo correction time: cùng người sửa transcript/timing model so với nhập tay, dùng cặp clip tương đương, đổi thứ tự để giảm learning effect; report số người và sample nhỏ.
- Alignment run A dùng ground-truth text để đo aligner; run B dùng transcript ASR đã/chưa review để đo pipeline. Không gán lỗi sai chữ cho timing đơn thuần.
- Onset/end MAE và P95 absolute error so với annotation; coverage = đơn vị có timing hợp lệ / reference units. Báo tỷ lệ unaligned, overlap, timestamp ngoài clip; interpolated timestamps đánh dấu riêng và không tính như aligned thành công.
- Đánh giá fallback câu bằng boundary error và khả năng review; silence/instrumental đo false text event/clip, độ dài hallucination và trạng thái cần user xác nhận. Không dùng confidence chưa hiệu chuẩn để công bố “không có lời”.

### Ngưỡng sàng lọc chờ TD-02/ACC-01

| Gate | Go đề xuất | No-Go / hành động |
|---|---|---|
| L1: ASR clean | Mỗi ngôn ngữ held-out clear: WER ≤30%, CER ≤15%; median correction time ≤60% nhập tay | Thử medium nếu tài nguyên cho phép; nếu vẫn fail ghi local candidate No-Go, không tự bỏ FR-201 |
| L2: word alignment | Với ground-truth text, mỗi ngôn ngữ clean: coverage ≥90%, onset và end MAE ≤150ms, P95 ≤300ms | Chỉ fallback câu sau khi L3 đạt; không công bố word sync đạt |
| L3: sentence fallback | Clean: ≥90% câu có timing hợp lệ; onset/end MAE ≤300ms, P95 ≤600ms; luôn sửa tay được | Chưa đủ cho auto sentence path; điều tra VAD/segmentation hoặc xin quyết định tiếp |
| L4: hard inputs | Tất cả clip được xử lý hoặc trả lỗi có thể khôi phục; báo metrics từng nhóm, 100% output cần review trước áp dụng | Không đặt quality guarantee hard cases khi chưa đo; failure phải ghi và yêu cầu phê duyệt giới hạn, không coi intake pass là ASR pass |
| L5: no-vocal safety | Trên toàn bộ negative controls: 0 lyrics tự áp dụng; 100% transcript đáng ngờ ở trạng thái review; báo riêng mọi false text và bỏ sót hát | Còn tự áp dụng hallucination → No-Go pipeline; không kết luận detector chính xác chỉ vì có review |
| L6: runtime | ASR + alignment finalist trên 300s clear: RTF ≤3, không OOM; resource gate R0 bên dưới | Tune tuần tự/thread/model; nếu không đạt user xem lại time budget, không tự tăng requirement máy |

Instrumental hoàn hảo trên sample nhỏ không bảo đảm tổng quát. L5 là gate workflow an toàn; false positive ASR vẫn là lỗi chất lượng phải báo. Word mode fail có thể cho **Conditional Go sentence mode** nếu L1/L3/L5/L6 đạt và user duyệt; không đổi ưu tiên word-fallback trong C.

VAD on/off trên development để kiểm tra mất phần hát kéo dài/rap. Separation A/B tối đa 6 hard development clips nếu ASR baseline yếu: chỉ đề nghị thêm nếu WER giảm ≥5 điểm phần trăm trên ≥4/6 clip, không làm clear xấu đi >2 điểm, tài nguyên vẫn đạt; con số là đề xuất, chưa chứng minh lợi ích. Demucs archive/license/versions phải được kiểm tra trước setup. Không tự thêm diarization dependency.

## 6. Video Rendering: matrix và Go/No-Go đề xuất

POC-03 dùng lyrics chuẩn để không trộn lỗi ASR. Cả ba template cùng canonical snapshot: TPL-01 ảnh + caption + nhạc; TPL-02 hai ảnh + Music Card/progress; TPL-03 video + lyric câu/từ. Fixtures có trim source, itemStart khác 0, rate 0.8/1.25, multiline/dấu Việt, transition và z-order chồng nhau.

Kích thước đề xuất cần duyệt, FPS nguyên 30/60:

| Ratio | 720 preset (W×H) | 1080 preset (W×H) |
|---|---|---|
| 9:16 | 720×1280 | 1080×1920 |
| 16:9 | 1280×720 | 1920×1080 |
| 1:1 | 720×720 | 1080×1080 |

Smoke: **3 templates × 3 ratios × 2 resolutions × 2 FPS = 36 output**, mỗi fixture 15s. Stress: mỗi template 300s, 1080p60 ở 9:16 (3 output); thêm TPL-03 300s 16:9 và 1:1 (2 output). Lặp finalist warm 3 lần sau screening; không nhân toàn bộ matrix cho mọi setting thread. Matrix này chưa thay thế toàn bộ E2E release.

Kiểm output bằng ffprobe (container, H.264/AAC, dimensions, average/r frame rate, sample rate, duration, audio presence), decode toàn file để phát hiện corruption và xem/nghe đầu/giữa/cuối. VFR input phải test seek và conversion, không suy ra đúng chỉ từ `r_frame_rate`. [ffprobe](https://ffmpeg.org/ffprobe.html).

So preview frame tại ít nhất 20 mốc/project, gồm clip/text boundaries, với frame render tương ứng. Dùng marker flash + audio click có timestamp chuẩn để đo AV/lyrics deviation ở đầu/giữa/cuối; kiểm encode delay và rounding. Highlight đúng chữ theo lời đã duyệt, không đánh giá lại ASR. Kiểm crop/layout/fonts/colors bằng review có checklist; không đòi pixel hash giống nhau qua lossy encoding. Giữ seed/time/fonts/assets cố định, không phụ thuộc wall-clock/network.

| Gate | Go đề xuất | No-Go / hành động |
|---|---|---|
| R0: tài nguyên chung | Tổng process tree workload peak private bytes ≤12 GiB, system available RAM ≥2 GiB ở các mẫu đo, không OOM/page-thrashing kéo dài | Dừng run nếu available <2 GiB liên tục 10s hoặc tăng mất kiểm soát; giảm concurrency/cache; không tự đòi GPU |
| R1: output | 36/36 smoke đúng preset, decode được, audio có; duration lệch ≤1 frame (kiểm audio padding riêng) | Điều tra input/encoder/time mapping; không bỏ 60FPS hoặc ratio đã xác nhận |
| R2: fidelity | Các mốc đã duyệt lệch ≤100ms ở preview/export, không thiếu dấu/font/layer, không drift tăng cuối clip | No-Go cách biểu diễn/renderer; FFmpeg-only cũng phải vượt cùng phép đo |
| R3: performance | Preview đơn giản ≥24FPS, UI P95 ≤200ms; 300s 1080p60 render RTF ≤10 (≤50 phút), đạt R0 | Đây là target sàng lọc, không phải guarantee; xem proxy/software render/thread và trình user kết quả |
| R4: job lifecycle | Progress đơn điệu theo phase, không 100% trước finalize; cancel ≤5s, process con thoát ≤10s, retry sạch | Worker còn treo hoặc báo thành công output thiếu → No-Go |
| R5: state/template | Undo/redo và save/reload giữ snapshot semantics; project mới không sửa template gốc; chỉnh trong khi render không đổi job snapshot | Bất kỳ mất state/reference → No-Go model dữ liệu |
| R6: offline | Các fixture đã chuẩn bị render/preview không tải font/model/asset qua mạng | Không coi lần online thành công là offline pass |

POC-04 harness thử 4 loại track (background/music/lyrics/caption) với baseline 12 items và stress 100 items để tìm bottleneck, **không chốt giới hạn sản phẩm**. Thử 50 lần trim/reorder/style + undo/redo, asset reuse ở hai projects. Lỗi disk-full mô phỏng bằng volume/quota disposable; không lấp đầy ổ máy thật.

## 7. Storage, cloud và đoạn nhạc

POC-05 so JSON snapshot và SQLite transactions + export package trên cùng fixtures. Theo [STORAGE_STRATEGY.md](STORAGE_STRATEGY.md): ít nhất 20 lần fault injection ở save/package phases, 10 round-trip restore ở folder khác, 2 Drive round-trip sau user cấp folder/tài khoản, offline file/unavailable/quota/conflict. Go: 0 corrupt manual save, 0 mất asset đang tham chiếu, hash/state khớp, recovery không overwrite khi chưa xác nhận, package không chứa path escape. Drive chưa thử → ST-03 vẫn mở, không đóng bằng test copy local.

POC-06 optional: 20 prompt caption tổng hợp tiếng Việt; user chấm tính phù hợp/sửa được, target ≥16/20 không bịa metadata và đáp ứng ràng buộc. Đo usage, latency, timeout/refusal/429 bằng tình huống kiểm soát; không spam làm hết quota để test. Go provider chỉ khi free eligibility/privacy được duyệt, budget vẫn $0, lỗi có fallback. Không có account consent → **Deferred**, không fail local Core.

POC-07: 6 track được phép, có câu/điệp khúc rõ; đề xuất ≥2 đoạn không trùng đáng kể nếu có đủ độ dài. So energy/novelty/beat heuristics đơn giản với chọn tay; user chấm hữu ích, target ≥4/6 track có ít nhất một gợi ý chấp nhận. Track ngắn/không đủ cấu trúc báo không đủ đề xuất và cho trim tay. Không đánh đồng tempo/energy với sở thích; giữ MED-03 mở nếu evidence yếu.

## 8. Bằng chứng, báo cáo và điểm dừng

Mỗi run dự kiến lưu cục bộ `evidence/<poc-id>/<run-id>/`: manifest hash, config/versions, raw transcript/timing, metrics CSV/JSON, resource samples, sanitized log, output metadata, screenshot/frame comparisons, lỗi và nhận xét. Đây là layout đề xuất, **chưa tạo evidence hoặc script**. Chỉ đưa báo cáo đã loại dữ liệu riêng tư vào Git sau user duyệt; model/cache/media không commit.

Bảng kết quả cần có requirement/test IDs, sample IDs/split, config và seed, cold/warm, metrics theo nhóm, pass/fail từng gate, manual edits, giới hạn và đường dẫn bằng chứng. Không đánh `Verified` cho FR chỉ từ PoC harness; RTM chỉ cập nhật khi có bằng chứng và task được giao.

Sau từng timebox: Go / Conditional Go / No-Go candidate, lý do và phép thử tiếp theo. No-Go model hoặc renderer **không tự cho phép bỏ yêu cầu A–G**, tăng ngân sách hay đổi kiến trúc. Kết thúc discovery bằng evidence review và ADR Proposed; chỉ Product Owner phê duyệt mới Accepted. **Hiện dừng ở planning, tất cả kết quả chưa đo.**
