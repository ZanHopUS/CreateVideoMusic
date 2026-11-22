# PRD v1.0 — AI Music Video Studio

**Trạng thái:** Baseline yêu cầu sản phẩm, 22/11/2026. **Chưa phê duyệt kiến trúc kỹ thuật; chưa triển khai.**  
**Owner:** Product Owner (người sử dụng); **Đối tượng:** người dùng cá nhân, desktop Windows 11 trước, mobile về sau.

## 1. Product Vision
Tạo ứng dụng web dựng và chỉnh sửa video âm nhạc cho TikTok/Reels/Shorts: chọn mẫu → tải ảnh/video và nhạc → hỗ trợ caption/lyrics thông minh → dựng bản nháp nhiều layer → chỉnh sửa linh hoạt → xuất MP4. Giá trị khác biệt hàng đầu là **Editor mạnh, linh hoạt**, kết hợp tự động hóa để tiết kiệm thao tác.

## 2. Mục tiêu và phi mục tiêu
**Mục tiêu:** (1) tạo được ba dạng video mục tiêu; (2) duy trì khả năng chỉnh sửa sau tự động tạo; (3) sử dụng local không phụ thuộc phí dịch vụ; (4) đồng bộ lời theo câu và thử căn từ với fallback; (5) project có thể lưu/mở và render thực tế.

**Ngoài MVP Core:** biên tập keyframe chuyên nghiệp, nhóm layer lồng nhau, batch rendering, cloud processing, cộng tác đa người dùng, tự đăng lên mạng xã hội, lấy âm thanh từ nền tảng không được cấp quyền, mobile editor hoàn chỉnh. Các tính năng đã xác nhận nhưng chưa thuộc Core **không bị hủy**, được đưa vào Complete/Backlog.

## 3. Người dùng và bối cảnh
- **Primary:** một người dùng cá nhân, vừa học công nghệ vừa có sản phẩm sử dụng lâu dài.
- **Skill range:** người mới lẫn người đã biết CapCut; giao diện tiếng Việt, desktop-first, hiện đại, dark theme mặc định, tối giản.
- **Environment:** Windows 11, RAM 16 GB, không bắt buộc GPU rời, ngân sách bắt buộc 0 đồng.
- **Priority:** Editor linh hoạt > trải nghiệm tạo nháp thuận tiện; các tính năng AI phải có kiểm soát và fallback.

## 4. Các quyết định baseline A–G
| Nhóm | Quyết định |
|---|---|
| A | Vừa học và dùng thực tế; mixed users; ưu tiên Editor; desktop trước/mobile sau; ngân sách free; dùng cá nhân |
| B | Template trước; nhiều ảnh/video; caption hybrid; nhạc tự chọn/gợi ý trong thư viện; tạo draft trước; template từ project **và** từ trang trắng |
| C | Lyrics Việt/Anh; ưu tiên từng từ/fallback câu; AI/nhập tay/LRC/SRT; hỗ trợ đầu vào remix/rap/multiple voices/instrumental; duyệt kết quả; gợi ý nhiều đoạn; local + API tùy chọn; nhiều phong cách chữ |
| D | Multi-track; chỉnh media advanced; effect presets; gợi ý style và sửa tay; blank template builder; Music Card tùy chỉnh; split/duplicate/snap/lock-hide |
| E | **Lưu thủ công**; mở lại toàn bộ editor state; chọn thư mục local; 720/1080p 30/60 FPS; 9:16,16:9,1:1; background render; xem trước/tải/mở folder; personal media library |
| F | Ưu tiên chất lượng; CPU-only 16GB; editor/render offline với AI online tùy chọn; tối đa 5 phút; recovery độc lập; không login; Drive desktop sync; dev khởi chạy bằng lệnh |
| G | MVP Core trước; **local-first, Vercel sau**; local AI + optional provider; upload + thư viện; storage local/Drive sync; E2E nghiệm thu; release cá nhân |

## 5. Danh mục template và giá trị người dùng
- **TPL-01 Ảnh + Caption + Nhạc:** một ảnh (có thể pan/zoom), caption tùy chỉnh, nhạc do người dùng chọn hoặc được đề xuất từ thư viện.
- **TPL-02 2+ Ảnh / Music Card:** ảnh hook, ảnh/card bài hát, bìa, tên bài, nghệ sĩ, tiến trình phát; có thể thay đổi bố cục.
- **TPL-03 Lyrics Video:** ảnh hoặc video nền, lyrics đồng bộ theo câu; theo từng từ khi kết quả đủ tin cậy; metadata, typography/effects.

