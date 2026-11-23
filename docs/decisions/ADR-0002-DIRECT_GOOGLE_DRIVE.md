# ADR-0002 — Google Drive trực tiếp, tùy chọn

Ngày: **23/11/2026**. Trạng thái: **hướng kết nối do người dùng yêu cầu; chưa nghiệm thu cloud**.

## Yêu cầu và phạm vi thay đổi

Người dùng chọn một thư mục kho chung và xác nhận: “Tôi muốn dùng trực tiếp Drive
trên web”. Đây là chỉ dẫn mới thay cho phương án bắt buộc Drive for desktop trong
ADR-0001/FR-407. Không sửa hồi tố baseline A–G. Không đổi renderer, timeline,
AI local hoặc SQLite runtime; Drive là đích lưu tùy chọn, đăng nhập không bắt buộc
cho editor local.

## Cách triển khai ban đầu

Backend local gọi Drive API bằng OAuth client riêng của ứng dụng. OAuth Desktop
qua browser, loopback callback riêng, PKCE S256, state dùng một lần/10 phút;
callback không ghi access log. Chỉ xin `drive.file`, chọn đúng folder bằng Google
Picker; từ chối chọn khác hoặc scope rộng hơn. Việc cấp quyền trong chat không
thay thế quyền của ứng dụng. Theo [Google desktop OAuth](https://developers.google.com/identity/protocols/oauth2/native-app)
và [Picker desktop](https://developers.google.com/workspace/drive/picker/guides/desktop-mobile-picker).

Client config và tokens lưu bằng Windows DPAPI theo user, ngoài Git và snapshot;
không có plaintext fallback. DPAPI không bảo vệ trước mã độc chạy cùng tài khoản
Windows. [Microsoft DPAPI](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata).

Người dùng bấm sao lưu và đồng ý upload inventory local đã ghi. Tạo các folder
Media/Projects/Exports/Lyrics/Templates/Backups. Upload từng file theo chunks
8 MiB, kiểm size/MD5 của kết quả Google trước công bố manifest cuối. Đây là kiểm
toàn vẹn truyền file, không phải chữ ký. Không upload live SQLite, OAuth, model
hoặc render temp. Không xóa nguồn; không đánh dấu autosave thành manual save.
[Drive uploads](https://developers.google.com/workspace/drive/api/guides/manage-uploads).

## Giới hạn và cửa kiểm chứng

- Hiện là checkpoint qua nút bấm; mỗi lượt copy lại media/output, tăng quota.
  Dedup, retry tiếp tục sau restart, tự đồng bộ và quota preflight chưa có.
- Lyrics trong state project đi cùng snapshot; chưa có importer lyrics/file lyrics
  riêng hay reusable-template upload. Hai folder tương ứng mới được dành chỗ.
- Chưa đọc/import kho Drive, restore khác máy, relink/cache eviction hay xử lý
  concurrent editing. Do đó chưa hoàn thành yêu cầu “Drive là kho chính mọi thứ”.
- Chưa login/upload/round-trip thật vì thiếu OAuth client của ứng dụng. Test dùng
  Google transport giả không chứng minh tài khoản, Picker hoặc quota tương thích.
- Giữ nguyên dữ liệu local đến khi restore + hash/content parity thật đạt.

Tiếp theo: cấu hình client, người dùng đăng nhập, thử fixture có quyền sử dụng;
kiểm upload/download/checksum, quota/offline và thu hồi quyền. Sau đó mới hoàn
thiện restore và chuyển Drive thành kho chính. Không bật cloud AI cùng kết nối này.
