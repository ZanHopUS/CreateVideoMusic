# UI Redesign Plan — R0–R6

**Cập nhật implementation R0:** PO đã cho phép sửa riêng Editor Lease/read-only; đã triển khai, chạy regression và kiểm lại C06. Sẵn sàng review chức năng R0 lease với giới hạn timing/native picker; xem [kết quả triển khai và evidence](UI_R0_LEASE_FIX_RESULTS.md). Các mô tả “chưa sửa” bên dưới là baseline/chẩn đoán lịch sử; R1–R6 và UI redesign chưa triển khai.

**Dự án:** Hòa Âm / AI Music Video Studio

**Ngày:** 24/11/2026 (Asia/Saigon)

**Trạng thái:** Proposed implementation plan — R0 lease diagnosis đã được giao và thực hiện; R1–R6 chưa triển khai

**Nhánh khảo sát:** `dev` · **HEAD:** `ba60ab0` · không tạo nhánh mới

**Nguồn:** [UI-01 Proposed](UI_01_DASHBOARD.md), [UI-02 Approved for Design nguyên văn](UI_02_VIDEO_EDITOR.md), [UI-03 Approved for Design](UI_03_STORAGE_MANAGER.md), [UI-04 Export Approved for Design nguyên văn và phụ lục kỹ thuật](UI_04_EXPORT_WORKSPACE.md), [UI-05 Project Management Approved for Design và phụ lục kỹ thuật](UI_05_PROJECT_MANAGEMENT.md), [UI-06 Settings Approved for Design và phụ lục kỹ thuật](UI_06_SETTINGS_WORKSPACE.md), [Gap Analysis](UI_GAP_ANALYSIS.md).

**Cập nhật R0:** đã đọc lại toàn bộ UI/UX, tái hiện browser trên hai modes và chạy 3 integration tests về lease/revision. [Báo cáo R0](UI_R0_LEASE_DIAGNOSIS.md) xác định race response cũ và các nhánh lỗi liên quan. Không sửa application code, không vô hiệu hóa lease. Đây chỉ là hoàn tất phần diagnosis; wireframe/contracts và R0 tổng thể chưa đóng.

## 1. Mục tiêu, quyền hạn và điều kiện vào

Tổ chức lại giao diện thành Creative Dashboard và professional Editor, giữ toàn bộ chức năng/data/business logic đã có. Bản UI-02 đầy đủ do PO cung cấp được lưu nguyên văn, không tự suy diễn các yêu cầu còn thiếu. Approved for Design không phải quyền triển khai code. R0–R6 dưới đây là các giai đoạn **dự kiến**, không phải các sprint đã chạy.

Lượt lập kế hoạch ban đầu chỉ tạo bốn tài liệu. Theo lệnh R0 mới, đã bổ sung công cụ chẩn đoán/browser evidence và báo cáo; không sửa application code/tests cũ, DB, API contracts, schema hoặc renderer, không commit/push/merge. Các file code được liệt kê trong từng R là file **dự kiến** sau khi kế hoạch được duyệt. R0 lập contract delta có mục đích theo D-01…04 và bằng chứng lease; không lấy redesign làm quyền refactor toàn bộ backend. Bản UI-02 nguyên văn được giữ bất biến; đây là bổ sung hướng thiết kế của PO.

**Cập nhật quyết định PO 24/11/2026:** D-01 lưu lịch sử mở xuyên phiên; D-02 giữ đầy đủ yêu cầu và triển khai hai giai đoạn; D-03 Storage Manager hoàn chỉnh với progress/error/cancel thật; D-04 preferences local độc lập project; D-05 compact + fullscreen Preview riêng. D-06 chuẩn hóa Asset DTO/Media Metadata giữ trạng thái Recommended Decision. Xem sổ quyết định trong Gap Analysis.

Các quyết định này thay phương án memory-only và UI-only trước đó, chưa phải lệnh triển khai. R0 phải thiết kế/review persistence và các delta tối thiểu của API/schema/composition cần cho capabilities mới; chỉ sau khi kế hoạch triển khai được duyệt mới sửa code. Không bỏ yêu cầu UI-02, không gọi phase A là full completion.

## 2. Kiến trúc component đề xuất

Tên file/component là đề xuất, không phải public API hoặc file đã có. Không thêm state-management/UI library chỉ để thay layout; React hooks/context + CSS hiện có đủ làm nền, dependency mới phải có lý do và được xem xét riêng.

```text
Studio (application controller chỉ mount một lần)
├── DashboardWorkspace
│   ├── DashboardNavigation
│   ├── DashboardHeader / CompactIntro
│   ├── TemplateGallery (3 templates thật)
│   └── ProjectList (recent semantics đã được duyệt)
├── EditorWorkspace
│   ├── EditorHeader (back, name, save state, undo/redo, lease, save/export)
│   ├── EditorBody (Grid 3 columns)
│   │   ├── LeftToolPanel
│   │   │   ├── MediaLibrary / MediaImport / MediaPreview
│   │   │   ├── TextTools
│   │   │   ├── LyricsWorkspace (Recognition / EditingAlignment / Styling)
│   │   │   ├── EffectsPanel
│   │   │   └── TemplatesPanel
│   │   ├── PreviewViewport / PreviewTransport
│   │   └── ContextualInspector
│   │       └── Project | Image | Video | Audio | Text | Lyrics | MusicCard
│   ├── TimelineResizeHandle
│   ├── TimelineDock (toolbar, ruler, headers/tracks, clips, playhead)
│   └── EditorStatusBar / background job summary
└── WorkspaceHost / DialogHost
    ├── StorageManager (Drive + lối vào local storage tools)
    ├── ProjectDataDialog (recovery/package/relink/delete)
    └── ExportDialog (preset/folder/preflight/job/output)
```

Controller refactor tăng dần từ `useStudio`; không tạo controller/API/history riêng trong Dashboard hoặc mỗi tab. Các hook phụ dự kiến `use-editor-lease`, `use-editor-ui`, `use-lyrics-workspace`, `use-drive-storage`, `use-timeline-resize` chỉ tách trách nhiệm, không tạo bản project authority thứ hai.

- Dashboard navigation state tách khỏi `project === null`; vào Dashboard không đồng nghĩa xóa project đang mở. Dùng dirty guard, flush working state theo quyền hợp lệ, giữ manual dirty và background jobs.
- Storage theo ST-01 đã duyệt dùng workspace riêng; Export/ProjectData có dialog theo spec tương ứng. Application controller không remount khi chuyển workspace; đóng surface không hủy render/ASR/Drive transfer. Export còn job thì status summary vẫn truy cập được.
- Chuyển tool tab không remount draft controller. Panel body có thể unmount phần view nếu draft/job/subscriptions đã được giữ ở workspace controller.
- Một Player giữ ref ổn định trong Editor; không tạo Player mới chỉ vì Inspector selection, tool tab hay timeline height đổi.
- Đề xuất tiếp tục một trang `/` với workspace state; không thêm Next routes/deep-link trong đợt này vì bootstrap hiện yêu cầu exact Referer `/`. Nếu PO muốn routing mới, phải review session/navigation riêng.

## 3. Viewport, Grid/Flex và Timeline resize

### 3.1. Sơ đồ và đề xuất CSS (chỉ thiết kế)

```text
┌────────────────────────────────────────────────────────────────┐
│ Header: Dashboard | Project | Save state | Undo/Redo | Save/Export│
├───────────────┬───────────────────────────────┬────────────────┤
│ Left tool tabs│ Preview giữ đúng aspect ratio│ Inspector      │
│               │                               │ theo selection │
│ Scroll riêng  │ Transport ngay dưới preview   │ Scroll riêng   │
├───────────────┴───────────────────────────────┴────────────────┤
│ Resize separator / keyboard action                            │
├────────────────────────────────────────────────────────────────┤
│ Timeline toolbar + ruler + track headers/tracks + playhead      │
│ Cuộn tracks riêng; horizontal zoom/scroll đồng bộ header/ruler    │
├────────────────────────────────────────────────────────────────┤
│ Status / background jobs                                       │
└────────────────────────────────────────────────────────────────┘
```

```css
/* Minh họa trong tài liệu; chưa phải application CSS. */
.editor-shell {
  height: 100dvh;
  display: grid;
  grid-template-rows: var(--header-h) minmax(0, 1fr) var(--resize-h)
    var(--timeline-h) var(--status-h);
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}
.editor-body {
  display: grid;
  grid-template-columns: var(--tool-w) minmax(0, 1fr) var(--inspector-w);
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}
.panel { display: flex; flex-direction: column; min-width: 0; min-height: 0; }
.panel-scroll { flex: 1; min-height: 0; overflow: auto; overscroll-behavior: contain; }
.preview-column { display: grid; grid-template-rows: minmax(0, 1fr) auto; min-height: 0; }
```

