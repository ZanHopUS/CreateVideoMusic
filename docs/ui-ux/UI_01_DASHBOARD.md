# UI-01 — Creative Dashboard

**Dự án:** AI Music Video Studio (Hòa Âm)

**Trạng thái:** Approved for Design về MR-01/MR-02 và hướng template-first; wireframe pixel vẫn Proposed, implementation chưa nghiệm thu

**Ngày khảo sát:** 24/11/2026 (Asia/Saigon)

**Mã khảo sát:** `dev` tại `ba60ab0`

**Master v2.1:** [MR-01…MR-04](UI_MASTER_SPEC.md) đã được PO phê duyệt cho triển khai liên tục R1–R6. Dashboard gồm CTA gọn → ba template thật → dự án gần đây; điều hướng chính là Tổng quan / Dự án / Lưu trữ / Cài đặt. Project Management là workspace riêng.

**Liên quan:** [UI-02](UI_02_VIDEO_EDITOR.md), [Gap Analysis](UI_GAP_ANALYSIS.md), [Kế hoạch R0–R6](UI_REDESIGN_PLAN.md).

## 1. Định hướng đã thống nhất

- Giữ thương hiệu Hòa Âm, phong cách dark-purple.
- Chuyển trang chủ từ landing page thành Creative Dashboard.
- Thu gọn Hero và đưa ba template lên vùng nhìn đầu tiên.
- Hiển thị các project gần đây.
- Cải thiện sidebar và điều hướng.
- Di chuyển Google Drive khỏi khu vực chính của Dashboard.

Đây là các định hướng đã nhận từ Product Owner. Những bố cục, số lượng card và hành vi chi tiết bên dưới là đề xuất để xem xét, chưa phải quyết định thiết kế được duyệt.

## 2. Hiện trạng

`apps/web/app/page.tsx` chỉ render `Studio`. Dashboard và Editor là hai nhánh JSX của `Studio`, phụ thuộc `project === null`; chưa có navigation state riêng. Hero lớn, CTA tạo mới và ba template đã có; project chỉ liệt kê trong sidebar. `DrivePanel` đặt trước cả hai nhánh. Nút “Studio của tôi” không có handler; brand `href="#"` không thực hiện chuyển Dashboard qua controller.

`GET /projects` hiện chỉ trả `{id, name}`, sắp xếp `rowid DESC` theo lúc tạo bản ghi. Không có `lastOpenedAt`, `updatedAt`, ảnh preview project hay số clip trong response. Không gọi thứ tự này là thứ tự mở gần nhất; không hiển thị ngày sửa hoặc thumbnail project giả. D-01 đã được PO chốt: lịch sử mở phải được lưu xuyên phiên; code hiện tại chưa đáp ứng.

## 3. Cấu trúc đề xuất để thảo luận

```text
┌─────────────────┬─────────────────────────────────────────────────┐
│ Hòa Âm          │ Tiêu đề ngắn + Tạo video / Mở file project     │
│ Tổng quan       ├─────────────────────────────────────────────────┤
│ Dự án           │ Bắt đầu từ mẫu                                 │
│ Mẫu             │ [Ảnh + Caption] [Music Card] [Lyrics Video]    │
│ Lưu trữ         ├─────────────────────────────────────────────────┤
│                 │ Project gần đây / Project trên máy             │
│ Local status    │ [Project] [Project] [Project] …                 │
└─────────────────┴─────────────────────────────────────────────────┘
```

Đây là sơ đồ thông tin, không phải wireframe đã chốt. Dashboard được phép cuộn nội dung khi nhiều project; quy tắc không cuộn toàn trang của UI-02 chỉ áp dụng Editor.

- Hero rút thành lời chào/tiêu đề một cụm ngắn; không chiếm phần lớn chiều cao.
- Ba template sử dụng đúng `create('TPL-01'|'TPL-02'|'TPL-03')`, mở draft thật. CTA tạo mới không dẫn tới blank builder ngoài Core.
- Sidebar thể hiện rõ workspace đang mở và thao tác được; danh sách project đầy đủ thuộc Dashboard, không kéo theo Editor.
- “Lưu trữ” mở Storage Manager riêng, không bung OAuth/Drive form trong nội dung chính. Local không đòi kết nối Drive.
- Card project sử dụng ID ổn định; hỗ trợ tên trùng, tên dài, mở và các thao tác hiện có qua controller. Không thêm clone/delete nâng cao ngoài phạm vi được duyệt.
- Tên, giới hạn hàng card, icon, kích thước, mật độ và responsive breakpoint cần duyệt ở R0/R1.

