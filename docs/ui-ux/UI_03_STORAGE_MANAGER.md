# UI-03 — Google Drive Storage Manager

**Phiên bản:** 0.1 · **Ngày:** 24/11/2026 (Asia/Saigon).

**Trạng thái:** **Proposed — Pending PO Review**, chưa triển khai. DS-P08 yêu cầu hoàn thiện tài liệu riêng; không đồng nghĩa phê duyệt toàn bộ wireframe, endpoint hoặc chuyển dữ liệu mới.

**Nguồn:** [UI-02 §11](UI_02_VIDEO_EDITOR.md), D-03/D-04 trong [Gap Analysis](UI_GAP_ANALYSIS.md), [ADR-0002](../decisions/ADR-0002-DIRECT_GOOGLE_DRIVE.md), [MVP contracts](../architecture/MVP_CONTRACTS.md), [Design System](DESIGN_SYSTEM.md). UI-02 nguyên văn không thay đổi. Các ràng buộc đã duyệt được kế thừa; bố cục/chi tiết mới dưới đây là đề xuất.

## 1. Mục tiêu và phạm vi

Đưa Google Drive ra khỏi nội dung chính của Dashboard/Editor thành Storage Manager riêng, quản lý kết nối, consent, backup, restore và MP4 đã khôi phục. Local Editor không phụ thuộc đăng nhập Google. Không biến Drive thành filesystem/cloud-first hoặc collaboration.

**Kế thừa Approved:** D-03 yêu cầu Storage Manager hoàn chỉnh, progress/error/cancel thật; consent hợp lệ, auto backup mặc định tắt, backup thành công theo backend xác minh, restore kiểm manifest/schema/checksum, không overwrite project local, không xóa nguồn hoặc upload runtime/credentials/models/temp render. Thiết kế theo palette DS-P01, Segoe UI v1, body14/label13/caption12, góc vuông, keyboard và lỗi rõ.

Không suy từ ảnh minh họa các chức năng đã tồn tại: quota1TB/gói Creative, file manager Drive tùy ý, upload file ngoài inventory, nhãn cloud, share link, đổi tên/xóa file cloud, search mọi thư mục hoặc quota tự tính. Muốn bổ sung cần task/contract riêng.

## 2. Entry và cấu trúc đề xuất

- Entry “Lưu trữ” ở Dashboard navigation và lối vào từ Editor. Không hiện form OAuth/backup thường trực trong main workspace.
- Ưu tiên workspace riêng cho dữ liệu dài; dialog rộng960px có thể dùng cho tác vụ ngắn. Loại surface và wireframe cuối chờ PO review; thử ở1366×768/1920×1080 theo DS-P05.
- Header: “Kho lưu trữ”, connection/folder status, đóng/quay lại; body cuộn độc lập nếu modal; footer tóm tắt hoạt động và action phù hợp. Error chi tiết không bị cắt chỉ để giữ header một dòng.
- Nhóm/tab nội dung: Tổng quan; Bản sao lưu; MP4 đã khôi phục; Cấu hình nâng cao. Đây là nhóm UI, không endpoint mới. Active transfer thuộc controller/service, không mất khi đóng workspace.
- Tổng quan hiển thị connected/disconnected, tên folder nếu biết, last backup nếu backend có, auto backup state và task active. Unknown dùng “Chưa có thông tin”, không dữ liệu mẫu giả.
- Bản sao lưu hiển thị danh sách từ API, ngày/name khi có, chọn một manifest và “Khôi phục thành project mới”; ID không phải tên project bảo đảm duy nhất. Search/filter local trên list đã tải được phép đề xuất, không quảng cáo tìm toàn Drive.
- MP4 khôi phục hiển thị file được API quản lý và action tải/xem hiện hữu; không tự tạo waveform/thumbnail hoặc hứa mở OS folder khi chưa có handler được phép.

## 3. Flow chưa kết nối và OAuth

