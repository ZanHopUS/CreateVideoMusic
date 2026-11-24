# UI/UX-02 — Professional Video Editor Redesign

**Dự án:** AI Music Video Studio (Hòa Âm)

**Phiên bản:** UI/UX Specification v1.0

**Trạng thái:** Approved for Design — Not Implemented

**Phạm vi:** Video Editor, Lyrics Workspace, Media Library, Inspector, Timeline, Google Drive Storage Manager.

## 1. Mục tiêu thiết kế

Thiết kế lại toàn bộ giao diện Video Editor theo phong cách phần mềm chỉnh sửa video chuyên nghiệp, hiện đại, dễ sử dụng và thống nhất với nhận diện thương hiệu Hòa Âm.

Các mục tiêu bắt buộc:

1. Editor hiển thị trong một viewport desktop, không có cuộn dọc toàn trang.
2. Preview và Timeline luôn hiện diện trong không gian làm việc.
3. Người dùng có thể truy cập và chỉnh sửa media, lyrics, timeline, hiệu ứng và thuộc tính mà không phải cuộn qua nhiều khối giao diện.
4. Khắc phục trạng thái chỉ đọc và lỗi nhận quyền chỉnh sửa.
5. Tổ chức Google Drive thành một khu vực quản lý lưu trữ riêng.
6. Giữ nguyên chức năng, dữ liệu và hành vi nghiệp vụ đã triển khai, trừ những thay đổi được phê duyệt rõ ràng.
7. Tối ưu desktop trước, hỗ trợ mobile trong giai đoạn phát triển sau.

## 2. Design Direction

### 2.1. Phong cách

- Dark-first, chuyên nghiệp, tối giản.
- Giữ nhận diện Hòa Âm và màu tím pastel.
- Sử dụng màu nhấn có chủ đích, không lạm dụng gradient.
- Icon nhất quán, có tooltip với các nút chỉ có biểu tượng.
- Typography rõ ràng, hỗ trợ đầy đủ dấu tiếng Việt.
- Trạng thái hover, focus, selected, disabled và loading phải phân biệt được.
- Ưu tiên thao tác và nội dung video hơn yếu tố trang trí.

### 2.2. Design System

Xây dựng hệ thống design tokens thống nhất cho:

- Background, surface, border, accent và semantic colors.
- Typography scale, line height, font weight.
- Spacing, radius, shadow và divider.
- Button, input, select, slider, tooltip, modal, toast.
- Panel header, tab, media card, timeline item.
- Trạng thái loading, empty, error, success, conflict.

Giá trị token cụ thể sẽ được chuẩn hóa trong giai đoạn Design System. Không coi mã màu và kích thước trong wireframe là giá trị production bắt buộc.

## 3. Layout — Professional Three-Column Editor

### 3.1. Cấu trúc tổng thể

Editor gồm:

- Header cố định phía trên.
- Left Tool Panel.
- Center Video Preview.
- Right Contextual Inspector.
- Bottom Docked Timeline.
- Các dialog/workspace chuyên dụng cho Storage, Export và quản lý dữ liệu.

**Quyết định:** Editor sử dụng ba cột cố định về cấu trúc. Nội dung trong từng panel có thể thay đổi theo tab.

### 3.2. Tỷ lệ khởi điểm đề xuất

| Khu vực | Kích thước đề xuất |
|---|---|
| Header | 56 px |
| Left Tool Panel | 280–320 px |
| Right Inspector | 280–320 px |
| Center Preview | Phần chiều rộng còn lại |
| Bottom Timeline | 260–320 px mặc định |
| Timeline min/max | Khoảng 180 px đến 55% chiều cao khả dụng |

Các thông số này cần kiểm tra trên màn hình 1366×768 và 1920×1080 trước khi chốt.

### 3.3. No Page Scroll

- Editor shell chiếm `100dvh`.
- Không có vertical scrolling trên `html`/`body` khi ở chế độ Editor.
- Header và Timeline giữ vị trí trong shell.
- Left Panel và Inspector có vùng cuộn độc lập.
- Preview tự co giãn nhưng phải giữ đúng aspect ratio.
- Nội dung dài được xử lý bằng scroll container nội bộ, tab hoặc dialog.
- Không dùng layout khiến Preview và Timeline bị đẩy ra ngoài màn hình.
- Khi viewport quá nhỏ, có chế độ thu gọn phù hợp; không được âm thầm cắt mất nút quan trọng.

