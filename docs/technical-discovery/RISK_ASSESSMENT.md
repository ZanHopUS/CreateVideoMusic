# Risk Assessment

Ngày: **22/11/2026 (Asia/Saigon)**. Trạng thái: **đánh giá trước PoC**, không có kết quả benchmark hoặc rủi ro đã được đóng. Owner vai trò: **PO** = Product Owner, **AI** = người thực hiện Lyrics PoC, **Media** = người thực hiện rendering, **Storage** = người thực hiện storage; chưa phân công cá nhân.

**Cập nhật xác nhận 22/11/2026:** Các định hướng/điều kiện trong [OPEN_QUESTIONS.md](../../OPEN_QUESTIONS.md) đã được Product Owner xác nhận. Việc đó giải quyết trạng thái phê duyệt định hướng, không đóng rủi ro thực nghiệm hoặc cấp quyền bắt đầu PoC. Các chi tiết kỹ thuật/ngưỡng/license và phần TD ngoài phạm vi xác nhận vẫn cần phê duyệt; các bảng bên dưới phải được đọc cùng cập nhật này.

## 1. Cách đánh giá

**Cập nhật sau các lượt PoC:** bảng dưới là baseline rủi ro trước thử nghiệm;
trạng thái hiện tại xem [POC_STATUS.md](POC_STATUS.md). Medium giảm lỗi trên một
bài Việt nhưng chưa có held-out/correction time; loader alignment Việt đã sửa
nhưng coverage chưa chứng minh timing đúng. [Matrix render](RENDER_MATRIX_RESULTS.md)
đạt video/decode/markers 36/36, còn đuôi audio/container 19ms khiến 60FPS vượt
ngưỡng container ≤1 frame; stress 300s và interactive fidelity chưa chạy.
R-01/02/08/09/10/19 tiếp tục mở; chưa đóng rủi ro bằng smoke hẹp.

**Follow-up sau checkpoint:** [Audio duration](AUDIO_DURATION_RESULTS.md) đạt
36/36 trên bản sao encode lại AAC; [stress đầu tiên](RENDER_STRESS_RESULTS.md)
đạt video 300s/1080p60 dọc, RTF 3.477 và các marker/tail checks. Audio workaround
chưa listening review; stress còn 4 outputs và UI/fidelity/lifecycle chưa thử.
Rủi ro còn mở, không coi một lượt harness là release acceptance.

**Cập nhật 23/11/2026:** [đủ năm stress outputs](RENDER_STRESS_SUITE_RESULTS.md)
đã qua validation: 90.000 frames, 0 lỗi timestamp, final duration 300s và tail checks
đạt; render RTF 2.378–3.477, sampled RAM trong gates. Phần render/resource screening
có thêm bằng chứng; R-08/09/10 vẫn mở cho concurrency/UI, fidelity, media rộng hơn
và repetitions. Không đóng toàn bộ POC-04 từ các generated fixtures.

Likelihood (L): 1 thấp, 2 vừa, 3 cao. Impact (I): 1 cục bộ, 2 ảnh hưởng workflow, 3 mất dữ liệu/privacy/budget hoặc chặn yêu cầu Core. Score = L×I: 1–2 thấp, 3–4 vừa, 6–9 cao. Đây là ước lượng định tính để ưu tiên, không phải xác suất đã đo. Cột “đóng” là điều kiện cần; mọi hàng hiện **Open** và residual risk sẽ đánh giá lại sau evidence.

## 2. Sổ rủi ro