1. Hiển thị “Google Drive chưa kết nối”; local Editor vẫn dùng được.
2. Hướng dẫn OAuth Desktop Client JSON và folder theo flow hiện hữu; chọn file, parse/validate, không echo nội dung credentials hoặc ghi vào project/browser storage.
3. “Lưu cấu hình” rồi “Kết nối Google”; chỉ mở URL được backend trả, không tự thêm scope. Pending OAuth có hướng “Mở Google để tiếp tục” và hủy kết nối theo API hiện hữu.
4. Chờ backend xác nhận connected/folder; không đánh dấu connected chỉ vì mở tab Google. Phân biệt OAuth cancel/expired/config error/network.
5. Ngắt kết nối cần nêu ảnh hưởng, không xóa local. Baseline backend chặn đổi config/disconnect khi transfer running; không dùng disconnect làm nút hủy transfer.

ADR-0002 về session/origin, PKCE/state, DPAPI và quyền folder vẫn là nguồn kỹ thuật; UI-03 không đổi OAuth contract. Không hứa lưu credential an toàn hơn khả năng DPAPI đã nêu.

## 4. Backup và tự sao lưu

**Backup thủ công:** hiển thị inventory/phạm vi upload theo dữ liệu backend thật, consent rõ → chuẩn bị working snapshot qua controller có quyền hợp lệ nếu đang sửa project → POST backup → theo dõi status. Không bypass read-only/revision khi chuẩn bị. Endpoint202 chỉ báo đã nhận, không phải backup thành công. Chỉ thông báo thành công khi terminal state có backend xác minh.

**Tự sao lưu:** default off cho cấu hình mới; chỉ bật bằng thao tác và consent hợp lệ. Đổi toggle pending/failure phản ánh kết quả backend; không tự bật lại sau lỗi. UI ghi rõ ứng dụng phải chạy và có mạng, snapshot mới có thể dùng thêm quota. Không dùng toggle như consent một lần cho mọi hành động tương lai nếu backend chưa có phạm vi consent đó.

**Snapshot an toàn:** local source giữ nguyên; không biến backup thành manual save; save B/edit C vẫn dirty đúng hash. Đóng workspace không đổi auto state, không release project lease. Chỉ account/connection state Drive thay đổi theo flow Drive; quyền Editor vẫn controller R0.

## 5. Restore

1. Tải danh sách backup; empty/error có action refresh rõ, không giữ bản ghi stale như đang online.
2. Chọn manifest, hiển thị metadata thật hiện có và cảnh báo “Khôi phục thành project mới, không ghi đè project trên máy”. Không bịa file count/schema/date chưa được API trả.
3. Xác nhận rồi gửi request hiện có. Đang kiểm manifest/download/verify/publish phải thể hiện đúng phase; unknown progress dùng indeterminate.
4. Backend staging/containment/schema/checksum là lớp kiểm cuối; lỗi/hủy không publish project/MP4 dang dở, không xóa project gốc. Không ghi đè project local đang chỉnh sửa.
5. Thành công refresh danh sách project/MP4 trên Dashboard; không tự mở project mới và bỏ draft đang edit. Cho user chọn “Mở project đã khôi phục” qua navigation/dirty guard.

Metadata preview trước restore và trả danh sách project IDs sau restore cần đối chiếu contract thực tế ở task R5; chưa thêm endpoint trong tài liệu này.

## 6. Capability inventory — baseline `d12015a`

Đã đọc `services/local-api/amvs/app.py`, `drive.py`, `drive_backup.py`, `drive_restore.py` và `apps/web/components/drive-panel.tsx`. “Có trong code” không đồng nghĩa đã chạy test mới hoặc đạt UI-03.

