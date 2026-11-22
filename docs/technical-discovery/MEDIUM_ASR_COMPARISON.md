# Vietnamese ASR Screening — Small vs Medium

Ngày: **22/11/2026 (Asia/Saigon)**. Scope: nhận dạng **audio-only** trên một bài Việt, benchmark CPU local có kiểm tra cùng cấu hình. Chưa chốt model mặc định hoặc nghiệm thu chất lượng tổng quát.

## 1. Kết luận

Trên mẫu `vi-001`, `medium` giảm WER **36.69% → 23.74%** và CER **25.19% → 15.56%**, đổi lại thời gian xử lý tăng **2.82 lần**. Cả hai run hoàn tất trong giới hạn tài nguyên của PoC. Đề xuất giữ medium làm **ứng viên tiếp tục đánh giá cho tiếng Việt**, vẫn bắt buộc review output.

Chưa đạt đủ bằng chứng Go cho quality gate: CER 15.56% vẫn cao hơn ngưỡng sàng lọc clean 15%; dữ liệu mới một bài exploratory, chưa được phân loại clean/rap/remix, chưa có held-out corpus hoặc phép đo thời gian sửa lời. Không suy WER thành accuracy người dùng, không đánh FR Verified.

## 2. So sánh có kiểm soát

- Cùng audio **296.681361s**, source SHA-256 `355a91a43c1cef6001a45dfdf8bea8a1d3fd109407f61ee6ed146de4c472fab8`.
- Cùng SRT gốc **68 cues**, reference SHA-256 `3c4bf2498c8ca51fa1219440465ac4ee2100cee271c887d3fb4a900c832aac99`.
- CPU `compute_type=int8`, **4 threads**, **beam 5**, VAD off, `condition_on_previous_text=False`, **seed 42**.
- Cùng thư viện ASR đã có; không cài dependency mới. Model medium được tải riêng, không ghi đè small.
- Reference chỉ dùng **sau inference** để chấm; `initial_prompt`, `prefix`, `hotwords` đều null. Không đưa lời có sẵn vào nhận dạng.
- Comparator xác minh source hash, time range, seed và toàn bộ decode-options giống nhau; không trộn baseline lịch sử không có explicit seed vào speed ratio.

Model small revision `536b0662742c02347bc0e980a01041f333bce120`; medium revision `08e178d48790749d25932bbc082711ddcfdfbc4f`. Medium artifact weights **1,527,906,378 bytes** trên disk, load với INT8. Inventory/checksums: [model-inventory-medium.json](../../.poc/evidence/poc-00/model-inventory-medium.json). [Nguồn model medium](https://huggingface.co/Systran/faster-whisper-medium).

## 3. Điểm nội dung

NFC/lowercase, punctuation/symbols thành khoảng trắng, collapse whitespace, **giữ dấu tiếng Việt**. WER theo units cách nhau bằng khoảng trắng, không phải từ ngữ nghĩa Việt; CER theo Unicode codepoints sau NFC và bỏ spaces. Giữ toàn bộ hypothesis, bao gồm text ngoài vùng có reference cues.

Reference: **556 units**, **1.806 ký tự không tính spaces**.

| Chỉ số | Small | Medium |
|---|---:|---:|
| WER | 36.69% | **23.74%** |
| CER | 25.19% | **15.56%** |
| Substitutions / deletions / insertions | 145 / 1 / 58 | 97 / 3 / 32 |
| Tổng edits theo units | 204 | 132 |
| Hypothesis units | 613 | 585 |
| ASR segments | 67 | 70 |

WER giảm **12.95 điểm phần trăm**, CER giảm **9.63 điểm phần trăm**. Lỗi tổng giảm nhưng deletions không giảm; số segment không là chỉ số accuracy. Các insertion có thể do hallucination/lặp hoặc khác biệt annotation, cần phân loại bằng nghe; chưa chứng minh medium xử lý instrumental an toàn.

## 4. Hiệu năng và tài nguyên

| Chỉ số một lượt đo | Small | Medium |
|---|---:|---:|
| Load model | 1.64s | 3.43s |
| Decode/inference/ghi partial | 139.27s | 392.56s |
| RTF theo toàn audio | 0.469 | 1.323 |
| Peak private process tree sampled | 2.98 GiB | 5.23 GiB |
| Min system available RAM | 5.83 GiB | 5.09 GiB |
| Abort / lỗi timestamp cấu trúc | Không / 0 | Không / 0 |

Private memory là metric workload Windows, không đồng nghĩa chỉ RAM vật lý của model. Monitor mỗi giây có thể bỏ sót peak ngắn. Không vượt ngưỡng dừng >12 GiB private hoặc available RAM <2 GiB liên tục 10s; không yêu cầu GPU rời.

Small lịch sử từng chạy khoảng 49.89s; run mới có explicit seed và điều kiện thực tế khác, nên không dùng lịch sử đó để tính speed ratio. Cặp mới chưa kiểm soát power/frequency/background load hoặc OS file cache; không quy kết nguyên nhân chênh lệch và không coi thời gian một lượt là SLA hay median cold/warm. Chưa đo ASR + alignment + render đồng thời.

## 5. Artifacts để review

| Artifact | Small | Medium |
|---|---|---|
| TXT nháp | [draft.txt](../../.poc/evidence/poc-01/vi-001-small-seeded/draft.txt) | [draft.txt](../../.poc/evidence/poc-01/vi-001-medium-seeded/draft.txt) |
| SRT nháp | [draft.srt](../../.poc/evidence/poc-01/vi-001-small-seeded/draft.srt) | [draft.srt](../../.poc/evidence/poc-01/vi-001-medium-seeded/draft.srt) |
| Raw run | [transcript.json](../../.poc/evidence/poc-01/vi-001-small-seeded/transcript.json) | [transcript.json](../../.poc/evidence/poc-01/vi-001-medium-seeded/transcript.json) |

Matched contract/metrics: [comparison.json](../../.poc/evidence/poc-01/vi-001-model-comparison/comparison.json).
Per-cue review: [lyric-review.tsv](../../.poc/evidence/poc-01/vi-001-model-comparison-reference/lyric-review.tsv).
Reproduce: [MODEL_COMPARISON.md](../../poc/lyrics/MODEL_COMPARISON.md).

Đã kiểm SRT nháp 67/70 cues: parse được, không overlap hoặc timestamp ngoài audio. Regression scorer/parser và syntax checks đạt; không thay reference bằng output model. Hash preview Việt đã được user duyệt vẫn khớp, preview không bị thay đổi.

## 6. Phần còn lại

Tiếp tục review lỗi medium, thêm bài Việt độc lập và đo correction time trước chọn model mặc định. Warm repeats, phân tầng thể loại, negative controls medium và held-out evaluation còn thiếu. Timestamp SRT nháp vẫn là ước lượng ASR, chưa forced alignment hoặc nghiệm thu timing.

Giữ cloud tắt, tiếng Anh tạm chưa tối ưu theo ưu tiên user. Các kết quả mới chưa commit/push; media/model/raw artifacts tiếp tục Git-ignored. Commit đề xuất: `test(lyrics): benchmark medium against small on Vietnamese audio`.