Bật scroll lock cho html/body **chỉ khi ở Editor**, cleanup đúng khi về Dashboard/dialog đóng; không khóa scroll toàn app bằng global `body {overflow:hidden}` vĩnh viễn. Các ancestor của grid/flex phải có min-height/min-width=0; chỉ đặt overflow ở scroll owner, tránh nested scroll vô ý. Header/status không tăng chiều cao tùy tiện khi status text dài; dùng status row giới hạn và disclosure/error dialog vẫn đọc đủ.

Kích thước gợi ý của UI-02 giữ nguyên: header 56px, tool/inspector 280–320px, timeline 260–320px, min khoảng 180px, max khoảng 55% khả dụng. Đây là điểm khởi đầu để kiểm 1366×768 và 1920×1080, không phải token production đã khóa. Đề xuất thử timeline 260px ở 1366×768 và 300px ở 1920×1080. Budget trừ header/status/separator/transport trước khi tính preview. Không hy sinh Preview/Timeline bằng cách xếp Inspector xuống dưới như breakpoint cũ.

Preview fit bằng container dimensions và project ratio, letterbox UI ngoài composition; không thay `compositionWidth/Height/fps` để vừa panel. Overlay safe area chỉ UI, không ghi vào MP4/content. D-05 đã chốt compact layout cho viewport nhỏ/browser zoom; mọi action quan trọng có lối tới được, không clip im lặng. Fullscreen Preview là mode riêng do user chủ động, tạm thay bố cục thường; Escape/thoát fullscreen phục hồi layout và playhead/selection, kiểm lại quyền hiện hành. Chỉ normal desktop workspace bắt buộc đồng thời Preview/Inspector/Timeline; không tự công bố mobile support.

### 3.2. Resize design

- Separator nằm giữa body và timeline, chiếm một grid row; không dùng `position:fixed` chồng lên tracks/preview.
- Pointer capture, pointermove/pointerup/pointercancel và lost-capture cleanup. Lưu baseline pointerY/height, cập nhật CSS variable bằng rAF trong kéo; commit UI state một lần cuối, không tạo history transaction từng pixel.
- `available = shellHeight - header - status - separator`; `max = min(0.55 * available, available - minimumBodyHeight)`; clamp requested height giữa min và max. Nếu available không đủ cả min timeline và body, dùng compact policy rõ ràng thay vì clamp range ngược.
- ResizeObserver/window resize clamp lại current height, không ghi project content hoặc gọi PATCH mỗi frame. Tab switch/escape/pointercancel không để listeners tồn tại hoặc cursor bị kẹt.
- Keyboard separator: focus visible, `role=separator`, `aria-orientation=horizontal`, value min/max/now, nhãn “Thay đổi chiều cao timeline”; ArrowUp/Down từng bước, Home/End về giới hạn, nút “Khôi phục chiều cao” riêng. Kích thước bước là đề xuất R1.
- Resize không tác động contentHash/manualSavedHash/Undo stack; timeline horizontal zoom và playhead giữ semantics hiện tại. Track headers sticky; ruler và clips dùng cùng content width/scroll offset; không thay timeline zoom khi đổi chiều cao.

## 4. State ownership và hợp đồng giữ nguyên

| State | Owner đề xuất | Quy tắc |
|---|---|---|
| Project content, history | Controller/domain hiện có | Một nguồn duy nhất; mọi edit qua transaction/validation/remapLyrics; không có form copy ghi last-write-wins |
| Revision/manualSavedHash/dirty | Record/serial sync | Keep optimistic revision; hash content tách view; working save không clear dirty; save B/edit C vẫn dirty |
| Session/API editor ID | Application controller | Stable trong vòng đời tab; token chỉ memory; không thêm vào URL/query/localStorage/project/log |
| Selection/playhead/zoom/panels cũ | Existing view adapter | Giữ tương thích selection/timelineZoom/playheadTicks/boolean panels; invalid/missing state fallback an toàn |
| Workspace/activeTool/lyricsMode/timelineHeight | UI controller riêng | D-04: session state được hydrate/ghi preferences local có version, tách content/hash/manual save; store/backend settings delta thiết kế ở R0, không nhét vào project view |
| Lyrics input/lines/audio/model/job | Lyrics controller theo project | Giữ draft qua mode/panel/dialog; tách draft, reviewed và applied (derived from lyric timeline items), không thêm Applied enum |
| Render/AI/package job | Controller/jobs API | Lifecycle độc lập việc mở/đóng view; không trộn succeeded ASR/package với MP4 |
| Drive state/consent/transfer | Storage controller độc lập project | Không reset consent thành true khi remount; không bật auto-sync khi mở manager; reuse backend autoSync đã được user bật |
| Numeric field đang nhập | Form UI local | Có thể nhập tạm chuỗi chưa hợp lệ; chỉ commit value hợp lệ qua domain; drag slider batch một history action, Escape cancel |

Baseline contracts và bất biến cần bảo toàn; delta theo D-01…04 thiết kế riêng:

| Boundary | Đang dùng | Điều cần giữ |
|---|---|---|
| Session/proxy | `/session/bootstrap`, `/session`, exact Host/Origin/Referer, bearer + x-amvs-editor | Cookie media chỉ GET/HEAD; không mở rộng trust để chữa lỗi lease |
| Project | GET/POST `/projects`, GET/PATCH/DELETE `/projects/{id}`, POST `/projects/{id}/save`, `/projects/open` | Expected revision, 409 conflict, preserve local draft/manual hash; không ghi arbitrary path |
| Lease | POST `/projects/{id}/editor-session` `{takeover,assetPins?,pinAllAssets?}` → `{canWrite,expiresInSeconds}`; DELETE release | 5s heartbeat / 30s expiry hiện có; không bỏ lease hoặc revision để UI dễ ghi |
| Assets | POST multipart `{file,rightsConfirmed}`, GET `/assets`, `/content`, `/thumbnail`, PATCH `/tags`, POST `/suggestions`, `/relink` | Opaque IDs, source bytes, rights, 2GiB/file validation; thumbnails regenerated riêng |
| Lyrics | POST `/lyrics/jobs`, `/lyrics/alignment`, GET `/jobs/{id}/lyrics` | ProjectId/revision/audioItemId, ngôn ngữ/model/lines; draft/provenance/fallback/timebase đúng nguồn |
| Templates | GET/POST `/templates`, POST `/templates/{id}/instances` | Typed bindings, IDs mới, template gốc bất biến |
| Data/storage | `/recoveries`, `/restore`, `/packages`, `/media-status`, `/storage/policy`, `/cache/cleanup`, `/source-gc`, `/temp/cleanup` | Consent/revision/checksums/pins; giữ toàn bộ entry chức năng hiện có |
| Drive | `/drive`, `/configure`, `/connect`, `/disconnect`, `/auto`, `/backup`, `/backups`, `/restore`, `/exports` | lastBackup đã có; backup all-inventory consent, no overwrite, no auto deletion, no credentials/DB/temp upload |
| Export | POST `/folder-grants` scope export → grant; POST `/jobs` `{projectId,revision,grantId}`; polling/cancel/output/open-folder | Bắt snapshot đúng revision; grant chỉ ID+label; queued không phải succeeded; retry job mới |
| Composition | project/schema v1, ticks 48000, orderedTracks/items, speed rational, style fields | Player/MP4 cùng scene, không thêm CSS editor làm đổi scene inheritance/render output |

Lưu ý API inventory: `GET /projects` là list; GET/PATCH/DELETE thao tác một project ở `/projects/{id}`. Các tên rút gọn trong bảng không cho phép thêm method chưa tồn tại. Bảng trên là baseline cần bảo toàn tương thích. D-01/D-04 cần metadata/preferences local độc lập project; D-03 cần transfer progress/error/cancel thật; D-02 giai đoạn B có thể cần field/capability mới. Các delta này phải được thiết kế/review ở R0 trước code, không sửa âm thầm endpoint cũ. Client có thể giữ status/code response hiện hữu. Không đưa UI preferences vào project DTO hoặc biến settings thành project revision.

## 5. Phương án lease P0, không bỏ optimistic concurrency

Đề xuất state machine frontend (không persisted DTO):

