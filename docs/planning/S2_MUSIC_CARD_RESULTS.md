# S2 Music Card — triển khai đang kiểm chứng

Ngày **23/11/2026**. Nhánh `dev`. Phạm vi: TPL-02 cơ bản,
không đổi schema/timeline hoặc preset render.

Dashboard chọn Music Card để tạo project có trường tên bài và nghệ sĩ. Hai ảnh
được đặt nối tiếp trong track hình ảnh; ảnh thứ hai làm bìa thẻ ở nửa sau video.
Panel Thuộc tính cho sửa metadata. Shared Remotion scene đặt bìa, thông tin bài
hát và tiến trình; Player và MP4 dùng chung component. Backend chấp nhận TPL-02
khi có ít nhất hai ảnh và nhạc; preset hiện là 720×1280/30FPS.

Đã đạt: build/TypeScript, 18 Vitest, 25 pytest, Ruff và Prettier. Browser E2E
qua chọn mẫu, nhập hai ảnh/WAV tự tạo, sửa metadata, preview và lưu project.
Lượt render production **chưa xuất MP4** vì RAM trống dưới admission 4 GiB;
test chờ đủ RAM rồi hết hạn. Lượt kiểm **chức năng** dùng admission 3 GiB chỉ
trong test server đã xuất MP4 3 giây: H.264/AAC 720×1280/30FPS, 90 frames,
144384 audio samples, 0 lỗi timestamp; hai frame trước/sau thẻ có độ lệch mẫu
RGB 68,86. SHA-256 output `5527933eab702a354af2648658821583cb653767f7b68cd08a32719e2d9c343a`.
Không coi FR-306/E2E-21 Verified về ngưỡng tài nguyên; production vẫn 4 GiB.

Chưa có layout/color nâng cao, progress gắn chính xác với playback của bài hát,
ma trận preset và kiểm hiệu năng dài. Trong bản cơ bản, progress biểu diễn thời
gian đã qua của phần thẻ. Chuyển thứ tự ảnh có thể đổi ảnh bìa, nên kiểm lại
preview trước khi xuất.