| ID / L×I | Rủi ro và tín hiệu cần quan sát | Giảm thiểu / thử nghiệm | Điều kiện đóng hoặc escalation | Owner |
|---|---|---|---|---|
| R-01 / 3×3=9 | Speech ASR sai trên hát Việt/Anh; WER/CER cao, sửa còn lâu hơn nhập tay | POC-01 theo ngôn ngữ/thể loại, small→medium có điều kiện | L1/L6 đạt trên held-out; fail cả hai thì trình PO, không bỏ FR-201 | AI + PO |
| R-02 / 3×3=9 | Timing từ sai do luyến âm, OOV, sai transcript | POC-02 ground-truth text độc lập; kiểm coverage và onset/end; sentence fallback | L2 đạt hoặc Conditional Go câu qua L3 được PO duyệt; word mode vẫn ghi chưa đạt | AI |
| R-03 / 3×3=9 | Hallucinated lyrics trên instrumental/silence hoặc VAD bỏ sót hát | Negative controls, review bắt buộc, không auto-apply | L5 đạt, false text/missed-vocal báo riêng; còn tự áp dụng sai thì No-Go | AI |
| R-04 / 3×2=6 | Rap/remix/overlap/code-switch suy giảm không đều | Đo từng nhóm, không average che lỗi; có manual/import fallback | PO duyệt giới hạn dựa trên L4 và bằng chứng, không tuyên bố chất lượng chung | AI + PO |
| R-05 / 2×3=6 | Aligner Việt mặc định có NC license; mục đích sử dụng thay đổi | Inventory model weights/license/revision/attribution trước tải; tìm thay thế nếu cần | PO xác định mục đích phù hợp hoặc có model thay thế được kiểm chứng; không coi miễn phí là permissive | AI + PO |
| R-06 / 3×2=6 | Tách vocal chậm, artifact làm ASR tệ hơn; upstream archive | POC-01 A/B nhỏ, không bật mặc định, ghi maintenance | Chỉ chọn nếu delta chất lượng và R0/L6 đạt; không có lợi thì bỏ nhánh separation, giữ yêu cầu lyrics | AI |
| R-07 / 3×3=9 | Python/native libs/driver/browser xung đột trên Windows | POC-00 pin versions, CPU-only, thử startup và offline; tách env | Startup/inference/render thực trên máy đích; tài liệu upstream không đủ đóng | AI + Media |
| R-08 / 3×3=9 | 16 GB không đủ khi model/browser/renderer cùng chạy | Tổng process tree, tuần tự jobs, threads/concurrency/cache giới hạn; unload model | R0 đạt, UI còn đáp ứng; OOM/repeated thrashing thì dừng và thiết kế lại scheduler | Media + AI |
| R-09 / 2×3=6 | Preview/export lệch do hai implementation, fps rounding, VFR, font | Composition/timeline chung, marker AV và boundary frames POC-03 | R2 đạt ở đầu/giữa/cuối và các rate, không gán lỗi này cho ASR | Media |
| R-10 / 2×3=6 | Preset MP4 sai, thiếu audio/codec hoặc 300s quá chậm | 36 smoke, 5 stress fixtures, ffprobe + decode + xem/nghe | R1/R3 đạt; không âm thầm giảm 1080p60 hoặc ratios | Media + PO |
| R-11 / 2×3=6 | Disk temp lớn, cancel treo, output nửa file báo thành công | Resource sampling, disposable quota test, state machine/progress/cancel/retry | R4 và disk error tests đạt, partial output không được publish thành complete | Media |
| R-12 / 2×3=6 | Save/crash/GC mất project hoặc shared assets | Immutable revisions, pin assets, stage/validate/publish; fault injection | POC-05 không corrupt save, không xóa pinned/shared source; mất dữ liệu là No-Go | Storage |
| R-13 / 3×3=9 | Drive sync live DB/partial package/conflict; báo backup thành công giả | Runtime ngoài Drive, immutable package, round-trip verify, không tự merge | ST-03 chỉ đóng sau sync-download-restore thật; copy local không đủ | Storage + PO |
| R-14 / 2×3=6 | Local service bị trang web khác gọi, path traversal/reparse escape hoặc shell injection | Loopback + Origin/Host + capabilities, validate canonical path, argv trực tiếp, untrusted package validation | SEC tests từ origin sai và path escape bị chặn; no-login không miễn authorization | Storage |
| R-15 / 2×3=6 | Gemini Free dùng dữ liệu riêng tư hoặc vượt quota/billing ngoài ý muốn | Provider tắt; synthetic-only opt-in, kiểm tier/quota/data terms, không paid fallback | Consent và account evidence trước POC-06; không có thì Deferred | PO |
| R-16 / 2×3=6 | Tưởng ChatGPT subscription là API free; OpenAI phát sinh phí | Không dùng API khi budget/credits chưa xác minh; không auto-recharge | PO duyệt budget riêng hoặc giữ tắt; local Core không phụ thuộc | PO |
| R-17 / 2×3=6 | Remotion/model/FFmpeg/font/media license không phù hợp khi phân phối | Inventory đúng version/build và phạm vi dùng; không dùng paid starter mặc định | Eligibility/license evidence trước chọn/phân phối; thay mục đích thì review lại | PO + Media |
| R-18 / 3×2=6 | Baseline đường dẫn sai, AC mơ hồ, proposal bị coi Accepted | GAP log, liên kết root, TD decision log; không sửa A–G | PO duyệt layout/AC/ADR riêng; mỗi quyết định có trạng thái rõ | PO |
| R-19 / 3×2=6 | Dataset ít, annotation lệch, leakage cùng bài, metrics đẹp giả | Source-group split, held-out freeze, report strata, 20% independent review | Đủ manifest/annotations; thiếu người review thì hạ độ mạnh kết luận, không tuyên bố tổng quát | AI + PO |
| R-20 / 2×2=4 | Template reuse làm thay đổi template gốc, undo giữ thiếu state | Clone IDs, schema versions, canonical snapshot semantic tests | R5 + round-trip restore giữ state, không mutation shared template | Media + Storage |
| R-21 / 2×2=4 | “Gợi ý đoạn hay” chỉ dựa energy, không hữu ích | POC-07 user rating, so manual selection, fallback trim | IT-13/PO acceptance dựa trên evidence; không gọi heuristics là AI hiểu bài | AI + PO |
| R-22 / 2×3=6 | Lệch timestamp do nhầm sped-up source với editor rate | Lưu timebase/provenance, round-trip trim/itemStart/rate, test lặp/overlap | POC-02/03 không timestamp ngoài clip hoặc drift; tách lỗi source map khỏi aligner | AI + Media |

