# UI-03 — Google Drive Storage Manager

**Phiên bản:** 1.0 · **Ngày:** 24/11/2026 (Asia/Saigon).

**Trạng thái:** **Approved for Design — Not Implemented**, theo phạm vi ST-01…ST-07. **PO duyệt ngày24/11/2026 (Asia/Saigon)** qua xác nhận “duyệt theo đề xuất” sau bảng ST và bản thảo0.2. Đây là duyệt thiết kế/hành vi và gate kiểm thử, không phải nghiệm thu implementation/cloud hoặc phê duyệt sẵn DTO/endpoint chưa chốt. Các yêu cầu Approved qua UI-02/D-03 tiếp tục giữ hiệu lực.

**Nguồn:** [UI-02 §11](UI_02_VIDEO_EDITOR.md), D-03/D-04 trong [Gap Analysis](UI_GAP_ANALYSIS.md), [ADR-0002](../decisions/ADR-0002-DIRECT_GOOGLE_DRIVE.md), [MVP contracts](../architecture/MVP_CONTRACTS.md), [Design System](DESIGN_SYSTEM.md). UI-02 nguyên văn không thay đổi. Các ràng buộc đã duyệt được kế thừa; ST-01…ST-07 đã được PO chốt. Chi tiết kỹ thuật ngoài phạm vi này còn Proposed/Pending Review như được nêu từng mục.

<a id="storage-decisions"></a>

## 0. Quyết định PO — ST-01…ST-07

**Nguồn:** bảng “Quyết định đề xuất” PO gửi trong hội thoại sau bản thảo0.1 ở commit `dc315d0`. Ban đầu bảng mang nhãn đề xuất; sau đó PO xác nhận **“duyệt theo đề xuất”**, nên ST-01…ST-07 được ghi nhận **Approved for Design** từ ngày24/11/2026. Không thay đổi lịch sử test hoặc coi cloud test đã chạy. Các điểm cần contract review riêng được phân biệt dưới đây.

| Mã    | Quyết định PO                                            | Lý do                                  | Áp dụng vào bản thảo / trạng thái                                                                                                                                   |
| ----- | -------------------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ST-01 | Workspace riêng, không phải dialog960px                  | Nhiều danh sách, lịch sử và tác vụ dài | **Approved**: workspace riêng; không manager dialog960px; UI-02 nguyên văn vẫn giữ, quyết định này chọn workspace trong các phương án được phép                     |
| ST-02 | Bốn tab: Tổng quan, Bản sao lưu, MP4 khôi phục, Cấu hình | Dễ tìm, không kéo dài trang            | **Approved**: đúng bốn tab; không đổi tên hoặc thêm tab lịch sử thứ năm                                                                                             |
| ST-03 | Backup và Restore có progress, error, cancel thật        | Đúng D-03 đã chốt                      | **Approved** yêu cầu hành vi, tiếp nối D-03; DTO/endpoint/lifecycle chi tiết còn cần review trước code                                                              |
| ST-04 | Lịch sử snapshot tách lịch sử tác vụ                     | Backup thành công khác upload lỗi/hủy  | **Approved** tách lịch sử snapshot/tác vụ; chưa ấn định storage schema/retention/API mới                                                                            |
| ST-05 | Mặc định không tự sao lưu, consent rõ                    | Bảo vệ dữ liệu người dùng              | **Approved**, kế thừa UI-02§11/D-03; không bật ngầm khi mở workspace/đăng nhập                                                                                      |
| ST-06 | Bắt buộc cloud test thật bằng tài khoản được cấp quyền   | Mock OAuth không thay kiểm cloud       | **Approved** gate nghiệm thu bắt buộc; tài khoản/folder/phạm vi và consent upload phải được cấp riêng trước test thật, không suy từ chat rằng app đã có OAuth grant |
| ST-07 | Không mất Editor state khi mở/đóng Storage               | Giữ project/draft/render/lease         | **Approved**, kế thừa bảo toàn nghiệp vụ UI-02 và state/lifecycle regression; không giữ writable cũ nếu quyền đã bị takeover trong lúc mở Storage                   |

## 1. Mục tiêu và phạm vi

Đưa Google Drive ra khỏi nội dung chính của Dashboard/Editor thành Storage Manager riêng, quản lý kết nối, consent, backup, restore và MP4 đã khôi phục. Local Editor không phụ thuộc đăng nhập Google. Không biến Drive thành filesystem/cloud-first hoặc collaboration.

**Kế thừa Approved:** D-03 yêu cầu Storage Manager hoàn chỉnh, progress/error/cancel thật; consent hợp lệ, auto backup mặc định tắt, backup thành công theo backend xác minh, restore kiểm manifest/schema/checksum, không overwrite project local, không xóa nguồn hoặc upload runtime/credentials/models/temp render. Thiết kế theo palette DS-P01, Segoe UI v1, body14/label13/caption12, góc vuông, keyboard và lỗi rõ.

