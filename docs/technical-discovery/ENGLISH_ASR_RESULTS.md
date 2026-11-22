# English ASR Exploratory Results

Ngày: **22/11/2026 (Asia/Saigon)**. Scope: một mẫu tiếng Anh do user cung cấp, so baseline ASR CPU với SRT; chưa chạy forced alignment hoặc nghiệm thu quality gate.

## 1. Dữ liệu và phạm vi xử lý

Sample `en-001`: AAC stereo 44.1kHz, **301.418231s**, 4,878,966 bytes. Audio và SRT được copy vào `.poc/data/user/`, không sửa file Downloads, không đưa lyrics/media vào Git.

- Audio SHA-256: `7f63317b31f2bb182b2fd1c7efa0072829ab3f681d76d5779fe61172ba934e47`.
- Reference SRT SHA-256: `5d96027ea329646f237f58520eea56a9287f64cad1abc97d53ab69bef45002a8`.
- SRT có **111 cues**, **0.389–286.811s**; parser không phát hiện lỗi cấu trúc, overlap hoặc timestamp ngoài audio.
- Xử lý **0–300s**, không tính 1.418231s cuối. Tất cả reference cues nằm trong vùng xử lý; không cắt mất cue để chấm điểm. Mốc này là phạm vi thí nghiệm, không bổ sung giới hạn upload của sản phẩm.
- Với `--max-seconds 300`, decode local về mono 16kHz rồi lấy 300s đầu trước ASR. Cùng đầu vào cho hai cấu hình; không dùng clip_timestamps làm vô hiệu VAD trong so sánh.

Đây là development/exploratory sample, không là held-out corpus. Reference có cả lời nói trong MV, lyrics và mô tả âm thanh; không gọi toàn bộ SRT là lyric-only ground truth. Timing user cung cấp chưa được kiểm chứng bằng annotation độc lập; chưa có word-boundary gold.

## 2. Cấu hình

Giữ model/revision và dependency baseline ở [POC_INITIAL_RESULTS.md](POC_INITIAL_RESULTS.md): faster-whisper 1.2.1, multilingual small, CPU INT8, 4 threads, beam 5, `condition_on_previous_text=False`, không word timestamps. Hai lượt chạy tuần tự, chỉ thay `vad_filter`; không cài thêm dependency hoặc cloud inference.

| Run | Audio còn sau VAD | Số đoạn | Load model | Decode/inference/ghi partial | RTF theo 300s |
|---|---:|---:|---:|---:|---:|
| VAD on | 14.912s | 5 | 0.93s | 7.11s | 0.0237 |
| VAD off | Không cắt bởi VAD | 65 | 0.81s | 236.12s | 0.7871 |

Đây là một lượt/config, chưa phải median cold/warm. RTF VAD-on thấp không thể coi là tốc độ xử lý đầy đủ khi gần 95% thời lượng không đi vào ASR. Không dùng thời gian run để dự đoán tốc độ trên bài khác hoặc checkpoint lớn hơn.

## 3. Text error so SRT nguyên bản

Giữ đúng phương pháp mẫu Việt: NFC/lowercase, punctuation/symbols thành khoảng trắng, collapse whitespace, giữ dấu; WER theo đơn vị cách bằng khoảng trắng; CER bỏ spaces. So toàn text ASR của 300s với toàn text reference, không dựa vào số thứ tự segment/cue. Reference **577 units**, **2.093 ký tự không tính spaces**.

| Run | Units ASR | Substitution / deletion / insertion | WER | CER |
|---|---:|---:|---:|---:|
| VAD on | 37 | 6 / 543 / 3 | **95.67%** | **93.98%** |
| VAD off | 465 | 196 / 122 / 10 | **56.85%** | **49.16%** |

SRT có **9 cue mô tả âm thanh không chứa lời chép cụ thể**, được kiểm tra trực tiếp: IDs **1, 2, 6, 9, 11, 12, 107, 108, 111**. ASR không phải sound-event captioner nên chấm các mô tả đó như spoken words làm lẫn mục tiêu. Giữ bảng nguyên bản để minh bạch, đồng thời có phép đo bổ sung loại đúng chín cue đã phân loại, không tự xóa mọi nội dung trong ngoặc.