| API hiện có (`/api/v1`)                          | Frontend/behavior hiện có                                                           | Khoảng cách                                                                     |
| ------------------------------------------------ | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| GET `/drive`                                     | Connection/config/folder/auto; backup/restore status+message; backend có lastBackup | Frontend DTO chưa lấy lastBackup; chưa structured byte/phase progress đầy đủ    |
| POST `/drive/configure`                          | `{credentials,folder}`                                                              | Cần form UX lỗi rõ/secret-safe, không thêm raw path                             |
| POST `/drive/connect`                            | URL OAuth                                                                           | Cần pending/failure/cancel state dễ hiểu                                        |
| POST `/drive/disconnect`                         | Ngắt/hủy OAuth khi không transfer                                                   | Không phải cancel backup/restore                                                |
| POST `/drive/auto`                               | `{enabled,confirmed:true}`                                                          | Toggle phải tôn trọng consent, server result                                    |
| POST `/drive/backup`                             | `{confirmed:true}`, trả202; chạy background                                         | Chưa có transfer identity/byte progress/cancel endpoint công bố                 |
| GET `/drive/backups`                             | List metadata manifest                                                              | Có thể dùng làm danh sách backup; không suy là lịch sử operation mọi trạng thái |
| POST `/drive/restore`                            | `{manifestId,confirmed:true}`, trả202                                               | Cần progress/error/cancel và integration refresh project                        |
| GET `/drive/exports`, GET `/drive/exports/{sha}` | Liệt kê/tải MP4 local đã restore                                                    | Không phải list toàn bộ MP4 trên Drive hoặc OS folder opener                    |

Baseline backup/restore có status idle/running/succeeded/failed và message; không lấy `/jobs/{id}/cancel` áp sang Drive vì chưa có Drive job contract tương ứng. D-03 còn thiếu capability thật; di chuyển panel thành dialog chỉ là một phần, chưa được gọi Storage hoàn chỉnh.

## 7. Progress / error / cancel — contract cần review trước code

Đề xuất yêu cầu hành vi, **chưa ấn định endpoint/DTO mới**:

| Nhóm               | Cần chốt                                                                                                              | Hành vi UI bắt buộc theo D-03                                                                           |
| ------------------ | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Identity/lifecycle | operation ID, loại backup/restore, ownership, status/phase, timestamps/terminal durability                            | Đóng/mở lại workspace vẫn tìm đúng task, stale poll không ghi đè task mới                               |
| Progress           | bytes/files done/total khi biết; phase verification/publish; unknown denominator                                      | Có số thật mới hiển thị%; không chạy timer fake; không100% trước verify/publish                         |
| Errors             | auth-expired/permission/quota/offline/corrupt/schema/checksum/local-disk/cancelled/unknown; retryable và safe message | Lỗi phân loại + hướng xử lý, không parse message bằng regex để giả structured code, không log secrets   |
| Cancel             | Request/ack/terminal state; stop upload/download ở boundary an toàn; cancel-vs-publish race; cleanup staged data      | Nút “Hủy tác vụ”, trạng thái “Đang yêu cầu hủy…” đến khi backend xác nhận; close/disconnect khác cancel |
| Retry              | Attempt mới hay resume; idempotence, checkpoint validity, cleanup policy                                              | Không hứa resume từ byte cũ nếu chưa có capability; retry không overwrite backup thành công trước       |
| History            | List operation successes/failures/cancel, retention/persistence/bounds                                                | Backup manifest list không thay history operation; unknown field không bịa                              |
| Compatibility      | Version/default/nullability, existing APIs, old manifests                                                             | Giữ legacy projects/manifests và tests, không sửa schema nội dung để chứa UI progress                   |

Cancel request tới sau publish thành công phải hiển thị kết quả terminal có thật; không chuyển succeeded thành cancelled chỉ vì user vừa click. Cleanup chỉ owned staging, giữ nguồn local và manifest đã xác minh trước đó. Chi tiết orphan chunks/rollback/publish atomicity cần thiết kế backend và tests trước implementation, không coi proposal đã được nghiệm thu.

## 8. States, keyboard và accessibility

Dùng DS E/G/I đã duyệt: button/field/tab/dialog/notification/progress đúng keyboard; Segoe UI, error persistent có reason/action, không toast-only cho mất kết nối/restore fail. Chưa có progress thì hiển thị phase text thật; screen reader announce theo phase thay vì mỗi poll2s.

