# Kết nối Google Drive trên web

Ngày: **23/11/2026**. OAuth đã kết nối với thư mục CreateVideoMusic. Một bản sao lưu
thật gồm 4 project/0 media/0 MP4 đã được tìm và khôi phục thành công vào workspace
thử riêng (4/4 project); chưa thử bản sao lưu có media hoặc MP4.
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

Media có cùng hash được dùng lại nếu file Drive cũ còn đủ size/checksum trong đúng
thư mục. Project và MP4 mỗi lượt vẫn tạo file riêng, dùng thêm quota. Khi
lỗi/quota đầy, giữ nguyên local và bản manifest thành công trước; file upload
dở/không có manifest có thể còn trên Drive. Không tự xóa những file đó.

Trong mục Kho Google Drive, có thể bật **Tự sao lưu** để app kiểm thay đổi mỗi
30 giây khi đang chạy. Đây là lựa chọn riêng; mặc định tắt. Bấm **Tìm bản sao lưu**,
chọn snapshot rồi **Khôi phục**.
Chỉ thêm project chưa có trên máy; project hiện có được giữ nguyên. File tải về
được kiểm checksum và project được kiểm schema/hash trước khi ghi. Tự sao lưu
dừng khi app đóng; chưa có quản lý xung đột giữa hai máy. MP4 đã khôi phục nằm
trong mục **Xem MP4 đã khôi phục** để tải về. Không xóa bản
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

Đã kiểm thực tế: OAuth/Picker, backup và restore 4 project vào workspace khác;
round-trip fixture ảnh PNG, H.264 MP4 nguồn, WAV và MP4 xuất đều khớp SHA-256.
Hai lượt backup fixture dùng lại cùng Drive file IDs cho 3 media. Chưa kiểm tự
sao lưu chạy lâu, refresh/revoke, upload lớn/đứt mạng/quota, restore trên PC khác.