## 4. Phép đo bổ sung trên reference có lời nói/lyrics

Reference sau loại mô tả còn **553 units**, **1.934 ký tự không tính spaces**; hypothesis không cắt hoặc sửa. Vẫn gồm dialogue và singing, chưa phải riêng lyrics.

| Run | Substitution / deletion / insertion | WER bổ sung | CER bổ sung |
|---|---:|---:|---:|
| VAD on | 6 / 519 / 3 | **95.48%** | **93.49%** |
| VAD off | 196 / 99 / 11 | **55.33%** | **45.76%** |

Không loại cùng kiểu ngoặc ở mẫu Việt: hai cue đầu của reference Việt có lời hát trong ngoặc. Việc loại cue chỉ áp dụng danh sách được phân loại cho mẫu Anh; không dùng để làm đẹp điểm hoặc thay bảng chính.

## 5. Tài nguyên và timing

| Run | Sampled peak private process tree | Min system available | Abort / lỗi timestamp cấu trúc |
|---|---:|---:|---|
| VAD on | 2.96 GiB | 3.28 GiB | Không / 0 |
| VAD off | 3.39 GiB | 2.65 GiB | Không / 0 |

Monitor mỗi giây, có thể bỏ sót peak ngắn; không vượt điều kiện dừng trong hai run này. Không có segment ngoài vùng 300s hoặc overlap theo kiểm tra cấu trúc. Chưa đo sentence/word MAE/P95, correction time hoặc nhận dạng nhạc instrumental. Timestamp không lỗi cấu trúc không đồng nghĩa lyric sync đúng.

## 6. Kết luận và hành động

Trên cả hai mẫu Việt/Anh đã thử, VAD mặc định giữ rất ít audio và text error cao; không đủ cơ sở chọn cấu hình đó cho lyrics. VAD-off ít lỗi hơn trên hai mẫu, nhưng vẫn vượt ngưỡng sàng lọc clean được đề xuất. Các mẫu chưa được phân loại sạch và chưa là held-out nên **không kết luận chất lượng chung cho ngôn ngữ, không đánh L1 hoặc FR Verified**.

Baseline small hiện chưa đủ bằng chứng đạt chất lượng lyrics. Cần rà lỗi theo nhóm (mất lời/sai chữ/dialogue/annotation), thử alignment với text reference đã có, rồi cân nhắc medium/VAD tuning/separation theo tài nguyên và plan đã duyệt. Không tự đổi kiến trúc hoặc yêu cầu phải có lời sẵn; luồng audio-only vẫn cần ASR + review/fallback.

Bằng chứng private:

- [VAD-off draft TXT](../../.poc/evidence/poc-01/en-001-no-vad/draft.txt), [draft SRT](../../.poc/evidence/poc-01/en-001-no-vad/draft.srt).
- [VAD-on draft TXT](../../.poc/evidence/poc-01/en-001/draft.txt).
- [Evaluation JSON](../../.poc/evidence/poc-01/en-001-reference-evaluation/evaluation.json): giữ cả điểm nguyên bản và supplementary exclusion.
- [Bảng đối chiếu theo cue](../../.poc/evidence/poc-01/en-001-reference-evaluation/lyric-review.tsv): overlap theo thời gian hỗ trợ review, không là word alignment.
- [VAD-on resources](../../.poc/evidence/poc-01/en-001/resources/resources.json), [VAD-off resources](../../.poc/evidence/poc-01/en-001-no-vad/resources/resources.json).

Harness evaluator đã hỗ trợ `--sample`, giữ cách chấm Việt và kiểm lại ra đúng điểm trước đó. Thêm guard không chấm reference vượt phần audio xử lý; regression parser/edit distance và syntax checks đạt. File tham chiếu được dùng như dữ liệu, không thực thi nội dung. Thay đổi mới chưa commit/push.