Tab/Shift+Tab vào các controls theo thứ tự; tabs dùng arrows; modal focus-trap/Escape/return-focus nếu chọn dialog. Escape đóng surface không hủy task; nút Hủy tác vụ riêng. Checkbox consent label đầy đủ, không auto-check. Disabled control có reason ngoài hover; read-only Editor không vô hiệu hóa mọi hành động Storage, mỗi action theo permission riêng.

Khi offline Drive nhưng API local còn hoạt động, edit local tiếp tục; khi session local401, hiển thị cần mở lại phiên, không làm writable giả. Error auth/quota/corrupt phân biệt và giữ message backend an toàn. Không đưa credentials/SQLite temp/model vào screenshot hay trace.

## 9. Acceptance & regression plan — chưa chạy cho UI-03

| ID       | Tiêu chí / evidence cần có                                                                                                      |
| -------- | ------------------------------------------------------------------------------------------------------------------------------- |
| UI-ST-01 | Entry riêng; không còn Drive form thường trực main; mở/đóng không mất draft/job/lease                                           |
| UI-ST-02 | Configure/connect/OAuth cancel/disconnect; không secrets trong DOM/log/project                                                  |
| UI-ST-03 | Consent thật; auto off mặc định, toggle chỉ đổi theo backend xác nhận                                                           |
| UI-ST-04 | Manual backup accepted202 khác succeeded; true status/progress/last backup                                                      |
| UI-ST-05 | List/empty/error/history đúng dữ liệu, không quota/metadata giả                                                                 |
| UI-ST-06 | Restore manifest/schema/checksum, tạo project mới, không overwrite local; refresh danh sách nhưng không tự bỏ draft             |
| UI-ST-07 | True transfer cancel: running→cancelling→cancelled/terminal thật, cleanup owned staging, source giữ nguyên; race publish/cancel |
| UI-ST-08 | Auth expired/quota/network/disk/checksum/schema errors có thông báo và retry đúng capability                                    |
| UI-ST-09 | MP4 đã restore tải/xem được, hash parity, không lộ path                                                                         |
| UI-ST-10 | 1366×768/1920×1080 thử nghiệm, keyboard/labels/focus/reduced-motion, lỗi đọc được trong panel hẹp                               |
| UI-ST-11 | R0 lease/read-only và manual save B/edit C không hồi quy khi mở Storage/chuẩn bị backup                                         |

Browser dùng fixture grants/transport lỗi **ghi nhãn rõ**, backend integration kiểm thật state/cancel/snapshot/checksum; cloud roundtrip thật tách khỏi fixture và chỉ làm với consent được cấp. Không gọi test OAuth local là Google cloud acceptance. Raw artifacts Git-ignore, dùng media tự tạo. Chưa chạy browser/backend/cloud tests mới trong lượt soạn tài liệu.

## 10. Giai đoạn và điểm chờ PO

- **R1:** dùng primitives/style đã duyệt; UI-03 chỉ đặc tả, không tích hợp Drive APIs mới, không gộp Advanced Editor.
- **R5.A:** chuyển manager/entry và các flow hiện có sau wireframe/DS; bảo toàn consent/restore/save, có error/focus tests. Chỉ là giai đoạn A, chưa full D-03.
- **R5.B:** triển khai progress/error/cancel/history thật sau contract/backend review và tests tương ứng. Full UI-03 chỉ nghiệm thu khi đủ capability và browser/backend/cloud evidence theo phạm vi PO chốt.

**Cần PO review:** loại surface workspace/dialog và wireframe, nhóm/navigation, metadata/history scope, delta lifecycle/progress/error/cancel/retry và persistence contract, viewport/keyboard AC và phạm vi cloud verification. Không tự chọn API route/schema hoặc nâng Proposed thành Approved qua việc soạn tài liệu.