```text
idle → claiming → writable | readOnly | error
writable → uncertain (heartbeat/network) → checking → writable | readOnly | error
readOnly → takingOver (explicit consent) → reloading → claiming → writable | error
bất kỳ state → sessionExpired khi 401 → bootstrap/reconnect có kiểm soát
```

- Chỉ writable mới cho project mutations/manual save/undo/redo theo policy. Selection, seek, đọc media và đọc output vẫn được; catalog/global storage permissions xét riêng. UI vừa báo quyền vừa chặn handler; backend vẫn là lớp kiểm cuối.
- Duy trì generation/operation ID + project ID cho claim/load/takeover/sync. Ignore response stale; cancel timer/listener khi generation đổi. Không dùng `setWritable(true)` trước khi đã có lease và loaded revision tương ứng.
- Takeover yêu cầu xác nhận ảnh hưởng local draft, gửi POST thật, kiểm canWrite, load latest, reset history theo semantics adopt hiện tại; một luồng điều phối thay vì nhiều claim chồng. Error/denial phải hiện nguyên nhân an toàn và retry/reload; không `.catch(() => {})` ở action cuối.
- Khi 409, giữ draft tại tab, kiểm lại lease và fetch latest để phân biệt stale revision vs mất quyền; không tự PATCH lại với revision mới bằng content cũ. Không dùng last-write-wins, không discard draft không consent.
- Khi heartbeat không chắc chắn, hiển thị đang kiểm tra/mất kết nối; đóng quyền ghi bảo thủ đến khi xác minh. Manual reacquire sau owner đóng/hết hạn; chỉ enable sau load latest. Không tự takeover qua tab khác.
- Preserve undo/history asset pins khi đổi panels hoặc read-only. Khi user đồng ý takeover/reload có thể reset history theo bản server mới; không replay lịch sử của snapshot cũ lên revision mới.
- Launcher restart → token/Api session mới; tái bootstrap và claim, kiểm revision, không giả định phiên cũ còn quyền. Không thử restart launcher thật của user trong khảo sát.
- Backend không có row thì guard cho qua và các job/catalog endpoints có policy riêng: ghi rõ giới hạn thay vì hứa exclusive fencing mọi API. Nếu reproduction yêu cầu sửa guard, body/error code hoặc server ownership, trình task backend riêng trước khi làm.

R0 phải tái hiện/trace trước khi xác nhận root cause; R2 sửa tối thiểu trong frontend theo bằng chứng. Trace không persist token/editor capability thô hoặc project/media private.

## 6. Di chuyển chức năng và capability policy

| Vùng cũ | Đích đề xuất | Bảo toàn và bổ sung UI trên field có sẵn |
|---|---|---|
| Import bar + library trong ProjectTools | Media tab | Rights/batch/partial failure/search/tags/audio listen/reuse/suggestions; thêm type filter, video preview, mime label, thumbnail fallback/retry |
| Add text ở Timeline, text styles Inspector | Text tab + typed Inspector | Add/select layer giữ IDs/history; preset chỉ tổ hợp style hiện hữu, không renderer mới |
| LyricsPanel + lyric Inspector | Lyrics ba mode + Lyrics Inspector | Draft controller giữ khi đổi mode; Recognition import/job, Editing sentence/word data và nghe source, Styling applied items; style không đổi timing |
| Effects select | Effects tab + Inspector | Group none/fade/slide/scale thật; effect preview dùng shared composition. Không fake supported rotation/zoom/filter |
| Templates details | Templates tab | Save slots/new instance/template immutability; vẫn có lối chọn 3 template chuẩn |
| Project name/duration/preset trong Inspector | Header rename + Project Inspector khi không chọn clip + Export configuration | Dùng cùng action; bỏ selection để tới Project Inspector, không giữ hai bản preset khác nhau |
| Recovery/package/relink/delete | ProjectDataDialog | Preserve consent/manual dirty/revision/package snapshot; local cache/quota/source GC có lối vào Storage tools |
| DrivePanel thường trực | StorageManager workspace riêng (ST-01 Approved for Design) | Poll/store ngoài view, last backup/history/exports; refresh project list sau restore success, không tự adopt overwrite current |
| Inline render/job-panel | ExportDialog + background status | Theo dõi job sau đóng dialog/quay Dashboard; reopen kết quả, cancel/retry/MP4/open folder |

**Export preset:** hiện preset nằm trong project content và ảnh hưởng preview + rescale x/y/font. Export dialog phải gọi cùng action preset qua history; có thể dùng lựa chọn tạm trong form, nhưng chỉ có một giá trị áp dụng. Cancel trước apply không sửa project; sau apply dirty đúng semantics, phải hiển thị rõ. Không gửi preset override ngoài DTO hiện hành. Folder được chọn bằng native grant, không nhập absolute path vào API. Resource state lấy job admission/message thật; chưa có preflight RAM endpoint độc lập nên không hiển thị “đủ RAM” giả.

**D-02 — phân kỳ đề xuất:** Giai đoạn A (R1–R5.A) làm Dashboard/workspace/lease/resize và di chuyển capabilities đang có. Giai đoạn B (R4.B/R5.B, sau baseline A) hoàn thiện các yêu cầu advanced còn thiếu bằng thay đổi tối thiểu đã review; giữ source mapping/history/preview-export parity. Không dựng zoom/rotation/card-layout/progress-style giả bằng CSS Editor. R6 có checkpoint A, nhưng chỉ nghiệm thu toàn bộ sau B. Phân chia này là đề xuất kỹ thuật, không suy thành quyền code hoặc waiver cho requirements.

**D-03 — Storage hoàn chỉnh:** R5.A chuyển đầy đủ UI với contract hiện tại; R5.B bổ sung transfer progress backend thật (bytes/count/phase có nguồn đo), structured safe error categories và cancel transfer. Schema/status transition/cancel scope phải mô tả trước code; cancel idempotent, cleanup đúng task, không xóa source/local hoặc backup thành công cũ, không publish manifest khi chưa verify. Đóng Storage workspace không hủy job; cancel OAuth không thay cancel upload. Không báo full Storage acceptance nếu B chưa đạt.

**D-01/D-04 — persistence local (đề xuất kỹ thuật):** dùng metadata/preferences store có version ngoài dữ liệu project, ví dụ sidecar do backend quản lý; xác định atomic write, corruption fallback, reset, scope workspace/user và multi-tab policy ở R0. Không phụ thuộc localStorage theo origin đơn lẻ vì launcher thay port. Recent chỉ lưu ID/thời điểm mở thật, không biến GET/poll thành lần mở; preferences chỉ field giao diện được duyệt. Không lưu bearer/editor token, credentials hoặc draft lyrics vào preferences; không upload store này lên Drive mặc định. Tests phải chứng minh reload/restart/port-change giữ dữ liệu, không đổi contentHash/manualSavedHash/revision/Undo.

**D-06 — Recommended Decision:** chuẩn hóa Asset DTO/Media Metadata; chưa chốt thêm/sửa field. R0 đề xuất inventory field thực: id/name/kind/mime/tags/bytes, dimensions khi là visual, durationTicks khi nguồn có thời lượng, codec khi probe có; nêu required/optional/null, ticks=48000/s, unknown vs not-applicable và defaults của metadata cũ. Không dùng extension làm codec, không phơi bày absolute file path hoặc chế metadata chưa probe. Liệt kê diff frontend/backend, contract tests và compatibility strategy để PO review trước triển khai.

## 7. Các giai đoạn R0–R6

### R0 — Baseline, scope và tái hiện lease

**Tiến độ:** diagnosis đã có evidence thật: 6/6 race checks chặt, controls và fault cases, 3 integration pass; full R0 còn wireframe/technical contract review. Không sửa lease/backend để làm phép đo xanh.

