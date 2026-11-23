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
- POC-03: Initial smoke và 36-case preset matrix completed. Matrix 36/36 đạt video metadata/decode/markers, 24.300 frames không lỗi timestamp, peak private 1.143 GiB/min available 4.793 GiB. Video 15.000s nhưng AAC/container 15.019s: 18 bản 60FPS vượt ngưỡng container ≤1 frame; R1 đầy đủ còn mở. Xem [RENDER_MATRIX_RESULTS.md](RENDER_MATRIX_RESULTS.md). Fidelity/trim/rate/VFR follow-up được ghi riêng bên dưới.
- Preview Việt 33.9s dùng audio/lyrics/timing thật (6 word cues + 1 sentence fallback): đã kiểm 1.017 frames, metadata, visual state và audio crop correlation; user xác nhận **“đạt” ngày 22/11/2026** cho đúng preview này. File giữ nguyên hash sau matrix; chưa có word timing annotation độc lập.
- POC-03 duration follow-up: 36 bản sao bounded-audio đạt cả duration container ≤1 frame; copy video payload giữ nguyên, AAC encode lại. Chưa listening review hoặc chốt production pipeline. Xem [AUDIO_DURATION_RESULTS.md](AUDIO_DURATION_RESULTS.md).
- POC-04 render screening completed, cập nhật 23/11/2026 — đã đủ 5/5 output 300s/1080p60 (TPL01/02 dọc, TPL03 dọc/ngang/vuông). 90.000 frames, 0 timestamp errors; final duration 300.000s, AV markers và tail checks đạt ở mọi file. Render RTF 2.378–3.477; peak private toàn bộ các lượt 2.111 GiB/min available 3.844 GiB. Đạt render-time/resource subgates trong scope fixture; UI/fidelity/lifecycle/listening và repetitions chưa nghiệm thu toàn bộ. Xem [RENDER_STRESS_SUITE_RESULTS.md](RENDER_STRESS_SUITE_RESULTS.md).
- Bốn mẫu mới đã chạy tuần tự và qua validation trong 56 phút 42 giây; source snapshots và 10 raw/bounded output hashes đã xác minh. Có năm bản xem 20s/540px/30FPS tạo sau benchmark; không thay bản 300s/1080p60.
- POC-03/04 fidelity follow-up 23/11: Remotion Player thật so PNG/MP4 tại 27 mốc mỗi project 12 items. TPL01/02 baseline 27/27 đạt; direct VFR TPL03 fail 3/27 (210/240/300), CFR proxy đơn thuần chưa sửa được. Candidate seek-nudge 10µs, default off, đạt 27/27 TPL03 + export/AV checks trong lượt riêng. Không chốt production policy hoặc đóng R2. Xem [PREVIEW_RENDER_FIDELITY_RESULTS.md](PREVIEW_RENDER_FIDELITY_RESULTS.md).
- Player harness: 100 seeks/project P95 49.61/49.70/66.41ms; 60s simple playback ≈29.997 frameupdate events/s, chưa phải compositor FPS hoặc UI latency nghiệm thu. Audio EOF 11ms tại 1.25× đã có pad/trim candidate, regression tail 300s đạt.
- POC-04 lifecycle: API-only cancel ~15ms nhưng worker exit ~30s không đạt. Supervisor candidate dọn owned PID tree ~2.063s, retry/immutable snapshot/publish-last checks đạt; chưa thử cancel finalize/crash/disk-full, undo/reuse hoặc editor thực. Xem [JOB_LIFECYCLE_RESULTS.md](JOB_LIFECYCLE_RESULTS.md).
- POC-04 state/template follow-up 23/11: 6 fixtures ×50 edits/undo/redo (300 mỗi loại) khớp state; dirty/history/template isolation và 6 valid bindings đạt. Sửa catalog guard chặn 6 wrong-MIME bindings. Model harness chưa là editor UI. Xem [STATE_TEMPLATE_POC_RESULTS.md](STATE_TEMPLATE_POC_RESULTS.md).
- POC-05 local: 32 functional checks đạt, gồm 24 process-crash runs/12 phases và 10 portable restores; lặp cùng fixtures trong thư mục mới cũng đạt. SQLite FULL thực, file ENOSPC injected, Windows file lock và independent recovery được kiểm. Chưa thử power loss/Drive hoặc chốt schema/driver/container. Xem [STORAGE_RECOVERY_POC_RESULTS.md](STORAGE_RECOVERY_POC_RESULTS.md).
- Render từ storage restore: 2 MP4/720 frames và 6 cặp PNG đạt chức năng. **R0 chưa đạt**: concurrency 2 min available 1.850 GiB; concurrency 1 bị dừng dưới 2 GiB liên tục 10s (min 1.651 GiB). Storage repeat cũng có sample 1.992 GiB. Chưa kết luận toàn bộ POC-05/Core Go; cần đủ headroom trước thử render nặng tiếp.
- POC-07: Pending — segment suggestions chưa chạy; editor UI và lifecycle coverage đầy đủ còn mở.
- POC-06: Excluded — local only.

Artifacts tải về, môi trường, media và raw evidence đặt dưới `.poc/`, được ignore khỏi Git. Script PoC có thể nằm trong `poc/`; không phải application code chính thức.

Chi tiết smoke ban đầu: [POC_INITIAL_RESULTS.md](POC_INITIAL_RESULTS.md). Kết quả mới sau khi nhận SRT và quy tắc hai luồng đầu vào: [LYRICS_INPUT_WORKFLOW.md](LYRICS_INPUT_WORKFLOW.md).

Kết quả mẫu Anh, annotation caveat và phạm vi xử lý: [ENGLISH_ASR_RESULTS.md](ENGLISH_ASR_RESULTS.md).

Kết quả alignment, loader compatibility fix và file word/sentence drafts: [ALIGNMENT_POC_RESULTS.md](ALIGNMENT_POC_RESULTS.md).

Video để nghe rà soát: [VIETNAMESE_LYRICS_PREVIEW.md](VIETNAMESE_LYRICS_PREVIEW.md). Theo steering của user, hiện ưu tiên tiếng Việt; tối ưu mẫu Anh tạm hoãn.

Checkpoint `ed0ed8f` đã push lên `origin/dev`, gồm Player fidelity, audio EOF và lifecycle cùng các checkpoint trước. Follow-up state/template/local storage hiện trên `dev`, chưa commit/push. Các câu trạng thái Git trong báo cáo cũ ghi thời điểm lập; trạng thái repository hiện tại theo Git history. Chưa chọn stack chính thức hoặc đánh FR Verified.