## 4. Header & Navigation

Header hiển thị:

- Nút quay về Dashboard.
- Tên project, có khả năng đổi tên theo luồng hợp lệ.
- Trạng thái lưu: Đã lưu / Chưa lưu / Đang lưu / Lỗi lưu.
- Undo và Redo.
- Trạng thái quyền chỉnh sửa khi cần.
- Nút Lưu project.
- Nút Xuất video.

Danh sách project dài và các chức năng Google Drive không được chiếm một hàng ngang thường trực trong Editor.

Điều hướng dự án chính nằm ở Dashboard.

## 5. Editor Lease & Read-only Recovery

**Priority: P0 — Functional Blocker**

### 5.1. Hành vi mong muốn

- Một project chỉ có một phiên ghi hợp lệ tại một thời điểm.
- Khi không có phiên ghi khác, tab mở project phải được cấp quyền chỉnh sửa.
- Tab thứ hai mở cùng project hiển thị chế độ chỉ đọc cùng lý do cụ thể.
- Nút “Nhận quyền chỉnh sửa” phải thực sự yêu cầu takeover và cập nhật UI theo kết quả API.
- Nếu takeover thành công, các thao tác chỉnh sửa phải được kích hoạt.
- Nếu takeover thất bại, phải hiển thị lỗi cụ thể và cách khắc phục.
- Không được tự ghi đè dữ liệu của phiên trước.
- Phiên hết hạn hoặc tab đóng bất thường phải có khả năng phục hồi quyền.

### 5.2. Kiểm thử bắt buộc

- Mở project trong một tab.
- Mở cùng project ở hai tab.
- Takeover từ tab thứ hai.
- Kiểm tra tab thứ nhất không còn quyền ghi.
- Đóng tab đang giữ quyền và mở lại.
- Khởi động lại launcher.
- Kiểm tra sửa thuộc tính, Undo/Redo và Manual Save sau takeover.

Không sửa vấn đề bằng cách vô hiệu hóa toàn bộ cơ chế bảo vệ đồng thời.

## 6. Left Tool Panel

Các tab chính:

1. Media.
2. Văn bản.
3. Lyrics.
4. Hiệu ứng.
5. Templates.

Các chức năng phụ được nhóm theo ngữ cảnh, không tạo thêm tab trùng lặp.

### 6.1. Media Library

- Import nhiều file ảnh, video và audio.
- Tìm kiếm media theo tên và tag.
- Lọc theo loại.
- Hiển thị thumbnail, tên file, định dạng và thời lượng phù hợp.
- Có trình nghe thử audio và xem trước video.
- Thêm media vào project/timeline.
- Hỗ trợ kéo-thả khi đã kiểm chứng được hành vi.
- Tên file dài không phá vỡ bố cục.
- Thumbnail lỗi phải có trạng thái fallback và khả năng thử lại.
- Không tự động xóa hoặc thay đổi media gốc.

### 6.2. Text Tools

- Tạo caption/text.
- Sử dụng preset văn bản.
- Chọn layer văn bản để chỉnh sửa.
- Các thuộc tính chi tiết được hiển thị trong Inspector.

### 6.3. Effects & Templates

- Hiển thị preset theo nhóm.
- Có bản xem trước hiệu ứng.
- Không hiển thị một chức năng như đã hoạt động nếu backend chưa hỗ trợ.
- Template hiện có và mẫu cá nhân phải sử dụng được mà không làm thay đổi template gốc.

## 7. Center Video Preview

Preview là trung tâm của Editor.

Yêu cầu:

- Luôn hiển thị, tự điều chỉnh theo không gian.
- Giữ tỷ lệ 9:16, 16:9 hoặc 1:1 theo project.
- Hiển thị video/ảnh/text/lyrics/effects từ composition hiện tại.
- Có vùng an toàn hiển thị nội dung khi phù hợp.
- Thanh điều khiển được đặt ngay dưới Preview.
- Hỗ trợ Play/Pause, seek, thời gian hiện tại/tổng thời lượng, volume/mute và fullscreen.
- Các thao tác được phép phải cập nhật preview phù hợp.
- Preview và MP4 tiếp tục sử dụng cùng mô hình composition hiện có.

Không dùng thành phần giao diện giả lập thay cho nội dung video thực.

