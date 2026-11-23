# Kết nối Google Drive trên web

Ngày: **23/11/2026**. Đã có UI/backend và kiểm thử local; **chưa kết nối tài khoản thật**.
Xem [quyết định và giới hạn](../decisions/ADR-0002-DIRECT_GOOGLE_DRIVE.md).

## Thiết lập một lần

1. Trong [Google Cloud Console](https://console.cloud.google.com/), chọn/tạo project
   của bạn; bật **Google Drive API** và **Google Picker API**.
2. Thiết lập Google Auth platform: tên ứng dụng và audience phù hợp. Với External
   ở Testing, thêm tài khoản sẽ dùng Drive vào Test users.
3. Tạo OAuth Client loại **Desktop app**, tải file JSON về máy. Không dùng Service
   Account, không dán token vào chat và không đặt JSON này trong Git.
4. Trong Studio, mở **Kho Google Drive**, kiểm tra link thư mục kho chung, chọn
   OAuth client JSON rồi **Lưu cấu hình Drive**.
5. Bấm **Đăng nhập Google** → **Mở Google để cấp quyền và chọn thư mục**. Đăng nhập
   tài khoản có quyền ghi và chọn đúng folder. Quay lại Studio để xem trạng thái.

App chỉ xin quyền `drive.file`; Google Picker cấp quyền cho đối tượng được chọn.
Tài liệu triển khai: [Google Picker desktop](https://developers.google.com/workspace/drive/picker/guides/desktop-mobile-picker).
Nếu app External đang Testing, refresh token cho scope này có thể hết hạn sau
7 ngày; đăng nhập lại khi cần. [Google OAuth token lifetime](https://developers.google.com/identity/protocols/oauth2).

## Bản sao lưu hiện tại

Xác nhận đồng ý upload rồi bấm **Sao lưu dữ liệu lên Drive**. Project hiện tại
được ghi vào local working state trước khi chốt inventory. Các file đã upload
thành công được kiểm checksum; manifest trong Backups chỉ xuất hiện cuối lượt
hoàn tất. Đóng tab không hủy upload; dừng launcher có thể ngắt lượt đang chạy.

Mỗi lượt tạo file riêng, chưa dedup: dùng thêm dung lượng và thời gian mạng. Khi
lỗi/quota đầy, giữ nguyên local và bản manifest thành công trước; file upload
dở/không có manifest có thể còn trên Drive. Không tự xóa những file đó.

Đây chưa phải tự đồng bộ, trình duyệt thư viện Drive hoặc restore. Không xóa bản
local sau sao lưu. SQLite, temp render, model và thông tin đăng nhập vẫn ở máy;
300 GB cloud không thay dung lượng trống cần cho xử lý local.

## Kiểm tra đã chạy

- 17 unit tests; 23 integration tests (9 Drive mới), đều đạt.
- Build, TypeScript, Prettier, Ruff đạt.
- 1 browser case thật: nhập JSON fixture → lưu cấu hình → sinh link PKCE/Picker
  → hủy kết nối; không mở Google hoặc upload cloud.
- Transport Google được giả lập: state/replay, sai folder/scope, DPAPI,
  upload nhiều chunk/remote checksum, chặn URL upload lạ, manifest cuối và lỗi
  quyền giữ nguyên local/manual-save state.

Chưa kiểm: OAuth client thật, Picker consent/account permissions, refresh/revoke
thật, upload lớn/đứt mạng/quota, download và restore.