## 3. Nguồn xác lập các rủi ro bên ngoài

- WhisperX ghi hạn chế overlapping speech và dictionary; source hiện có mapping Vietnamese nhưng model card công bố CC BY-NC 4.0. Điều đó làm R-02/04/05 thành câu hỏi thực tế, chưa chứng minh mức sai trên hát. [WhisperX](https://github.com/m-bain/whisperX), [aligner Việt](https://huggingface.co/nguyenvulebinh/wav2vec2-base-vi-vlsp2020).
- Demucs repo gốc được archive; CPU mode không chứng minh đủ nhanh. [Demucs](https://github.com/facebookresearch/demucs).
- SQLite có WAL sidecars, Backup API tạo DB snapshot; Drive stream/mirror không cung cấp snapshot transaction cho project nhiều file. [SQLite WAL](https://sqlite.org/wal.html), [SQLite Backup](https://sqlite.org/backup.html), [Drive desktop](https://support.google.com/drive/answer/13401938).
- Gemini terms/pricing có phân biệt unpaid/paid data-use; OpenAI data retention thay đổi theo endpoint. Không suy luận toàn bộ cloud “riêng tư” hoặc “miễn phí”. [Gemini terms](https://ai.google.dev/gemini-api/terms), [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data).
- Remotion license có eligibility, FFmpeg license phụ thuộc thành phần build. Cần đọc đúng artifact trước phân phối, không coi stack đã được duyệt. [Remotion licensing](https://www.remotion.dev/pricing), [FFmpeg licensing](https://ffmpeg.org/legal.html).

## 4. Liên kết toàn bộ Open Questions tới hành động

Tên `AI-01/02/03` cũng xuất hiện như test IDs trong SRS. Bảng này dùng **Open Question ID**; kết quả PoC phải ghi rõ namespace để không nhầm câu hỏi với test.

| Open Question | Nơi xử lý | Kết quả cần / gate |
|---|---|---|
| AI-01 | AI_PROVIDER_COMPARISON; POC-06 | Free quota/model/account + terms + user consent; chưa có thì tắt |
| AI-02 | AI_PROVIDER_COMPARISON; TD-06 | Budget/credit eligibility; không suy từ Plus |
| AI-03 | POC-01, R-01/07/08 | WER/CER/correction time/RTF/RAM trên máy đích |
| AI-04 | POC-02, R-02/22 | Timing coverage/error Việt/Anh, fallback câu đã đo |
| AI-05 | POC-01 A/B, R-06 | Delta chất lượng vs cost và maintenance |
| AI-06 | Provider consent proposal, R-15 | Data categories/provider/revoke/log retention được duyệt |
| ST-01 | STORAGE_STRATEGY; POC-05 | JSON vs SQLite và portable package evidence |
| ST-02 | POC-05 security/permission | Folder selection workflow và backend capability validation |
| ST-03 | POC-05 Drive round-trip | Package restore sau sync thật, không live DB |
| ST-04 | POC-04/05 resources | Cache/temp quotas, preflight, recovery retention và GC consent |
| MED-01 | TECHNICAL_ASSESSMENT scope | Giữ upload/library trong Core; URL adapter Later, không nghiên cứu downloader |
| MED-02 | POC-00 dataset/license inventory | Media/lyrics/font/model có quyền dùng đúng mục đích |
| MED-03 | POC-07 | Metadata/heuristics usefulness vs manual; không giả định mood analysis |
| MED-04 | POC-00/03/04 | Codec/VFR/input caps/concurrency sau measurement |
| UX-01 | POC-04 harness | 4 track types/12 và 100 items chỉ là fixtures; PO chốt Core detail |
| UX-02 | Template contract ở assessment, R-20 | Save/reuse contract trước, blank builder UI Complete; acceptance chi tiết cần task planning sau |
| ARC-01 | Deferred tới Later | Không chọn Local Agent/cloud render hoặc triển khai Vercel trong discovery |
| ACC-01 | POC_PLAN gate tables, TD-02 | User duyệt ngưỡng sàng lọc; benchmark xong mới khóa release thresholds |

## 5. Quy tắc dừng và quyết định phê duyệt

Không chạy PoC trước TD-01/02 và các approval liên quan. Khi đã được phép thử: dừng run nếu thiếu quyền dùng dữ liệu, có outbound trái consent, có chi phí không được duyệt, mất dữ liệu hoặc vượt resource safety gate. Dùng bản sao disposable cho fault tests; không tác động manual project thật.

No-Go là kết luận về **candidate/configuration**, không tự giảm yêu cầu sản phẩm. Word alignment fail chỉ mở đường Conditional Go sentence mode khi câu đạt và PO chấp nhận; local ASR fail không biến manual-only thành Core hoàn thành. Rendering fail không cho bỏ một preset E. Storage mất dữ liệu chặn chọn phương án, không coi khả năng “retry được” là đủ.

Trước bước tiếp theo cần PO duyệt: TD-01 phạm vi/cài tải PoC, TD-02 corpus/annotations/ngưỡng, TD-03 model/license, TD-04 rendering matrix, TD-05 storage experiments. TD-06 cloud tiếp tục tắt nếu không có opt-in riêng; TD-07 layout baseline là thay đổi tài liệu riêng. Sau evidence review mới đề nghị ADR; chưa có ADR Accepted, commit/push hoặc thử nghiệm nào được cấp phép bởi báo cáo này.
