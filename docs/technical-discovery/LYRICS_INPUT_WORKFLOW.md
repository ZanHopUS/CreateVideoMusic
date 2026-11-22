# Lyrics Input Workflow and Reference Evaluation

Ngày cập nhật: **22/11/2026 (Asia/Saigon)**. Phạm vi: làm rõ yêu cầu đã có và đánh giá PoC; chưa xây editor/pipeline chính thức.

## 1. Xác nhận cách nhận lời

Người dùng cung cấp SRT lời gốc cho mẫu `vi-001`, đồng thời xác nhận: sau này có lời sẵn sẽ gửi cùng audio; không có lời thì hệ thống vẫn phải tự nhận dạng/chép lời từ audio.

Đây là hai đường vào đã nằm trong PRD nhóm C và SRS **FR-201–204**, không thay đổi A–G hoặc thêm tính năng sáng tác lyrics mới.

| Đầu vào | Hành vi cần có | Trạng thái cần phân biệt |
|---|---|---|
| Audio + SRT/LRC | Import text/timing, validate định dạng và source timebase; cho user rà soát | Timing do user cung cấp, chưa mặc định đúng hoặc chính xác từng từ |
| Audio + lời text chưa có timing | Dùng text được cung cấp cho alignment, giữ nguyên bản gốc; user duyệt khác biệt | Text reference và aligned draft tách riêng |
| Chỉ audio | ASR local nhận dạng/chép lời, tạo bản nháp để review; sau đó alignment/fallback câu | ASR-generated draft, không phải ground truth |
| Instrumental/không rõ lời | Báo giới hạn, đánh dấu đoạn nghi ngờ, cho sửa/nhập/import; không tự sáng tác lời | Unknown/no-vocal suspected cần review, không coi confidence là bảo đảm |

Không tự ghi đè lời user bằng ASR; nếu chạy ASR đối chứng thì giữ kết quả riêng. Import SRT/LRC không bắt buộc phải chạy ASR lại. Nếu cần word highlighting, thử căn từ trên text được duyệt; không chia đều thời gian câu thành từ rồi coi là forced alignment.

Giữ provenance cho text và timing: source/hash, phương thức nhập, model/revision/config nếu có, timebase audio, manual edits, review status. Audio trim/rate cần map timestamp về timeline theo BR-05. Import hợp lệ về cú pháp không đồng nghĩa lyric timing đã được nghiệm thu.

## 2. File tham chiếu thực tế

- Source: SRT được user gửi dưới tên chứa cùng video ID với mẫu audio; copy cục bộ thành `.poc/data/user/vi-001.reference.srt`. Không sửa file Downloads.
- SHA-256: `3c4bf2498c8ca51fa1219440465ac4ee2100cee271c887d3fb4a900c832aac99`.
- **68 cues**, từ **27.050s** đến **268.681s**, nằm trong audio **296.681361s**.
- Parser kiểm ID, timestamp, thứ tự, duration, overlap và giới hạn audio: không phát hiện lỗi/cảnh báo trên file này.
- Text được dùng làm **user-provided reference** theo xác nhận “lời gốc”; chưa có review độc lập. Sentence timestamps được cung cấp, chưa có word-level annotations hoặc kiểm chứng bằng nghe.

## 3. Phương pháp tính lỗi nội dung

Đối chiếu toàn bộ text ASR của cả recording với toàn bộ lời trong SRT, không dựa trên segment boundaries. Chuẩn hóa Unicode NFC/lowercase, punctuation/symbols thành khoảng trắng, collapse whitespace và **giữ dấu tiếng Việt**.

Đơn vị WER là token cách nhau bằng khoảng trắng, không phải từ ngữ nghĩa tiếng Việt. CER tính Unicode codepoint sau NFC và bỏ khoảng trắng. Edit distance dùng substitutions/deletions/insertions; tổng lỗi có thể lớn hơn số reference units ở các tình huống khác, không diễn giải `1-WER` như accuracy tổng quát.

Reference có **556 whitespace units**, **1.806 ký tự không tính khoảng trắng**. So sánh toàn recording giữ cả phần text ASR ngoài vùng có phụ đề, nên insertions có thể đến từ hallucination, vocalizations không được SRT chép hoặc khác biệt annotation; chưa phân loại bằng nghe. Không tự cắt hypothesis để làm đẹp điểm.

## 4. Kết quả đối chứng

| Run | Units ASR | Substitutions / deletions / insertions | WER theo whitespace units | CER giữ dấu, bỏ spaces |
|---|---:|---:|---:|---:|
| VAD on | 110 | 45 / 446 / 0 | **88.31%** | **84.00%** |
| VAD off | 613 | 145 / 1 / 58 | **36.69%** | **25.19%** |

VAD-off có ít lỗi nội dung hơn VAD-on trên phép đo/mẫu này. Mức lỗi vẫn cao hơn ngưỡng sàng lọc clean được đề xuất trong POC_PLAN (WER 30%, CER 15%), nhưng mẫu này **chưa được phân loại clean/rap/remix và chưa thuộc held-out corpus**. Vì vậy không kết luận gate L1 toàn bộ thất bại hoặc một cấu hình đã được chốt. Cần error review và thêm dữ liệu độc lập; kết quả này cũng chưa chứng minh forced alignment đạt.

Timestamps ASR khác segmentation của SRT: không lấy cue số 1 so với segment số 1 để tính timing error. Chưa tính word/sentence MAE/P95, correction time, hay điểm tiếng Anh. Không đổi transcript cũ thành “đã review” chỉ vì đã nhận file tham chiếu.

## 5. Bằng chứng và kiểm tra

- [evaluation.json](../../.poc/evidence/poc-01/vi-001-reference-evaluation/evaluation.json): cấu hình normalize, hash reference, raw text và edit counts từng run.
- [lyric-review.tsv](../../.poc/evidence/poc-01/vi-001-reference-evaluation/lyric-review.tsv): từng cue reference, text ASR trùng vùng thời gian, cột sửa lời/review timing. Đây là công cụ rà soát, không phải alignment đối chiếu token tự động; ASR timing sai có thể làm text ở cột đối chiếu lệch câu hoặc bị lặp ở nhiều hàng.
- [reference.txt](../../.poc/evidence/poc-01/vi-001-reference-evaluation/reference.txt): lời trích từ SRT, giữ trong vùng private.
- Harness [evaluate.py](../../poc/lyrics/evaluate.py): kiểm thử regression edit counts, chuẩn hóa Unicode/dấu Việt, SRT BOM/CRLF/multiline/tags và timestamp đảo ngược đã đạt. Không thêm dependency.

Media, lời bài hát, reference và raw evaluation tiếp tục nằm trong `.poc/`, được ignore khỏi Git. Báo cáo chỉ lưu số liệu; chưa commit/push thay đổi của lượt này.

## 6. Tiếp theo

Dùng bản text user cung cấp cho PoC alignment, giữ timing SRT như reference câu cần kiểm chứng thay vì word-level gold. Review lỗi ASR và các cue nghi ngờ trước khi kết luận word timing; mở rộng corpus/held-out theo kế hoạch. Luồng thiếu lyrics vẫn phải ASR local + review + alignment/fallback, không trở thành yêu cầu “luôn phải có lời sẵn”.

Đã nhận và thử mẫu Anh cùng SRT; xem [ENGLISH_ASR_RESULTS.md](ENGLISH_ASR_RESULTS.md). Reference Anh có non-verbal annotations nên báo cả so sánh nguyên bản và phép đo bổ sung đã phân loại cue, không tự áp dụng quy tắc xóa ngoặc cho lời Việt.