- **Mục tiêu:** chốt nguồn đặc tả, gap/capability decisions, wireframes hai viewport và baseline trước thay đổi; tìm repro lease P0.
- **File dự kiến:** bốn tài liệu UI/UX; sau khi được phép viết tests: `tests/e2e/editor-lease.spec.ts`/`editor-layout.spec.ts` (mới), fixture server và notes evidence dưới `.local` Git-ignored. Không sửa backend để đoán lỗi.
- **Dependency:** PO duyệt phạm vi thực thi; UI-01 wireframe còn Proposed; D-01…05 đã chốt hướng; còn technical contracts và D-06 Recommended cần review. Runtime/setup đang có; media tự tạo/disposable workspace.
- **Acceptance Criteria:** requirements → component/API/tests map đầy đủ; current UI screenshot + geometry ở hai desktop viewport; lease repro một/hai tab/expiry/close/restart và failure trace; hypothesis tách khỏi confirmed cause. Mục chưa tái hiện phải ghi chưa tái hiện, không bịa kết luận.
- **Test plan:** chạy baseline core browser không heavy trước; integration lease/revision và queued-save race; ghi exact command/version/source hash. Mỗi test có trạng thái thực, không lấy pass lịch sử làm baseline mới. Rerender khi đủ RAM, không giảm admission.
- **Rủi ro:** user environment khác fixture; privacy/credentials; stale RTM; approval gap do capability thiếu.
- **Điều kiện hoàn thành:** PO duyệt UI-01 wireframe/phạm vi, quyết định capability có đường xử lý; baseline artifacts/repro hoặc ghi rõ inconclusive + kế hoạch chứng minh. Không chuyển sang code các phần còn blocker.

### R1 — Design System v1.0 và Dashboard

