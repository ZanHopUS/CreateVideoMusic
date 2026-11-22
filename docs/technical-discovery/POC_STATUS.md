# PoC Execution Status

## Authorization

Product Owner xác nhận ngày 22/11/2026 (Asia/Saigon): **“Đồng ý kế hoạch PoC, chỉ dùng local và dữ liệu có quyền sử dụng, mục đích cá nhân phi thương mại.”**

Phê duyệt cho phép setup môi trường PoC riêng, cài dependency/tải model cần thiết và chạy các phép thử local theo POC_PLAN, gồm faster-whisper small, WhisperX và Remotion/FFmpeg. Ngưỡng trong kế hoạch được dùng làm ngưỡng sàng lọc PoC; không trở thành cam kết release hoặc ADR Accepted. Cloud POC-06 không thực hiện. Không commit/push nếu chưa được yêu cầu.

Ghi nhận này cập nhật các ghi chú “chưa cho phép chạy PoC” trong tài liệu discovery trước đó. Không cấp quyền dùng file chưa rõ nguồn/license hoặc tự công bố kết quả có media cá nhân.

## Current execution

- POC-00: Environment smoke completed; corpus/ground truth readiness còn thiếu. Venv riêng, model small pin revision/hash, Remotion/browser đã chuẩn bị.
- POC-01: Initial runs completed — 12 generated negative-control runs và hai mẫu Việt/Anh user cung cấp, mỗi mẫu đối chứng VAD on/off. Việt (68 cues): WER 88.31% / 36.69%, CER 84.00% / 25.19%. Anh (111 cues, audio 0–300s): WER nguyên SRT 95.67% / 56.85%; loại 9 non-verbal cues trong phép đo bổ sung: 95.48% / 55.33%. Mỗi ngôn ngữ mới một mẫu exploratory, chưa có held-out corpus; chưa kết luận quality gate toàn bộ.
- POC-01 bổ sung: matched small/medium Việt, seed 42, CPU INT8/4 threads/VAD off — medium WER 23.74%, CER 15.56% so small 36.69%/25.19%; thời gian 392.56s vs 139.27s. Không vượt safety gates; CER vẫn trên mục tiêu clean 15%, chưa chốt model hoặc đánh quality gate Verified. Xem [MEDIUM_ASR_COMPARISON.md](MEDIUM_ASR_COMPARISON.md).
- POC-02: Initial full runs completed — Việt author loader 59/68 cue word draft, 9 fallback, coverage sàng lọc 98.02%; Anh 17/102 word draft, 85 fallback, coverage 60.78%. Đã sửa loader Việt bỏ qua feature_transform và giữ baseline đối chứng. Chưa có word-boundary gold hoặc timing review độc lập; không đánh quality gates Verified.
- POC-03: Initial smoke và 36-case preset matrix completed. Matrix 36/36 đạt video metadata/decode/markers, 24.300 frames không lỗi timestamp, peak private 1.143 GiB/min available 4.793 GiB. Video 15.000s nhưng AAC/container 15.019s: 18 bản 60FPS vượt ngưỡng container ≤1 frame; R1 đầy đủ còn mở. Xem [RENDER_MATRIX_RESULTS.md](RENDER_MATRIX_RESULTS.md). Interactive preview fidelity và fixtures trim/rate/VFR/transition chưa chạy.
- Preview Việt 33.9s dùng audio/lyrics/timing thật (6 word cues + 1 sentence fallback): đã kiểm 1.017 frames, metadata, visual state và audio crop correlation; user xác nhận **“đạt” ngày 22/11/2026** cho đúng preview này. File giữ nguyên hash sau matrix; chưa có word timing annotation độc lập.
- POC-04/05/07: Pending — chưa chạy stress/editor/storage/Drive/segment suggestions.
- POC-06: Excluded — local only.

Artifacts tải về, môi trường, media và raw evidence đặt dưới `.poc/`, được ignore khỏi Git. Script PoC có thể nằm trong `poc/`; không phải application code chính thức.

Chi tiết smoke ban đầu: [POC_INITIAL_RESULTS.md](POC_INITIAL_RESULTS.md). Kết quả mới sau khi nhận SRT và quy tắc hai luồng đầu vào: [LYRICS_INPUT_WORKFLOW.md](LYRICS_INPUT_WORKFLOW.md).

Kết quả mẫu Anh, annotation caveat và phạm vi xử lý: [ENGLISH_ASR_RESULTS.md](ENGLISH_ASR_RESULTS.md).

Kết quả alignment, loader compatibility fix và file word/sentence drafts: [ALIGNMENT_POC_RESULTS.md](ALIGNMENT_POC_RESULTS.md).

Video để nghe rà soát: [VIETNAMESE_LYRICS_PREVIEW.md](VIETNAMESE_LYRICS_PREVIEW.md). Theo steering của user, hiện ưu tiên tiếng Việt; tối ưu mẫu Anh tạm hoãn.

Đã có commit baseline discovery/PoC `df5efd3` trên `dev`, chưa push. Các thay đổi reference evaluation, alignment, preview, benchmark medium và render matrix mới chưa commit/push; chưa chọn stack chính thức hoặc đánh FR Verified.