## 8. Right Contextual Inspector

Inspector thay đổi theo đối tượng đang chọn.

### Không chọn clip

- Thông tin project.
- Cấu hình canvas và video preset.
- Các thuộc tính chung.

### Image

- Fit, crop, zoom.
- Position, rotation.
- Brightness, blur, filter.
- Duration và các hiệu ứng hỗ trợ.

### Video

- Transform.
- Trim/source range.
- Playback speed.
- Visual effects.

### Audio

- Volume/mute.
- Trim/source offset.
- Playback speed.
- Fade nếu được triển khai.

### Text

- Nội dung.
- Font, size, color.
- Stroke, shadow.
- Position, rotation.
- Animation/preset.

### Lyrics

- Font, vị trí và kiểu trình bày.
- Karaoke highlight.
- Animation.
- Timing và trạng thái đồng bộ.

### Music Card

- Cover art.
- Title, artist.
- Card layout.
- Progress style.
- Typography và colors.

### Interaction

- Ưu tiên slider kết hợp numeric input cho thuộc tính số.
- Hiển thị đơn vị rõ ràng.
- Có reset về mặc định khi phù hợp.
- Thuộc tính thay đổi phải phản ánh lên Preview.
- Disabled control phải giải thích nguyên nhân.
- Các thao tác phải tôn trọng quyền chỉnh sửa hiện hành.

## 9. Bottom Docked Timeline

**Quyết định:** Timeline được cố định phía dưới và có thể kéo thay đổi chiều cao.

### 9.1. Cấu trúc

- Timeline Toolbar.
- Time Ruler.
- Playhead.
- Track Headers.
- Timeline Tracks.
- Clip Items.
- Horizontal Scroll/Zoom.

### 9.2. Tương tác

- Select clip.
- Drag/reposition.
- Trim.
- Split và Duplicate theo phạm vi được hỗ trợ hoặc task mở rộng đã được phê duyệt.
- Undo/Redo.
- Zoom timeline.
- Snapping nếu tính năng đã được triển khai.
- Track reorder và visibility nếu thuộc capability của track.
- Đồng bộ playhead với Preview.
- Có biểu thị rõ clip được chọn và track hiện tại.

### 9.3. Resizable Timeline

- Có drag handle giữa khu vực preview và timeline.
- Giới hạn min/max hợp lý.
- Không làm Inspector hoặc Preview tràn khỏi viewport.
- Có thể khôi phục kích thước mặc định.
- Không làm thay đổi project content hoặc Manual Save state chỉ vì thay đổi kích thước panel.

## 10. Dedicated Lyrics Workspace

Lyrics không còn là một form dài nằm giữa Preview và Timeline.

Ba chế độ:

### Recognition

- Chọn audio source.
- Chọn ngôn ngữ và local model.
- Start/Cancel AI job.
- Hiển thị tiến trình, lỗi và bản nháp.
- Import LRC/SRT.
- Không tự áp dụng nội dung AI chưa duyệt.

### Editing & Alignment

- Danh sách câu với timestamp.
- Sửa text và thời gian.
- Nghe tại đoạn nguồn phù hợp.
- Căn thời gian theo câu hoặc từng đơn vị từ khi có kết quả.
- Hiển thị fallback khi alignment không đủ tin cậy.
- Lưu bản nháp vào project.
- Review và áp dụng lời đã duyệt.

### Styling

- Font, color, stroke/shadow.
- Karaoke highlight.
- Animation presets.
- Position/layout.
- Preview cập nhật theo nội dung đã được áp dụng.

Giữ phân biệt rõ Draft, Reviewed và Applied.

## 11. Google Drive Storage Manager

Google Drive được chuyển khỏi trang Editor chính thành một Storage Workspace hoặc dialog độc lập.

### 11.1. Khi chưa kết nối

- Hiển thị trạng thái chưa kết nối.
- Hướng dẫn thiết lập OAuth.
- Chọn OAuth Desktop Client JSON.
- Nhập/chọn thư mục kho.
- Kết nối tài khoản.
- Hiển thị lỗi cấu hình rõ ràng.

### 11.2. Khi đã kết nối