## 6. Hành trình chính và Use Cases
**UC-01 Tạo video:** Dashboard → Thư viện template → chọn mẫu → nhập nhiều media và nhạc → chọn đoạn → caption/lyrics → generate draft → editor → lưu → xuất MP4.
**UC-02 Duyệt lyrics:** nhận dạng/nhập/import → rà soát nội dung và timestamp → xác nhận → animation theo cấu hình.
**UC-03 Chỉnh sửa:** chỉnh timeline nhiều track, trim, style, hiệu ứng, âm lượng → undo/redo → preview.
**UC-04 Tái sử dụng template:** lấy project hiện có → đánh dấu placeholder → lưu template → áp dụng với media mới.
**UC-05 Template trống:** tạo từ canvas trống, thêm layer/placeholder, kiểm tra hợp lệ, lưu (MVP Complete).
**UC-06 Khôi phục:** khi mở app sau crash, đề nghị phục hồi từ recovery snapshot, không ghi đè bản lưu thủ công.

## 7. Ưu tiên phát hành
### MVP Core — tiêu chí bắt buộc
- TPL-01/02/03: luồng tạo bản nháp chạy thực, sử dụng được ảnh, video và nhạc hợp lệ.
- Upload, thư viện media cơ bản và một project có nhiều ảnh/video.
- Chọn nhạc/thời điểm cắt thủ công, nghe thử, đề xuất nhiều đoạn ở mức có kiểm chứng; fallback thủ công.
- AI lyrics pipeline thực, hỗ trợ nhập tay/LRC/SRT, review, căn thời gian câu; thử căn từ với fallback rõ ràng.
- Caption nhập tay và gợi ý khi provider có sẵn; không chặn luồng khi AI offline.
- Editor multi-track (background, music, lyrics, caption/text), kéo thả/chỉnh duration, playhead, trim, typography/effect cơ bản, undo/redo, preview.
- Lưu thủ công, cảnh báo dirty-state, lưu/mở đầy đủ trạng thái, recovery snapshot.
- Background render MP4, progress/cancel, xem trước/tải/mở folder, tỷ lệ và preset chất lượng theo lựa chọn E4/E5 được thực thi và test.
- Một thư viện template; lưu từ project có sẵn nếu cần cho Core, đảm bảo dữ liệu schema có thể mở rộng cho builder từ trang trắng.
### MVP Complete — vẫn thuộc cam kết sản phẩm
- Blank Template Builder với layer/placeholder; nhiều effect/font presets; timeline split/duplicate/snap/lock-hide; zoom/pan/rotate/filter nâng cao; AI style suggestions; Music Card layout tinh chỉnh; preset cá nhân; gợi ý nhạc tinh chỉnh.
- Các thành phần đã xác nhận trong B–D được triển khai đủ ở mốc này, không tự loại bỏ.
### Later
- Batch, Vercel/cloud worker, mobile editor, nhập media từ nguồn trực tuyến được cấp phép, chia sẻ template JSON, cộng tác và tự đăng nền tảng.

## 8. Chỉ số thành công
- Cả 3 template cho ra MP4 thực qua luồng E2E; bản nháp mở được trong editor và thay đổi còn sau lưu/mở.
- Không có lỗi mức blocker/critical trên đường đi chính; mọi job render có trạng thái và cơ chế hủy/thử lại.
- Playback/renderer dựa trên dữ liệu thời gian đã duyệt; mục tiêu chênh lệch ≤100ms thuộc renderer, **không** phải độ chính xác ASR.
- Benchmark CPU/RAM/trễ preview và render trên máy đích trước khi khóa ngưỡng hiệu năng.

## 9. Phụ thuộc, giới hạn và chính sách
- User cung cấp hoặc có quyền dùng media/nhạc; không tự tải audio từ TikTok/YouTube/Spotify trái quyền truy cập.
- Không tự gửi file private đến AI cloud; yêu cầu bật tính năng và thông báo rõ.
- Google Drive for desktop dùng đồng bộ **bản project đóng gói/snapshot nhất quán**, tránh đồng bộ live SQLite/temp đang ghi.
- Vercel chỉ là mục tiêu sau MVP local; website trên Vercel không tự truy cập CPU/filesystem của máy người dùng.

## 10. Phụ thuộc quyết định chưa đóng (xem OPEN_QUESTIONS.md)
AI-01/02 (free API và ASR/forced alignment), ST-01/02 (project portable / Drive snapshot), MED-01/02 (license, tagging, import URL), UX-01 (mức chi tiết editor Core), ARC-01 (Vercel mode tương lai), ACC-01 (ngưỡng benchmark). Những mục này có chủ sở hữu, phương án mặc định tạm và checkpoint phê duyệt.

## 11. Release gates
**G1 Requirements:** baseline và Open Questions; **G2 PoC:** transcription/alignment, render/preview; **G3 Architecture:** ADR, storage, API; **G4 Core:** E2E + save/reopen; **G5 Release:** benchmark, bảo mật local, tài liệu cài đặt. Mỗi gate phải có bằng chứng, không thay bằng mô tả code.