Không suy từ ảnh minh họa các chức năng đã tồn tại: quota1TB/gói Creative, file manager Drive tùy ý, upload file ngoài inventory, nhãn cloud, share link, đổi tên/xóa file cloud, search mọi thư mục hoặc quota tự tính. Muốn bổ sung cần task/contract riêng.

## 2. Entry và cấu trúc theo ST-01/ST-02

- Entry “Lưu trữ” ở Dashboard navigation và lối vào từ Editor. Không hiện form OAuth/backup thường trực trong main workspace.
- Theo ST-01, Storage Manager là **workspace riêng**, không dùng dialog960px cho toàn bộ manager. Dialog nhỏ chỉ dành xác nhận thao tác cụ thể, không thay workspace. Wireframe chi tiết vẫn chờ review; thử ở1366×768/1920×1080 theo DS-P05.
- Header: “Kho lưu trữ”, connection/folder status, quay lại Editor/Dashboard; từng vùng danh sách cuộn nội bộ; footer tóm tắt hoạt động và action phù hợp. Error chi tiết không bị cắt chỉ để giữ header một dòng.
- Bốn tab nội dung theo ST-02: **Tổng quan; Bản sao lưu; MP4 khôi phục; Cấu hình**. Đây là nhóm UI, không endpoint mới. Active transfer thuộc controller/service, không mất khi đóng workspace.
- Tổng quan hiển thị connected/disconnected, tên folder nếu biết, last backup nếu backend có, auto backup state và task active. Unknown dùng “Chưa có thông tin”, không dữ liệu mẫu giả.
- Bản sao lưu hiển thị danh sách từ API, ngày/name khi có, chọn một manifest và “Khôi phục thành project mới”; ID không phải tên project bảo đảm duy nhất. Search/filter local trên list đã tải được phép đề xuất, không quảng cáo tìm toàn Drive.
- MP4 khôi phục hiển thị file được API quản lý và action tải/xem hiện hữu; không tự tạo waveform/thumbnail hoặc hứa mở OS folder khi chưa có handler được phép.

### 2.1. Snapshot khác tác vụ — ST-04

- **Danh sách snapshot:** trong tab Bản sao lưu; chỉ biểu diễn snapshot/manifest đã publish và xác minh thành công, có action restore. Không tạo snapshot card cho upload đang chạy/lỗi/hủy. Khi backend list chưa đủ metadata, hiển thị trường đã biết, không tự bổ sung timestamps/count giả.
- **Lịch sử tác vụ:** vùng riêng trong tab Tổng quan (mặc định) và liên kết xem chi tiết từ Bản sao lưu; ghi attempt backup/restore, trạng thái running/succeeded/failed/cancelled/interrupted theo contract được review. Không cần tab thứ năm. Backend chưa lưu/trả lịch sử đầy đủ thì ghi capability thiếu, không tạo history giả bằng polling memory rồi gọi là durable history.
- Task thành công có thể liên kết snapshot ID; failed/cancelled không được coi như snapshot có thể restore. Restore attempt tham chiếu snapshot nguồn, không sửa lịch sử snapshot. Attempt retry phải phân biệt attempt cũ; không xóa lỗi cũ để lịch sử trông thành công.
- Search/filter, retention, pagination, thời điểm ghi record và liên kết operation↔snapshot là Proposed; chốt nullability/compatibility/bounds trước API/DB code.

### 2.2. Bảo toàn Editor — ST-07

Workspace navigation dùng chung application controller; không tạo Api/editor identity mới hoặc unmount project/history/draft/job state khi chuyển sang Storage. Selection/playhead/dirty state, lyrics draft chưa apply, render đang chạy và UI preferences giữ theo policy hiện hành. View có thể được ẩn/hiện để tiết kiệm tài nguyên nhưng state authority không được reset theo tab.

Không release lease khi chỉ mở/đóng Storage; heartbeat/loss/reconnect của R0 tiếp tục hoạt động. Nếu tab khác takeover hoặc TTL/network khiến quyền đổi trong lúc ở Storage, quay lại Editor phải phản ánh quyền mới nhất, không khôi phục canWrite cũ từ snapshot UI. Đóng Storage không hủy render/AI/Drive transfer. Restore success chỉ refresh danh sách, mở project khác vẫn qua dirty guard.

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

Baseline backup/restore có status idle/running/succeeded/failed và message; không lấy `/jobs/{id}/cancel` áp sang Drive vì chưa có Drive job contract tương ứng. D-03 còn thiếu capability thật; di chuyển panel thành workspace chỉ là một phần, chưa được gọi Storage hoàn chỉnh.

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