- Hiển thị trạng thái kết nối.
- Tên thư mục Drive.
- Lượt sao lưu gần nhất nếu có dữ liệu.
- Nút Sao lưu ngay.
- Nút Tìm bản sao lưu / Khôi phục.
- Toggle Tự sao lưu, mặc định tắt.
- Tiến độ upload/download.
- Lịch sử backup.
- Danh sách MP4 đã khôi phục.
- Lối vào Cấu hình nâng cao và Ngắt kết nối.

### 11.3. Quy tắc an toàn

- Không upload nếu chưa có consent hợp lệ.
- Không bật tự sao lưu ngầm.
- Backup chỉ được báo thành công theo trạng thái backend đã kiểm chứng.
- Restore kiểm manifest, schema, checksum.
- Không ghi đè project local đang chỉnh sửa.
- Không xóa dữ liệu local sau upload.
- Không đưa credentials, SQLite runtime, model hoặc temp render lên Drive.
- Trạng thái đăng nhập hết hạn, quota, mất mạng và hủy thao tác phải có thông báo riêng.

## 12. Export Workspace

Export mở bằng dialog hoặc workspace chuyên dụng, không đặt lẫn trong Inspector.

Nội dung:

- Resolution.
- FPS.
- Aspect ratio.
- Output folder.
- Kiểm tra media thiếu.
- Kiểm tra tài nguyên trước render.
- Bắt đầu, theo dõi, hủy và retry render.
- Thông báo nguyên nhân blocked/waiting.
- Xem kết quả MP4 và mở thư mục chứa file.

Không coi job queued là render thành công.

## 13. Global UI States

Chuẩn hóa:

- Loading.
- Empty State.
- Read-only.
- Permission Conflict.
- Unsaved Changes.
- Background Job Progress.
- Offline/Drive Disconnected.
- Missing Media.
- Invalid Input.
- Recoverable Error.
- Fatal Error.

Thông báo phải ngắn gọn, bằng tiếng Việt và có hướng xử lý phù hợp.

## 14. Regression & Acceptance Criteria

| ID | Tiêu chí |
|---|---|
| UI-ED-01 | Editor không có cuộn toàn trang tại desktop viewport được hỗ trợ |
| UI-ED-02 | Preview, Inspector và Timeline hiển thị đồng thời |
| UI-ED-03 | Timeline resize được, không phá layout |
| UI-ED-04 | Các panel có vùng cuộn riêng |
| UI-ED-05 | Editor lease và takeover hoạt động đúng |
| UI-ED-06 | Các thuộc tính thay đổi phản ánh lên Preview |
| UI-ED-07 | Media thumbnail, danh sách và import hoạt động |
| UI-ED-08 | Lyrics workflow draft → review → apply không regression |
| UI-ED-09 | Timeline select/seek/trim/undo/redo hoạt động |
| UI-ED-10 | Manual Save và recovery giữ nguyên semantics |
| UI-ED-11 | Google Drive backup/restore và consent hoạt động |
| UI-ED-12 | Export MP4 sử dụng project snapshot chính xác |
| UI-ED-13 | Không có lỗi console nghiêm trọng chưa xử lý |
| UI-ED-14 | Các trường hợp empty/error/disabled được kiểm thử |
| UI-ED-15 | Tab navigation, focus và keyboard controls hoạt động phù hợp |

Các tiêu chí phải có bằng chứng browser test thực tế và kiểm thử backend tương ứng. Build pass không thay thế kiểm thử tương tác.

## 15. Out of Scope

Chưa triển khai trong đợt redesign:

- Viết lại AI Lyrics Engine.
- Thay đổi renderer hoặc video codec mặc định.
- Thay đổi định dạng dữ liệu project.
- Cloud-first architecture.
- Mobile Editor hoàn chỉnh.
- Collaboration nhiều người.
- Refactor toàn bộ backend nếu không có nguyên nhân kỹ thuật được chứng minh.

## 16. Implementation Governance

- Chỉ triển khai khi Product Owner phê duyệt kế hoạch.
- Làm việc trên nhánh `dev`.
- Không sửa trực tiếp `main`.
- Chia task theo layout, editor lease, media, lyrics, inspector, timeline, Drive và regression.
- Mỗi task có Acceptance Criteria và kết quả kiểm thử.
- Không thay thế chức năng đang hoạt động bằng mockup tĩnh.
- Không tự commit/push/merge trái với quy tắc AGENTS.md.

**Trạng thái hiện tại:** Đặc tả thiết kế được chốt; chưa thực hiện thay đổi mã nguồn.