## 4. Project gần đây — D-01 đã chốt

**Quyết định PO ngày 24/11/2026:** lưu lịch sử mở project xuyên phiên. Phương án chỉ giữ trong memory và nhãn “Gần đây trong phiên này” không còn là đích triển khai.

Thiết kế kỹ thuật đề xuất: lịch sử local theo workspace, tham chiếu project ID và thời điểm mở thành công, nằm ngoài project content/manual-save hash. Không lấy mọi GET/polling project làm lần mở. R0 cần chốt chính xác thời điểm ghi (ví dụ project đã load thành công), giới hạn lịch sử, xử lý project bị xóa/import/restore và đồng bộ nhiều tab. Chưa tự chọn số lượng entry hoặc thứ tự tie-break làm quyết định PO.

Cần lớp lưu local xuyên restart và API metadata được thiết kế ở R0; không suy timestamps từ rowid hay sửa đổi giả. Cổng localhost của launcher thay đổi nên localStorage theo origin đơn lẻ không bảo đảm xuyên phiên; đề xuất metadata sidecar qua backend, không trộn vào bảng nội dung project. Đây là phương án kỹ thuật để review, chưa phải code hoặc contract đã ban hành. Không có yêu cầu tự đồng bộ lịch sử mở lên Drive hoặc sang máy khác.

Sau restore/import phải refresh danh sách; project đã xóa hoặc không còn truy cập được không được giữ như card mở được. Ghi lịch sử không làm project dirty, không tăng content revision và không đổi lease ownership.

## 5. Trạng thái và điều hướng đề xuất

| Trạng thái | Hành vi |
|---|---|
| Session loading | Skeleton/nhãn đang kết nối, chưa cho tạo/mở; không báo project rỗng khi dữ liệu chưa về |
| Empty | Ba template vẫn xuất hiện; hướng dẫn tạo mới và mở `.amvs.json`/`.amvs` |
| Có project | Tên trùng phân biệt bằng ID nội bộ; ellipsis và tooltip tên đầy đủ; không fabricate timestamp |
| API/session error | Thông báo tiếng Việt, retry/bootstrap theo quyền hiện có; không xóa state |
| Mở project | Chờ load + claim; sau đó Editor writable hoặc read-only có lý do |
| Về Dashboard khi dirty | Áp dụng chính sách cảnh báo hiện có; không biến working save thành manual save |
| Về Dashboard khi render | Job tiếp tục ở controller, mở lại vẫn thấy tiến độ/kết quả |

Đề xuất giữ điều hướng trong origin `/` và một controller cấp ứng dụng; chưa thêm route Editor riêng. Bootstrap hiện kiểm Referer đúng trang `/`; deep links cần review bảo mật riêng nếu muốn bổ sung.

## 6. Acceptance Criteria đề xuất

| ID | Tiêu chí để PO xem xét |
|---|---|
| UI-DB-01 | Thương hiệu Hòa Âm/dark-purple; navigation có selected/focus/disabled rõ |
| UI-DB-02 | Ở 1366×768 và 1920×1080, cả ba card template và tên/CTA của chúng nằm trong vùng nhìn đầu tiên, không cần page scroll |
| UI-DB-03 | Cả ba template tạo draft thật bằng controller hiện có, không đổi template IDs/schema |
| UI-DB-04 | Project list phản ánh lịch sử mở thật xuyên reload, đóng/mở browser và restart launcher (kể cả đổi port); tên dài/trùng/empty/error được xử lý, không làm project dirty |
| UI-DB-05 | Storage mở riêng, không có Drive form hoặc hàng Drive thường trực trong nội dung chính |
| UI-DB-06 | Vào/ra Editor không làm mất draft, manual dirty semantics, session hoặc job |
| UI-DB-07 | Keyboard tới được template/card/action; browser không có lỗi nghiêm trọng chưa xử lý |

Chưa chạy browser test cho thiết kế này. Kiểm hình học card dùng bounding boxes, không chỉ screenshot. Nếu chọn mật độ khiến UI-DB-02 không đạt, phải sửa wireframe trước code; không âm thầm hạ viewport mục tiêu.

## 7. Phần cần duyệt trước triển khai

D-01 đã chốt lịch sử mở xuyên phiên; wireframe Desktop hai viewport, chi tiết persistence/history, nội dung navigation, vị trí entry vào Storage; mật độ project cards; cách quay lại Editor đang mở. Kết quả này chỉ là đầu vào R0/R1. UI-01 vẫn **Proposed**, không chuyển trạng thái chỉ vì UI-02 đã được duyệt thiết kế.
