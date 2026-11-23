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

UI mở bằng URL local thường có thể lấy session hiện hành từ Next route cùng origin
qua browser fetch. Route yêu cầu Host đúng, `Sec-Fetch-Site: same-origin` và
Referer là trang Studio, trả `no-store`; không cấp qua điều hướng trực tiếp hoặc
nguồn ngoài. Token vẫn chỉ ở memory của tab, không ghi URL/query/storage. Đây là
bổ sung cho cơ chế launcher, để tab mới trong trình duyệt local dùng được UI.

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

- Có tùy chọn tự sao lưu mỗi 30 giây khi app chạy. Media đã xác minh có thể dùng
  lại cùng Drive file ID; project/MP4 snapshot mới vẫn tăng quota. Retry tiếp tục
  sau restart và quota preflight chưa có.
- Lyrics trong state project đi cùng snapshot; chưa có importer lyrics/file lyrics
  riêng hay reusable-template upload. Hai folder tương ứng mới được dành chỗ.
- Có tìm manifest và restore project mới vào SQLite local, không ghi đè project
  hiện có. Đã restore 4/4 project từ bản cloud thật vào workspace thử riêng.
  Fixture PNG/H.264 MP4/WAV và MP4 xuất đã round-trip checksum trên Drive thật.
  Chưa chứng minh restore khác máy, relink/cache eviction hay xử lý
  concurrent editing. Do đó chưa hoàn thành yêu cầu “Drive là kho chính mọi thứ”.
- Giữ nguyên dữ liệu local đến khi restore + hash/content parity thật đạt.

Tiếp theo: cấu hình client, người dùng đăng nhập, thử fixture có quyền sử dụng;
kiểm upload/download/checksum, quota/offline và thu hồi quyền. Sau đó mới hoàn
thiện restore và chuyển Drive thành kho chính. Không bật cloud AI cùng kết nối này.
