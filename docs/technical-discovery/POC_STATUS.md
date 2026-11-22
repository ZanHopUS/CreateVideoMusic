# PoC Execution Status

## Authorization

Product Owner xác nhận ngày 22/11/2026 (Asia/Saigon): **“Đồng ý kế hoạch PoC, chỉ dùng local và dữ liệu có quyền sử dụng, mục đích cá nhân phi thương mại.”**

Phê duyệt cho phép setup môi trường PoC riêng, cài dependency/tải model cần thiết và chạy các phép thử local theo POC_PLAN, gồm faster-whisper small, WhisperX và Remotion/FFmpeg. Ngưỡng trong kế hoạch được dùng làm ngưỡng sàng lọc PoC; không trở thành cam kết release hoặc ADR Accepted. Cloud POC-06 không thực hiện. Không commit/push nếu chưa được yêu cầu.

Ghi nhận này cập nhật các ghi chú “chưa cho phép chạy PoC” trong tài liệu discovery trước đó. Không cấp quyền dùng file chưa rõ nguồn/license hoặc tự công bố kết quả có media cá nhân.

## Current execution

- POC-00: Environment smoke completed; corpus/ground truth readiness còn thiếu. Venv riêng, model small pin revision/hash, Remotion/browser đã chuẩn bị.
- POC-01: Initial runs completed — 12 generated negative-control runs và một bài Việt user cung cấp, đối chứng VAD on/off. Chưa có ground truth hoặc mẫu Anh; quality gates chưa đo.
- POC-02: Pending — chưa chạy forced alignment; cần text đúng để đánh giá timing độc lập với ASR.
- POC-03: Initial smoke completed — 3 MP4 thực 15s/720×1280/30FPS trên media tự tạo; metadata/full decode/marker checks đạt trong phạm vi này. 36-case matrix và preview fidelity chưa chạy.
- POC-04/05/07: Pending — chưa chạy stress/editor/storage/Drive/segment suggestions.
- POC-06: Excluded — local only.

Artifacts tải về, môi trường, media và raw evidence đặt dưới `.poc/`, được ignore khỏi Git. Script PoC có thể nằm trong `poc/`; không phải application code chính thức.

Chi tiết, kết quả đo và bản TXT/SRT để rà soát: [POC_INITIAL_RESULTS.md](POC_INITIAL_RESULTS.md). Chưa chọn stack chính thức, chưa đánh FR Verified, chưa commit/push.