**Cập nhật 24/11/2026:** PO đã chọn **Phương án 2 — Minimal Professional** và [nghiệm thu riêng R0 lease](UI_R0_LEASE_FIX_RESULTS.md#po-acceptance-r0). Sau bản thảo [Design System v1.0](DESIGN_SYSTEM.md) và [audit](UI_DESIGN_AUDIT.md), PO đã duyệt DS-P01…DS-P07 theo phạm vi ở DS§11; DS-P08 đã có [UI-03 riêng](UI_03_STORAGE_MANAGER.md) Approved for Design theo xác nhận PO cho ST-01…ST-07. Chưa triển khai code trong lượt ghi nhận quyết định này. Ghi nhận này cập nhật dependency R1, không tự đóng wireframe/contracts của R0 tổng thể hoặc rewrite R2/R3–R6.

- **Mục tiêu:** tokens/primitives thống nhất theo style Approved (radius0, panel phẳng, lavender xám, không glow/gradient trang trí); Dashboard template-first/recent/navigation/entry Storage giữ định hướng UI-01. Palette, Segoe UI, body14/label13/caption12 và component/interaction đã duyệt; DS-P05 chỉ duyệt thử1366×768/1920×1080, chi tiết ngoài phạm vi vẫn Proposed/Pending Approval.
- **Phân chia:** R1.A foundations — tokens, UI primitives, state/keyboard/focus specimens, CSS scoping; R1.B Dashboard — chỉ tích hợp sau wireframe, navigation/dirty semantics và D-01 metadata contract được duyệt. DS-P07 cho phép triển khai từng phần theo thứ tự này; không gộp Advanced Editor. Quyền code đến từ quyết định PO, không phải từ việc có tài liệu.
- **File hiện tại (docs-only):** `docs/ui-ux/DESIGN_SYSTEM.md`, `UI_DESIGN_AUDIT.md`, phần R1/dependency trong plan này; UI-03 cùng bản ghi ST-01…ST-07 Approved for Design theo DS-P08. Bản ghi R0 acceptance đã có, không thay evidence lịch sử. Không sửa application files.
- **File dự kiến khi được giao code:** `apps/web/app/globals.css` (chỉ reset/token scope), `components/ui/*` và CSS Modules cho Button/IconButton/Field/Input/Textarea/Select/Checkbox/Toggle/Slider/Tabs/Tooltip/Popover/Dialog/Status/Progress; card/InspectorField/Timeline primitives tích hợp theo phase thực; `components/dashboard/*`, `studio.tsx` và navigation state ở R1.B. Persistence adapter/service D-01/D-04 có task/contract riêng được duyệt trước, không tự đổi API/schema. Chưa thêm UI/icon/motion library hoặc font asset mới.
- **Dependency:** R0 **lease đã PO Accepted**, giữ controller `EditorLease` và regression; wireframe UI-01 vẫn Proposed; DS-P01…P04/06/07 đã duyệt theo phạm vi; DS-P05 duyệt thử hai viewport; DS-P08/UI-03 đã duyệt ST-01…ST-07; delta contract còn cần review riêng. D-01…D-05 Approved về hướng, D-06 vẫn Recommended. R1.A không cần tự làm recent metadata hoặc preferences backend; R1.B cần D-01 contract xuyên browser/launcher đổi port. Compact/resize preference details thuộc R3/D-04/D-05, chỉ spec ở DS lúc này. UI-03 Approved for Design theo ST-01…ST-07 dựa trên UI-02§11+D-03; contracts chưa chốt vẫn cần review, không suy capability từ ảnh concept.
- **Acceptance Criteria R1.A:** Áp dụng quyết định DS-P01…P07 đã ghi nhận; component8mục/state matrix đầy đủ, radius0, màu/typography/spacing theo tokens đã chọn; controls/focus/selected/disabled lý do rõ; text AA và control boundaries kiểm bằng computed styles; keyboard/NVDA với overlay/tab/tooltip; theme scope không lan vào composition; primitive không tự claim/save/revision. Không gọi DS Approved toàn bộ hoặc “accessibility passed” từ ratio palette.
- **Acceptance Criteria R1.B:** UI-DB-01…07, ba template first fold1366×768/1920×1080, recent không metadata giả, navigation giữ draft/jobs/manualSave, Storage entry riêng. D-01 history qua reload/browser/launcher restart+đổi port, không thay project dirty/content revision. Hero không chiếm diện tích trái mục tiêu chỉ vì ảnh tham chiếu.
- **Test plan:** R1.A kiểm field/button states và focus/dialog trap-return/tooltip/tabs/slider; Vietnamese IME/glyph, long names, zoom/reflow/reduced-motion/forced-colors; R0 unit/integration/browser dev+production, saveB/editC và stale writer guard giữ nguyên. R1.B Dashboard empty/error/many/trùng tên/3templates, dirty navigation, recent metadata persistence. Kiểm Preview CSS leakage; không dùng transport AI hoặc mock thumbnail làm evidence cloud/render. Ghi test thực và phần chưa chạy; task docs hiện tại không chạy browser/build mới.
- **Rủi ro:** global button/h1/footer rules ảnh hưởng Player, focus bị cắt do overflow, status wrap đẩy Preview, consent/readonly bị đổi thành variant màu, mất lyrics draft/job khi remount, font mới tải mạng, prototype compact chưa đủ AA/reflow. Border divider gốc không đủ3:1 cho input: dùng `border-control` DS-P01 đã duyệt; vẫn đo contrast computed khi triển khai.
- **Điều kiện hoàn thành:** triển khai từng phần trong phạm vi DS-P07 đã duyệt, không cần duyệt lại palette/Segoe UI/ba cỡ chữ/keyboard; các phần còn Pending Approval phải được chốt trước khi phụ thuộc vào đó. Sau code R1.A có state specimens + browser accessibility evidence, R1.B có wireframe được duyệt và UI-DB AC đạt; không suy toàn R1 xong từ docs hoặc build. Không thay đổi UI-02 nguyên văn hay nghiệm thu R3–R6. Commit/push/merge vẫn cần lệnh riêng cho task hiện hành.

**Dependency UI-04:** R1 cung cấp Dialog hai cột/góc vuông, Field/Button/Status/Progress có focus trap/return focus/keyboard/error; close và cancel-render là hai action riêng. Primitives không sở hữu job/preset/schema hoặc gọi renderer. Kích thước Export Dialog lớn theo UI-04; Dialog640 generic cũ không là ràng buộc production. Chưa triển khai trong task tài liệu này.

**Dependency UI-05 tại R1.B:** PM-01=both dùng chung normalized project list/query/controller và ProjectCard nền tảng với Dashboard; không tạo hai hệ thống card hoặc writer. D-01/PM-T01 phải chốt trước recent persistence xuyên restart/đổi port; list hiện chỉ id/name, không giả lastOpened/thumbnail/media status. File dự kiến: `components/projects/{project-toolbar,project-grid,project-list,project-card,project-row}.tsx` và shared list projection; UI-01 wireframe vẫn Proposed. Test Grid/List cùng IDs/filter/sort, recent ngoài contentHash/revision/Manual Save; chưa có data thì hiển thị unknown phù hợp.

**Dependency UI-06 tại R1:** Design System primitives/Settings sidebar, section, Field/Status/SaveBar/dialog focus trap và hai viewport. STG-01 workspace riêng; sáu section chỉ render capability thật. D-04 preference store contract SET-T01/02 chưa duyệt nên R1 không giả lập persistence hoặc ngôn ngữ chưa dịch. File dự kiến `components/settings/{settings-workspace,settings-navigation,settings-section,settings-field,settings-status,settings-save-bar}.tsx` cùng R1 primitives.

### R2 — Lease/session và controller lifecycle (P0)

- **Mục tiêu:** fix theo repro R0, quyền UI thống nhất và error/takeover/reconnect đáng tin cậy, giữ optimistic writes.
- **File dự kiến:** `use-studio.ts`, `hooks/use-editor-lease.ts`, `lib/api.ts` (giữ status/code client), `studio.tsx`, lease status component; integration/browser lease tests. `amvs/edit_leases.py/app.py` chỉ đọc; sửa cần task backend riêng được duyệt.
- **Dependency:** R0 reproduction/decisions, primitives feedback R1. R2 là gate trước khi bàn giao Editor layout mới cho dùng thật.
- **Acceptance Criteria:** UI-ED-05; claim được khi không owner; tab2 read-only; takeover thành công enable đúng revision, tab1 không ghi; thất bại có error; TTL/close/launcher recovery; không mất draft hoặc bypass revision.
- **Test plan:** matrix L-01…L-09; sửa field/Undo/Redo/manual save sau takeover; assert stale tab PATCH/save bị chặn; delayed response A→B→A, heartbeat timeout/401/409, failed takeover; browser dev và production lifecycle. Raw token không vào artifacts.
- **Rủi ro:** stale queued sync, StrictMode, cancelled unload, server semantics không đáp ứng mục tiêu; không biến error thành writable.
- **Điều kiện hoàn thành:** lỗi tái hiện có fix nhỏ + evidence fail-before/pass-after, matrix quyền đầy đủ; backend delta nếu cần đã được duyệt/kiểm riêng. Không tuyên bố root cause chỉ từ symptom.

### R3 — Editor shell, Preview transport và Timeline dock/resize

- **Mục tiêu:** 3 cột và dock viewport đúng UI-02; preview/timeline không bị panel dài đẩy khỏi màn hình.
- **File dự kiến:** `studio.tsx`, `globals.css`/editor CSS scoped; `components/editor/{workspace,header,left-tool-panel,preview-viewport,preview-transport,timeline-dock,timeline-resize-handle}.tsx`; `timeline.tsx`; `hooks/use-timeline-resize.ts`, UI state hook và local preferences adapter theo contract R0.
- **Dependency:** R1 primitives, R2 controller/lease, D-04/05; DOM adapter giữ callbacks cũ trước thay phần nội dung R4.
- **Acceptance Criteria:** UI-ED-01…04,09,15; header/preview/inspector/timeline đồng thời ở hai viewport; độc lập scroll; resize pointer/keyboard/reset/clamp, ratio 9:16/16:9/1:1; resize không dirty/content change/history.
- **Test plan:** geometry + wheel/page-scroll tests, many tracks + panels dài, horizontal zoom/ruler/playhead agreement; pointercancel/window resize/100–125% browser scale; transport seeks/focus/fullscreen theo D-05. Assert contentHash/manualSavedHash trước/sau resize; Player ref continuity.
- **Rủi ro:** minimum tracks/preview budget mâu thuẫn, position overlay, font metrics, event leaks, frame/scroll coordinate drift.
- **Điều kiện hoàn thành:** browser layout assertions/screenshot review đạt ở cả viewport; không bỏ controls để tránh overflow; timeline nghiệp vụ cũ còn hoạt động.

**Dependency UI-04:** thêm ExportEntry ở Header và BackgroundJobStatus/ReopenExportAction ở Editor, cùng activity entry Dashboard khi chuyển workspace. Job controller sống ngoài dialog/active project; visibility không reset history/selection/playhead/lyrics draft/lease, không tự revoke grant. R3 chỉ tích hợp entry/ownership, chưa gọi Export Dialog fully accepted trước R5/R6.

**Dependency UI-05 tại R2/R3:** ProjectManagement/Recovery là view, không tự adopt project hoặc claim quyền khi xem danh sách. Một application controller giữ lease epoch/TTL/revision, dirty hash, history, selection/playhead và lyrics draft; project switch đi qua dirty guard đã chốt PM-T02, workspace-only không reset state. App-owned job tracking theo jobId (PM-T08) bảo toàn render/package/AI khi chuyển workspace, không hủy job/revoke grant do unmount. File dự kiến: workspace navigation/dirty guard, `use-studio.ts`, job ownership hook và tests lifecycle; không tạo API client/writer thứ hai. R0 stale-response/takeover/expiry và saveB-editC phải regression; quyền khi quay lại lấy trạng thái hiện hành, không phục hồi writable từ cache.

**Dependency UI-06 tại R2/R3:** application controller/EditorLease/job tracking nằm ngoài Settings view; mở/quay lại giữ project/draft/history/playhead/heartbeat, return target kiểm quyền lease hiện hành. Settings draft guard riêng project dirty. D-04 versioned app preferences nằm ngoài content và localhost origin, atomic/multi-tab/fallback theo SET-T01/02 được duyệt; Timeline resize/panel preferences không đổi hash/revision/manualSavedHash. File dự kiến navigation state, preference adapter/service, Settings state hook và lifecycle tests; không tạo controller Drive thứ hai.

### R4 — Media, Lyrics, Text/Effects/Templates và contextual Inspector

- **Mục tiêu:** chuyển các forms dài thành Left Tool Panel, 3 mode lyrics và Inspector đúng loại; bảo toàn mọi đường hiện hữu.
- **File dự kiến:** tách `project-tools.tsx` sang `components/media/*`, `components/templates/*`, `components/project-data/*`; `lyrics-panel.tsx` sang `components/lyrics/*` + draft hook; `inspector.tsx` sang `components/inspector/*`; `TextTools/EffectsPanel`, tests liên quan. Giai đoạn A dùng lại domain/composition; giai đoạn B có thể sửa `packages/domain` schema/types, shared scene và validation tối thiểu theo delta đã review; không đổi codec/viết lại engine.
- **Dependency:** R2/R3, D-02 capability matrix; giai đoạn A: Media/Text/Templates → Lyrics → Inspector hiện có; giai đoạn B: advanced capabilities còn thiếu theo delta R0. Mỗi phần có review/regression riêng.
- **Acceptance Criteria:** UI-ED-06…10,14,15; media filter/search/tags/thumb retry/video-audio preview; batch partial failure; draft/review/applied giữ đúng qua đổi tab; nghe source; contextual project/image/video/audio/text/lyrics/MusicCard; numeric units/reset/disable reason; template không đổi bản gốc; giai đoạn B kiểm đủ advanced theo capability delta đã review, không thay renderer chỉ ở preview.
- **Test plan:** existing core-workflows/library/templates/AI fixture assertions chuyển UI mới; nhận dạng fail giữ draft, không auto apply; mode switch/selection/undo/source trim-rate/style-timing invariance; source bytes/hash; thumbnail error + long name; speed/highlight controls chỉ field có sẵn. Fixture AI phải gắn nhãn, tách khỏi real-model smoke.
- **Rủi ro:** unmount mất lyrics draft/job; duplicate form state; thay style đụng timing; HTML remount defaultValue; capability không có trong schema.
- **Điều kiện hoàn thành:** migration inventory mọi action cũ có entry mới, không mock chức năng; UX modes đạt browser tests; giai đoạn A ghi rõ advanced còn mở; giai đoạn B phải có capability thật, round-trip/schema compatibility và preview/MP4 regression trước nghiệm thu đầy đủ.

### R5 — Storage Manager, Project Data và Export

**Cập nhật ST-01…ST-07:** PO đã xác nhận “duyệt theo đề xuất” ngày24/11/2026; [UI-03](UI_03_STORAGE_MANAGER.md#storage-decisions) **Approved for Design — Not Implemented** theo các quyết định này. Workspace riêng/bốn tab, snapshot list khác task history; cloud test thật bằng tài khoản/folder được cấp quyền là gate bắt buộc đã duyệt, không dùng mock OAuth thay thế. Mở/đóng Storage phải giữ project/draft/render và theo dõi quyền lease hiện hành. Contract/API mới còn cần review.

- **Mục tiêu:** Drive/data/export tách khỏi vùng làm việc chính; transfers/jobs vẫn sống khi rời Storage workspace hoặc đóng dialog tác vụ khác; giữ consent và save/output invariants.
- **File dự kiến:** `drive-panel.tsx` tách `components/storage/*` + polling hook, `components/project-data/*`, `components/export/*`, `studio.tsx`/controller, `lib/api.ts` types field hiện hữu; Drive/export/data browser tests. R5.A dùng contract hiện tại; R5.B bổ sung delta đã review trong `amvs/drive*.py`, `app.py`, transfer state/client DTO và integration tests, không refactor backend ngoài scope.
- **Dependency:** R1 dialog/focus, R2/R3, R4 extraction; D-03 đã yêu cầu đầy đủ §11; cần contract progress/error/cancel được review ở R0 trước R5.B.
- **Acceptance Criteria:** UI-ED-10…12,14,15; unconnected/connected/lastBackup/history/exports; consent không mất hoặc tự bật, auto persisted true không reset ngầm; restore refresh list và giữ current project. Export preset thật/folder cancel/missing-media/waiting/cancel/retry/output; correct snapshot B khi editor C; không preset override ẩn; R5.B có progress đo từ transfer, error category và cancel thật cho upload/download.
- **Test plan:** Drive settings/bootstrap regressions, labelled transport error scenarios và backend consent/no-overwrite tests; workspace/tab navigation và back/return focus; modal Tab/Escape/focus trap cho Export/confirmation; đóng/mở progress không cancel ngầm; R5.B test cancel từng phase, lỗi giữa chunks, repeat cancel và cancel-vs-success, giữ backup cũ/no partial manifest. Real cloud chỉ với test fixture và consent hợp lệ, không upload dữ liệu người dùng để kiểm giao diện; UI mock không chứng minh cloud pass. Export render/decode thật ngắn và fidelity theo scope thay đổi.
- **Rủi ro:** autoSync consent drift, server chỉ có generic errors, restore thành công nhưng sidebar stale, mất job UI khi dialog unmount, preflight báo sai resource, native chooser bị nhầm thành lỗi.
- **Điều kiện hoàn thành:** ST-06 yêu cầu evidence cloud thật trong phạm vi được cấp quyền; chưa có quyền/evidence thì ghi chưa đạt, không thay bằng OAuth mock. Không có Drive form trong main; toàn bộ storage/recovery/GC/export actions cũ được chuyển; browser/backend evidence đạt; R5.A chưa được gọi hoàn tất; R5.B phải chứng minh progress/error/cancel thật, cleanup và no-overwrite trước nghiệm thu Storage.

**R5 Export theo UI-04 — Approved for Design, Not Implemented:** bắt buộc modal hai cột và đóng dialog không hủy render. File dự kiến: `components/export/{export-dialog,export-preview-pane,export-validation-panel,export-configuration-form,preset-fields,output-folder-field,export-dialog-footer,export-job-details,export-result-actions}.tsx`, `components/editor/{export-entry,background-job-status}.tsx`, render job controller/hook ở application scope, `use-studio.ts`, Api types và tests Export. Tên/path là proposed, chưa tạo code. Filename field chỉ có tác dụng khi EX-P02 đã duyệt/có backend thật; không input giả.

- **R5 Export dependency/gates:** R1 primitives, R3 stable entry/job ownership, R0 regression; [EX-P01…EX-P07](UI_04_EXPORT_WORKSPACE.md#export-open-decisions) cần chốt theo phần phụ thuộc: staged preset/apply/Preview, custom filename, safe result metadata, resource-preflight/error detail, retryB/C/idempotence, server job lease policy và dialog width/compact. UI approval không tự cấp quyền backend/renderer/schema delta.
- **Contracts giữ nguyên:** project schema/timebase/PRESETS12/history/manualSavedHash; Api session/editor headers; POST folder-grants scope export→opaque grant/cancel; POST jobs `{projectId,revision,grantId}`→202; GET jobs/list/id; POST jobs/id/cancel; GET outputs/id và POST open-folder. Pinned immutable snapshot/media pins, sharedScene/preset/duration/parity, native chooser/no raw path/no fallback. Đóng UI không DELETE grant gắn job; revoke có thể cancel job ở baseline.
- **Capability gate:** API hiện không nhận tên file tùy chọn hoặc trả đủ summary snapshot sau reopen; resource checks nằm trong job và async failure generic. POST jobs có revision guard nhưng chưa leases.guard; cần review trước siết policy, không tuyên bố đã fence mọi API. Các thiếu hụt không được bỏ qua chỉ để khớp mockup.
- **AC và verification:** UI-EX-01…15 ở §8.1 và phụ lục UI-04. Browser dev+production: close/reopen/Workspace/Takeover + polling jobId, preset-stage/cancel/apply/Undo/dirtyB/C, invalid/missing media, native picker cancel/grant revoke, status/terminal/cancel/publish race/output actions. Small real generated-media render/decode, snapshotHash/mediaGC pins và Preview/MP4 parity; heavy/fidelity chọn theo impact/admission, không dữ liệu người dùng. Không báo full R5 Export nếu EX-P gaps còn khiến requirements chưa đạt.

**R5 Project Management theo UI-05 — Approved for Design, Not Implemented:** PM-01 Grid/List chung data, PM-02 Recovery workspace riêng, PM-03 menu Xóa → dialog xác nhận (hai bước). File dự kiến: `components/projects/project-management-workspace.tsx`, actions/details/rename/delete/save/package/import dialogs; `components/project-data/{recovery-workspace,recovery-snapshot-list,missing-media-dialog,media-relink-dialog}.tsx`, controller/navigation và tests tương ứng. Đây là cấu trúc proposed, không tạo code trong task tài liệu.

- **Dependency:** R1.B shared list/primitives và D-01, R2/R3 single authority/navigation/job lifecycle, R5 Export/Storage shared background ownership. Chốt [PM-T01…PM-T08](UI_05_PROJECT_MANAGEMENT.md#h-pending-technical-approval) theo phần phụ thuộc; metadata/API/schema mới là Pending Technical Approval. Không tự thêm duplicate/trash/bulk delete/thumbnail generation hoặc sửa recovery/GC contract.
- **Contracts giữ nguyên:** GET projects `{id,name}`; project template/schema và PATCH expected revision; R0 lease/TTL/optimistic concurrency; native grants và Manual Save hashB/currentC; `.amvs` immutable inventory/checksum/import no-overwrite; local recovery thay working copy cùngID, không đổi manual checkpoint; relink exact checksum với native picker; DELETE project không tự source GC; GC recheck pins. Manual checkpoint open khác package import và có lease-policy gap cần PM-T04 review.
- **Acceptance/Test plan:** UI-PM-01…16 ở §8.2 và UI-05 phụ lục J. Browser dev+production dùng fixture riêng: dirty navigation/unapplied lyrics, rename409, saveB-editC, package còn chạy khi đổi workspace, native import/collision/corrupt, recovery confirm/conflict và manual file invariance, relink cancel/wrong checksum, delete menu→confirm/Hủy/Escape/double-submit/stale target. Backend kiểm source/pin/revision/hash/no-overwrite; không xóa/restore dữ liệu người dùng.
- **Rủi ro và điều kiện hoàn thành:** delete chưa expected-revision/rowcount distinction, recovery của project đã xóa không truy cập được qua API hiện tại, manual-open concurrent mutation và component-owned job polling còn khoảng cách. Phải xử lý quyết định kỹ thuật + có evidence browser/backend theo AC trước nghiệm thu; docs/build hoặc tests nền không đóng R5. Không đổi UI-01…04/DS để che thiếu capability.

**R5 Settings theo UI-06 — Approved for Design, Not Implemented:** STG-01 workspace sidebar+content, STG-02 safe immediate vs critical Lưu/Hủy, STG-03 Drive summary/link tới UI-03. Components dự kiến `components/settings/{general-settings,appearance-settings,local-storage-settings,ai-processing-settings,drive-settings-summary,system-information,cache-cleanup-dialog,source-gc-preview-dialog}.tsx`; tên/path proposed. Storage policy GET/PATCH, cache/temp cleanup, source-GC preview/confirm, ai/providers, health/session và Drive GET giữ contract hiện tại. Không thêm model installer/GPU selector/global model preference, không nhân đôi OAuth/backup/restore/progress controller.

- **Gates:** [SET-T01…05](UI_06_SETTINGS_WORKSPACE.md#f-api-contract-pending-decisions-và-regression) cần PO duyệt theo phần phụ thuộc: D-04 store/version/atomic/port/multi-tab, reset+hybrid field map, cleanup result semantics, diagnostics/redaction, app controller/job ownership. Chỉ bổ sung backend delta thật sự cần; không đổi UI-01…05/DS. Ảnh có “X” được diễn giải là back workspace theo STG-01, không là modal.
- **Test/AC:** UI-SET-01…16 ở §8.3; browser dev+production hai viewport, reload/restart/đổi port/two tabs, safe immediate rollback vs draft save/cancel/guard, cache partial failures, GC pin recheck, model missing, Drive summary parity/navigation, R0 lease/jobs/dirtyB-C và secret redaction. Fixture riêng; không cleanup/GC/restore dữ liệu người dùng. Không gọi UI-06 Passed từ docs/build.

### R6 — Regression, accessibility và design acceptance

- **Mục tiêu:** chứng minh redesign giữ nghiệp vụ, dữ liệu, preview/export và đạt UI-ED-01…15; cập nhật hồ sơ có evidence thật.
- **File dự kiến:** `tests/e2e/{dashboard,editor-layout,editor-lease,editor-panels,storage-export}.spec.ts`, adapters cho specs cũ; integration/unit khi cần; `playwright.config.ts` cho viewport matrix; docs UI/UX và bảng evidence (không sửa lịch sử spec được duyệt).
- **Dependency:** R1–R5 đã tích hợp; decisions blockers đã xử lý; machine đủ RAM cho heavy tests. Không chạy song song nhiều heavy coordinators.
- **Acceptance Criteria:** toàn bộ bảng §8 có result/path; không có critical console/page error; keyboard/disabled/error/empty đầy đủ; hash/schema/revision/manual-save invariants còn đúng; đủ 3 template E2E/MP4. Không lấy build pass thay interaction pass; không lấy S6 cũ làm pass redesign.
- **Test plan:** unit/integration/typecheck/format/build; browser matrix; all-preset/fidelity/300s theo ảnh hưởng CSS/composition/layout; giai đoạn B bổ sung schema round-trip/legacy projects và transfer-cancel cleanup; ghi elapsed/resources/admission/repetitions. Nội dung code source/hash và raw test reports/screenshot/trace liên kết. Model/cloud chất lượng kiểm riêng, không tự đóng quality gates cũ.
- **Rủi ro:** selector migration làm test yếu, retry che flakes, resource blocked giả failure UI, visual snapshot che sai dữ liệu, user không duyệt capability gap.
- **Điều kiện hoàn thành:** PO review screenshots + workflow demo; giai đoạn B advanced và Storage đầy đủ đã kiểm, UI-01 state chuyển chỉ khi PO duyệt; UI-02 acceptance từng ID; lỗi/gap unresolved có owner và không blocker phát hành. Commit/push/merge vẫn cần chỉ dẫn riêng.

**UI-04 acceptance R6:** UI-EX-01…15 phải có browser/backend evidence và safe source/build provenance; giữ queued/waiting/cancelling/interrupted khác success. Kiểm keyboard/NVDA/body-only overflow ở1366×768/1920×1080, outputB khác currentC, background render sau close/Escape/Dashboard, R0 lease/saveB-editC còn đúng. Existing tests chỉ là nền; không lấy kết quả cũ/build/fixture renderer giả làm pass UI-04. Mọi skip/block đều ghi lý do và không đóng gate còn thiếu.

**UI-05 acceptance R6:** yêu cầu đủ UI-PM-01…16 theo §8.2, browser thực ở1366×768/1920×1080, keyboard/focus/long names/IME và backend invariants. Ghi từng result/report/source/build, Not run/Blocked/Skipped có lý do. Không dùng test cũ làm bằng chứng UI mới; không ép Project Management theo no-page-scroll của Editor. Tests fixtures bao gồm restart/đổi port cho D-01, lease takeover khi đang ở PM, Manual Save B/edit C, recovery sameID/manual checkpoint giữ nguyên, import collision và shared source GC pins.

## 8. Browser E2E & regression matrix đề xuất

Bảng dưới là **acceptance plan cho redesign**, chưa phải kết quả pass. R0 đã đo baseline UI-ED-01/02 (chưa đạt) và chẩn đoán các kịch bản UI-ED-05; kết quả cụ thể/giới hạn ở báo cáo R0, không suy toàn bộ bảng đã chạy. Viewports chính 1366×768 và 1920×1080; thêm thử nhỏ/zoom để xác định compact policy, không tự công bố mobile supported.

| AC | Bằng chứng cần có | Backend/domain regression |
|---|---|---|
| UI-ED-01 | html/body scrollHeight ≤ clientHeight + sai số rounding, scrollY không đổi khi wheel; ở mode Editor, không chỉ screenshot | Không áp dụng |
| UI-ED-02 | Bounds Preview/Inspector/Timeline trong viewport, >0 area và không bị overlay khác che ở normal workspace; cả 3 ratios | Composition dimensions/FPS unchanged |
| UI-ED-03 | Drag/keyboard/reset/min/max/resize viewport; preferences giữ qua reload/restart/port-change, invalid state fallback; cancel/unmount cleanup | contentHash/manualSavedHash/revision/history không đổi |
| UI-ED-04 | Scroll library/lyrics/inspector/many tracks, body không cuộn, header/ruler sticky đúng | Không mutate content từ scrolling |
| UI-ED-05 | Một/hai tab, takeover deny/fail/success, owner close/expiry/launcher restart, edit/undo/redo/save, delayed requests | Existing lease/revision/queued-save race; stale PATCH/save blocked |
| UI-ED-06 | Select từng type, numeric/slider/reset/style/trim/rate, preview cập nhật thật | validateMediaWindows/remapLyrics/hash; supported fields only |
| UI-ED-07 | Batch good+bad, rights, image/video/audio, type/search/tags, long filenames, thumb fail+retry, reuse | Probe/content endpoints; source bytes/pins unchanged |
| UI-ED-08 | Import/manual/recognition, mode switches giữ draft; review/apply/fallback; fail/cancel AI; source audition | Parser/source mapping, no auto apply, no word timestamps giả |
| UI-ED-09 | Select/move/trim/seek/zoom/order/undo/redo; timeline horizontal scroll/height changes | Single transaction/user action, interval/timebase invariants |
| UI-ED-10 | Save B/edit C dirty, recovery confirm, package/open/relink; navigation/dialog không mất dữ liệu | Revision/manual hash/checksum/no overwrite/pins |
| UI-ED-11 | Storage connect/disconnect/settings/consent/auto/history/restore/list refresh; real progress/error/cancel upload/download, lỗi giữa chunks và cancel-vs-success race | DPAPI/no secret in response, manifest-last, cloud round-trip riêng |
| UI-ED-12 | Export dialog cancel/wait/fail/cancel/retry/output; edit C khi render B; reopen UI | MP4 H.264/AAC/duration/frames/timestamps; immutable snapshot |
| UI-ED-13 | pageerror + console.error có phân loại, không critical error chưa xử lý; network errors được phản ánh UX | Error DTO safe, no private data logs |
| UI-ED-14 | Loading/empty/read-only/conflict/unsaved/job/offline/disconnected/missing/invalid/recoverable/fatal | Fixture kết quả lỗi ghi rõ; không coi fixture là model/cloud thật |
| UI-ED-15 | Keyboard tab order/arrow tabs, separator keys, tooltip accessible name, modal focus trap/Escape/return focus, no shortcut khi đang gõ | Không bypass edit permissions/history |

Test data: media tự tạo, library riêng, project names trùng/dài/dấu Việt, 12/100 clips, nhiều tracks, lyrics dài, thiếu asset và network delay. Browser API dùng fixture grants cho OS chooser, vẫn giữ native picker regression riêng. Session bootstrap tests phải giữ nguyên exact-origin protection. Artifacts Git-ignored, không đẩy credentials/media cá nhân vào repo.

Lệnh dự kiến sau khi có code và quyền triển khai: `npm.cmd test -- --pool=threads --maxWorkers=1`, `python -m pytest`, `npm.cmd run typecheck`, `npm.cmd run format:check`, `npm.cmd run build`, `npm.cmd run test:e2e`; dùng Python từ `.venv-api`. Fidelity/long-run/Drive runners chọn theo thay đổi và tài nguyên; không báo pass khi skipped/blocked. Ngưỡng UI P95/FPS trong SRS vẫn experimental, ACC-01 cần PO chốt.

### 8.1. UI-04 — UI-EX-01…15 (chưa chạy cho redesign)

Nguồn chuẩn và test matrix chi tiết: [UI-04§11 và phụ lục J](UI_04_EXPORT_WORKSPACE.md). Hai quyết định chính đã Approved; bảng này là kế hoạch evidence, không trạng thái Passed.

| AC | Tiêu chí nghiệm thu | Evidence dự kiến |
|---|---|---|
| UI-EX-01 | Dialog Export hai cột | Geometry hai desktop viewports |
| UI-EX-02 | Minimal Professional/DS/góc vuông | Computed styles/state screenshots |
| UI-EX-03 | Chỉ cấu hình supported | PRESETS12, filename capability thật, negative API tests |
| UI-EX-04 | Preview/MP4 cùng composition/preset | Real Preview + decode/fidelity theo impact |
| UI-EX-05 | Preset qua history/dirty đúng | Stage/cancel/apply/Undo/Redo/hashB/C |
| UI-EX-06 | Folder grant đúng/cancel neutral | Native picker + scope/invalid/reselect/no raw path |
| UI-EX-07 | Snapshot/revision đúng | Stale409/immutableB/media pins, C không đổi outputB |
| UI-EX-08 | Close không hủy render | Real job vẫn chạy, reopen đúngId, no revoke/cancel request |
| UI-EX-09 | Status/progress backend thật | Queued/Waiting/render phases/network stale; no fakeRAM/% |
| UI-EX-10 | Cancel terminal đúng | Cancelling→terminal, repeat/race, owned-tree cleanup |
| UI-EX-11 | Failed/Cancelled/Succeeded rõ | UI+backend terminal/interrupted/retry attempt matrix |
| UI-EX-12 | MP4 truy cập qua supported actions | Output success guard/download/open-folder, summaryB |
| UI-EX-13 | Không mất project/draft/lease/history | Dialog/workspace/takeover + R0/manualSave regression |
| UI-EX-14 | Keyboard/focus/Escape/overflow | Focus trap/return/NVDA/IME/zoom/body-only scroll |
| UI-EX-15 | Browser/backend regression đạt | Reports thật, giữ tests cũ, ghi Not run/Skipped/Blocked |

### 8.2. UI-05 — UI-PM-01…16 (chưa chạy cho redesign)

Nguồn chuẩn: [UI-05§15 và phụ lục J](UI_05_PROJECT_MANAGEMENT.md). PM-01/02/03 đã duyệt về thiết kế; đây là kế hoạch evidence, không phải Passed. R1.B/R2–R3/R5 thực hiện đúng dependency ở trên, R6 kiểm đầy đủ.

| AC | Tiêu chí nghiệm thu nguyên văn | Evidence dự kiến |
|---|---|---|
| UI-PM-01 | Project Management là workspace riêng | Workspace entry/back giữ context; không mutation do đổi view |
| UI-PM-02 | Grid/List hoạt động với dữ liệu thật | Grid/List cùng IDs/query/controller; metadata thật/unknown |
| UI-PM-03 | Search, filter, sort hoạt động | Tên Việt/trùng/dài/no-results; recent/warning cần nguồn thật |
| UI-PM-04 | Recent Projects lưu xuyên restart | Open event thành công khác GET/poll; restart/browser/launcher đổi port |
| UI-PM-05 | Tạo/mở project đúng template và lease | Ba template bất biến; claim/read-only/takeover; failed load không stale state |
| UI-PM-06 | Chuyển project bảo toàn dirty/draft | Dirty guard, unapplied lyrics/read-only drafts; cancel/save failure không mất state |
| UI-PM-07 | Rename đúng revision và state | Current/noncurrent rename, validation, lease/revision409, list refresh |
| UI-PM-08 | Manual Save bảo toàn B-save/C-edit | Native grant/cancel, snapshotB được lưu trong lúc editC; C vẫn dirty |
| UI-PM-09 | Package `.amvs` chính xác, không mất source | Immutable package/source checksums/pins; background tracking và terminal thật |
| UI-PM-10 | Import kiểm schema/checksum và không overwrite | Native chooser/schema/checksum/containment/collision; không auto-adopt bỏ draft |
| UI-PM-11 | Recovery có workspace riêng và xác nhận an toàn | Workspace riêng/confirm/corrupt/conflict; sameID working restore, manualfile giữ |
| UI-PM-12 | Missing media/relink dùng đúng reference | Missing inventory; native exact checksum, wrong-file/cancel; mapping/hash giữ |
| UI-PM-13 | Delete có dialog hai bước, không xóa nhầm media | Menu→confirm; Hủy/Escape/no request; stale target; không automatic GC |
| UI-PM-14 | Error, loading, empty, read-only được xử lý | Fault injection labelled, API errors giữ dữ liệu; không fallback mẫu |
| UI-PM-15 | Keyboard, focus, responsive đạt yêu cầu | Keyboard/focus trap-return/long names/IME; hai viewport/workspace scroll |
| UI-PM-16 | Không regression lease, jobs, history, render, storage | R0/lease/history/jobs/parity/storage/source pins, không thay tests cũ |

### 8.3. UI-06 — UI-SET-01…16 (chưa chạy cho redesign)

Nguồn chuẩn: [UI-06§16 và phụ lục F](UI_06_SETTINGS_WORKSPACE.md). Bảng là kế hoạch evidence, không phải Passed.

| AC | Tiêu chí nghiệm thu nguyên văn | Evidence dự kiến |
|---|---|---|
| UI-SET-01 | Settings là workspace riêng | Workspace/back giữ controller |
| UI-SET-02 | Sáu nhóm điều hướng rõ ràng | Sáu mục keyboard/selected |
| UI-SET-03 | Đúng Design System, góc vuông | Computed DS/radius0 hai viewport |
| UI-SET-04 | Hybrid Save hoạt động đúng semantics | Immediate rollback + draft Save/Hủy/guard |
| UI-SET-05 | Settings preferences độc lập project | Hash/revision/history/lease bất biến |
| UI-SET-06 | Preferences có persistence/version/fallback an toàn | Reload/restart/port change/version corrupt/two tabs |
| UI-SET-07 | Reset bố cục không thay đổi dữ liệu project | Reset không đổi project |
| UI-SET-08 | Cache cleanup an toàn và có feedback | Cache partial result/source preserved |
| UI-SET-09 | Source GC có preview, consent, xác minh pins | GC preview/consent/pins recheck |
| UI-SET-10 | AI controls chỉ phản ánh capability thật | Model/provider status thật, no fake control |
| UI-SET-11 | Drive Settings liên kết với UI-03, không nhân đôi controller | Drive same status + link UI-03, one owner |
| UI-SET-12 | Session/backend/system errors được xử lý rõ | Offline/session/system error |
| UI-SET-13 | Mở/đóng Settings không làm mất Editor state/job/lease | Editor draft/job/lease continuity |
| UI-SET-14 | Không lộ credentials, tokens hoặc dữ liệu nhạy cảm | Secret/token redaction |
| UI-SET-15 | Keyboard/accessibility/responsive đạt yêu cầu | Keyboard/NVDA/focus/reflow |
| UI-SET-16 | Không regression project dirty, revision, history, render, Drive | Dirty B/C, render, Drive regression |

## 9. Review và trạng thái bàn giao tài liệu

Đã tạo UI-01 Proposed; lưu đủ UI-02 Approved for Design — Not Implemented; phân tích mã/gaps và kế hoạch R0–R6. Chưa có ứng dụng redesign hoặc browser acceptance mới; đã có công cụ/bằng chứng chẩn đoán R0 và 3 integration tests được chạy. Không thay baseline RTM/ADR/DB/API trong nhiệm vụ này. Khi được duyệt triển khai, bắt đầu từ R0 và P0 lease; không tự bắt đầu từ layout để bỏ qua blocker.

Commit tài liệu đề xuất khi PO cho phép: `docs(ui): document dashboard and professional editor redesign plan`. Tạo commit/push không thuộc quyền hiện tại.

**Bàn giao UI-05 ngày24/11/2026:** đã lưu đầy đủ đặc tả PO v1.0 (bổ sung hoàn chỉnh từ hội thoại), 16AC và phân tích capability/flow/rủi ro/Pending Technical Approval trong UI-05. Chỉ tài liệu; chưa triển khai R5, chưa chạy browser/backend tests mới, chưa commit/push/merge. Các thay đổi UI-03/UI-04 có sẵn được giữ nguyên.

**Bàn giao UI-06 ngày24/11/2026:** đặc tả PO v1.0 và 16AC được bảo toàn; phần capability/contract/risks và dependency R1–R6 là kế hoạch tài liệu. Chưa chạy browser/backend tests mới hoặc triển khai R5 Settings; giữ STG-01/02/03 và UI-03 Drive ownership.