**Bổ sung theo ST-01…ST-07 (kế hoạch kiểm, chưa chạy):**

- Workspace riêng có đúng bốn tab, đóng/quay lại đúng context; dialog confirm không biến thành manager960px. Snapshot list không chứa task failed/cancelled; task history vẫn giữ failed attempt sau retry thành công.
- Backup/restore thật → kiểm bytes/hash/content parity, manifest/schema/checksum; lỗi/hủy trong quá trình transfer, race cancel-vs-publish, nguồn local và backup đã thành công trước còn nguyên. Không gắn nhãn cloud-tested cho fixture HTTP hoặc OAuth local.
- Khi mở Storage từ Editor: project ID/contentHash/manualSavedHash/dirty/history/selection/playhead và lyrics draft được bảo toàn; render đang chạy còn theo dõi/cancel được. Nếu playback pause khi navigation phải giữ đúng vị trí theo policy được review, không reset về0.
- Hai tab: A mở Storage, B takeover project; A trở về Editor phải read-only. A mất heartbeat/lease khi ở Storage phải giữ draft và không writable giả. Save B/edit C rồi chuyển workspace không làm C sạch dirty; Undo/Redo vẫn đúng sau quay lại.
- Auto backup off trên config mới; mở/đóng/tab-switch/login không tự cấp consent hoặc bật auto. Nếu config trước đó đã được user bật hợp lệ, phản ánh state server, không reset setting chỉ vì remount.

### 9.1. Cloud verification gate — ST-06

Trước test phải xác nhận tài khoản được phép, folder thử riêng, quyền app OAuth thật và inventory media tự tạo; không ghi credentials/token trong artifact. Upload/restore/MP4 roundtrip và source/no-overwrite cần evidence thực: run/source version, terminal statuses, checksums, kết quả đối chiếu và cleanup owned test artifacts theo phạm vi đã cấp. Error/cancel phải có transfer thật khi khả thi; lỗi quota không thể gây an toàn có thể bổ sung fixture được ghi nhãn, nhưng fixture không thay cloud success/cancel coverage thực và gap còn phải báo PO.

Không có tài khoản/grant/folder/consent phù hợp thì chặn phần cloud test, không chặn công việc tài liệu hoặc local regression độc lập; không đánh dấu full UI-03 Passed. Không gọi Drive connector trong chat là OAuth grant cho ứng dụng Hòa Âm. Lượt ghi nhận ST này không upload/download hoặc chạy cloud test.

Browser dùng fixture grants/transport lỗi **ghi nhãn rõ**, backend integration kiểm thật state/cancel/snapshot/checksum; cloud roundtrip thật tách khỏi fixture; theo ST-06 là **gate bắt buộc đã được PO duyệt** trước nghiệm thu đầy đủ UI-03. Dùng tài khoản/folder được cấp quyền và consent upload đúng inventory; không có quyền thì ghi Blocked/Not run, không thay bằng mock pass. Không gọi test OAuth local là Google cloud acceptance. Raw artifacts Git-ignore, dùng media tự tạo. Chưa chạy browser/backend/cloud tests mới trong lượt soạn tài liệu.

## 10. Giai đoạn và phần kỹ thuật cần review

- **R1:** dùng primitives/style đã duyệt; UI-03 chỉ đặc tả, không tích hợp Drive APIs mới, không gộp Advanced Editor.
- **R5.A:** chuyển manager/entry và các flow hiện có sau wireframe/DS; bảo toàn consent/restore/save, có error/focus tests. Chỉ là giai đoạn A, chưa full D-03.
- **R5.B:** triển khai progress/error/cancel/history thật sau contract/backend review và tests tương ứng. Full UI-03 chỉ nghiệm thu khi đủ capability và browser/backend/cloud evidence theo phạm vi PO chốt.

**Đã chốt:** ST-01…ST-07 Approved for Design — workspace riêng, bốn tab, progress/error/cancel thật, hai loại lịch sử tách biệt, auto backup mặc định tắt/consent rõ, cloud test thật và bảo toàn Editor state. Không cần xin duyệt lại các quyết định này.

**Còn cần review trước phần triển khai phụ thuộc:** wireframe/kích thước chi tiết, metadata/history retention và contract lifecycle/progress/error/cancel/retry/persistence. Môi trường/tài khoản/folder/quyền app/consent cloud phải có trước test thật. Lệnh duyệt thiết kế không tự commit/push/merge hoặc tự upload dữ liệu trong phiên này. Không tự chọn API route/schema hoặc nâng Proposed thành Approved qua việc soạn tài liệu.
