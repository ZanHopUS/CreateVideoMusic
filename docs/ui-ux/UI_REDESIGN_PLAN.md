# UI Redesign Plan — R0–R6

**Cập nhật implementation R0:** PO đã cho phép sửa riêng Editor Lease/read-only; đã triển khai, chạy regression và kiểm lại C06. Sẵn sàng review chức năng R0 lease với giới hạn timing/native picker; xem [kết quả triển khai và evidence](UI_R0_LEASE_FIX_RESULTS.md). Các mô tả “chưa sửa” bên dưới là baseline/chẩn đoán lịch sử; R1–R6 và UI redesign chưa triển khai.

**Dự án:** Hòa Âm / AI Music Video Studio

**Ngày:** 24/11/2026 (Asia/Saigon)

**Trạng thái:** Proposed implementation plan — R0 lease diagnosis đã được giao và thực hiện; R1–R6 chưa triển khai

**Nhánh khảo sát:** `dev` · **HEAD:** `ba60ab0` · không tạo nhánh mới

**Nguồn:** [UI-01 Proposed](UI_01_DASHBOARD.md), [UI-02 Approved for Design nguyên văn](UI_02_VIDEO_EDITOR.md), [Gap Analysis](UI_GAP_ANALYSIS.md).

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
- Storage/Export/ProjectData dùng dialog để Editor không remount; đóng dialog không hủy render/ASR/Drive transfer. Export còn job thì status summary vẫn truy cập được.
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
| DrivePanel thường trực | StorageManager dialog | Poll/store ngoài view, last backup/history/exports; refresh project list sau restore success, không tự adopt overwrite current |
| Inline render/job-panel | ExportDialog + background status | Theo dõi job sau đóng dialog/quay Dashboard; reopen kết quả, cancel/retry/MP4/open folder |

**Export preset:** hiện preset nằm trong project content và ảnh hưởng preview + rescale x/y/font. Export dialog phải gọi cùng action preset qua history; có thể dùng lựa chọn tạm trong form, nhưng chỉ có một giá trị áp dụng. Cancel trước apply không sửa project; sau apply dirty đúng semantics, phải hiển thị rõ. Không gửi preset override ngoài DTO hiện hành. Folder được chọn bằng native grant, không nhập absolute path vào API. Resource state lấy job admission/message thật; chưa có preflight RAM endpoint độc lập nên không hiển thị “đủ RAM” giả.

**D-02 — phân kỳ đề xuất:** Giai đoạn A (R1–R5.A) làm Dashboard/workspace/lease/resize và di chuyển capabilities đang có. Giai đoạn B (R4.B/R5.B, sau baseline A) hoàn thiện các yêu cầu advanced còn thiếu bằng thay đổi tối thiểu đã review; giữ source mapping/history/preview-export parity. Không dựng zoom/rotation/card-layout/progress-style giả bằng CSS Editor. R6 có checkpoint A, nhưng chỉ nghiệm thu toàn bộ sau B. Phân chia này là đề xuất kỹ thuật, không suy thành quyền code hoặc waiver cho requirements.

**D-03 — Storage hoàn chỉnh:** R5.A chuyển đầy đủ UI với contract hiện tại; R5.B bổ sung transfer progress backend thật (bytes/count/phase có nguồn đo), structured safe error categories và cancel transfer. Schema/status transition/cancel scope phải mô tả trước code; cancel idempotent, cleanup đúng task, không xóa source/local hoặc backup thành công cũ, không publish manifest khi chưa verify. Đóng dialog không hủy job; cancel OAuth không thay cancel upload. Không báo full Storage acceptance nếu B chưa đạt.

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

### R1 — Design system và Dashboard

- **Mục tiêu:** tokens/primitives thống nhất, Dashboard template-first gọn, project list/navigation và entry Storage.
- **File dự kiến:** `globals.css` (scope lại), `components/ui/{button,field,tabs,dialog,tooltip,status}.tsx`, `components/dashboard/*`, `studio.tsx`, `hooks/use-editor-ui.ts` hoặc workspace navigation state; metadata persistence adapter/service mới (tên/path chốt ở R0), tests restart/port-change.
- **Dependency:** R0; UI-01 wireframe/recent semantics được PO duyệt. D-01 yêu cầu persistence xuyên phiên; metadata API/store contract đã review ở R0.
- **Acceptance Criteria:** UI-DB-01…07; 3 template first fold; no Drive inline; loading/empty/error; back/open giữ draft/jobs; keyboard/focus/long names tốt. Giá trị token chỉ chốt sau review, không gọi kích thước đề xuất là bắt buộc. Recent phải còn sau browser/launcher restart và đổi port, không làm project dirty.
- **Test plan:** new dashboard E2E tại 1366×768/1920×1080, create 3 templates, empty/many/duplicate-name projects, dirty navigation; recent xuyên reload/browser restart/launcher port-change, không tăng project revision; component state/focus kiểm khi có hành vi cần test. Kiểm CSS không rò vào ProjectScene.
- **Rủi ro:** body scroll lock lây Dashboard, mất state khi navigation, typo theme/contrast, timestamp giả.
- **Điều kiện hoàn thành:** review wireframe/token screenshots được chấp thuận, browser AC đạt và tests cũ tương ứng không mất assertions.

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

### R4 — Media, Lyrics, Text/Effects/Templates và contextual Inspector

- **Mục tiêu:** chuyển các forms dài thành Left Tool Panel, 3 mode lyrics và Inspector đúng loại; bảo toàn mọi đường hiện hữu.
- **File dự kiến:** tách `project-tools.tsx` sang `components/media/*`, `components/templates/*`, `components/project-data/*`; `lyrics-panel.tsx` sang `components/lyrics/*` + draft hook; `inspector.tsx` sang `components/inspector/*`; `TextTools/EffectsPanel`, tests liên quan. Giai đoạn A dùng lại domain/composition; giai đoạn B có thể sửa `packages/domain` schema/types, shared scene và validation tối thiểu theo delta đã review; không đổi codec/viết lại engine.
- **Dependency:** R2/R3, D-02 capability matrix; giai đoạn A: Media/Text/Templates → Lyrics → Inspector hiện có; giai đoạn B: advanced capabilities còn thiếu theo delta R0. Mỗi phần có review/regression riêng.
- **Acceptance Criteria:** UI-ED-06…10,14,15; media filter/search/tags/thumb retry/video-audio preview; batch partial failure; draft/review/applied giữ đúng qua đổi tab; nghe source; contextual project/image/video/audio/text/lyrics/MusicCard; numeric units/reset/disable reason; template không đổi bản gốc; giai đoạn B kiểm đủ advanced theo capability delta đã review, không thay renderer chỉ ở preview.
- **Test plan:** existing core-workflows/library/templates/AI fixture assertions chuyển UI mới; nhận dạng fail giữ draft, không auto apply; mode switch/selection/undo/source trim-rate/style-timing invariance; source bytes/hash; thumbnail error + long name; speed/highlight controls chỉ field có sẵn. Fixture AI phải gắn nhãn, tách khỏi real-model smoke.
- **Rủi ro:** unmount mất lyrics draft/job; duplicate form state; thay style đụng timing; HTML remount defaultValue; capability không có trong schema.
- **Điều kiện hoàn thành:** migration inventory mọi action cũ có entry mới, không mock chức năng; UX modes đạt browser tests; giai đoạn A ghi rõ advanced còn mở; giai đoạn B phải có capability thật, round-trip/schema compatibility và preview/MP4 regression trước nghiệm thu đầy đủ.

### R5 — Storage Manager, Project Data và Export

- **Mục tiêu:** Drive/data/export tách khỏi vùng làm việc chính; transfers/jobs vẫn sống khi đóng dialog; giữ consent và save/output invariants.
- **File dự kiến:** `drive-panel.tsx` tách `components/storage/*` + polling hook, `components/project-data/*`, `components/export/*`, `studio.tsx`/controller, `lib/api.ts` types field hiện hữu; Drive/export/data browser tests. R5.A dùng contract hiện tại; R5.B bổ sung delta đã review trong `amvs/drive*.py`, `app.py`, transfer state/client DTO và integration tests, không refactor backend ngoài scope.
- **Dependency:** R1 dialog/focus, R2/R3, R4 extraction; D-03 đã yêu cầu đầy đủ §11; cần contract progress/error/cancel được review ở R0 trước R5.B.
- **Acceptance Criteria:** UI-ED-10…12,14,15; unconnected/connected/lastBackup/history/exports; consent không mất hoặc tự bật, auto persisted true không reset ngầm; restore refresh list và giữ current project. Export preset thật/folder cancel/missing-media/waiting/cancel/retry/output; correct snapshot B khi editor C; không preset override ẩn; R5.B có progress đo từ transfer, error category và cancel thật cho upload/download.
- **Test plan:** Drive settings/bootstrap regressions, labelled transport error scenarios và backend consent/no-overwrite tests; modal Tab/Escape/return focus; đóng/mở progress không cancel ngầm; R5.B test cancel từng phase, lỗi giữa chunks, repeat cancel và cancel-vs-success, giữ backup cũ/no partial manifest. Real cloud chỉ với test fixture và consent hợp lệ, không upload dữ liệu người dùng để kiểm giao diện; UI mock không chứng minh cloud pass. Export render/decode thật ngắn và fidelity theo scope thay đổi.
- **Rủi ro:** autoSync consent drift, server chỉ có generic errors, restore thành công nhưng sidebar stale, mất job UI khi dialog unmount, preflight báo sai resource, native chooser bị nhầm thành lỗi.
- **Điều kiện hoàn thành:** không Drive form trong main; toàn bộ storage/recovery/GC/export actions cũ được chuyển; browser/backend evidence đạt; R5.A chưa được gọi hoàn tất; R5.B phải chứng minh progress/error/cancel thật, cleanup và no-overwrite trước nghiệm thu Storage.

### R6 — Regression, accessibility và design acceptance

- **Mục tiêu:** chứng minh redesign giữ nghiệp vụ, dữ liệu, preview/export và đạt UI-ED-01…15; cập nhật hồ sơ có evidence thật.
- **File dự kiến:** `tests/e2e/{dashboard,editor-layout,editor-lease,editor-panels,storage-export}.spec.ts`, adapters cho specs cũ; integration/unit khi cần; `playwright.config.ts` cho viewport matrix; docs UI/UX và bảng evidence (không sửa lịch sử spec được duyệt).
- **Dependency:** R1–R5 đã tích hợp; decisions blockers đã xử lý; machine đủ RAM cho heavy tests. Không chạy song song nhiều heavy coordinators.
- **Acceptance Criteria:** toàn bộ bảng §8 có result/path; không có critical console/page error; keyboard/disabled/error/empty đầy đủ; hash/schema/revision/manual-save invariants còn đúng; đủ 3 template E2E/MP4. Không lấy build pass thay interaction pass; không lấy S6 cũ làm pass redesign.
- **Test plan:** unit/integration/typecheck/format/build; browser matrix; all-preset/fidelity/300s theo ảnh hưởng CSS/composition/layout; giai đoạn B bổ sung schema round-trip/legacy projects và transfer-cancel cleanup; ghi elapsed/resources/admission/repetitions. Nội dung code source/hash và raw test reports/screenshot/trace liên kết. Model/cloud chất lượng kiểm riêng, không tự đóng quality gates cũ.
- **Rủi ro:** selector migration làm test yếu, retry che flakes, resource blocked giả failure UI, visual snapshot che sai dữ liệu, user không duyệt capability gap.
- **Điều kiện hoàn thành:** PO review screenshots + workflow demo; giai đoạn B advanced và Storage đầy đủ đã kiểm, UI-01 state chuyển chỉ khi PO duyệt; UI-02 acceptance từng ID; lỗi/gap unresolved có owner và không blocker phát hành. Commit/push/merge vẫn cần chỉ dẫn riêng.

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

## 9. Review và trạng thái bàn giao tài liệu

Đã tạo UI-01 Proposed; lưu đủ UI-02 Approved for Design — Not Implemented; phân tích mã/gaps và kế hoạch R0–R6. Chưa có ứng dụng redesign hoặc browser acceptance mới; đã có công cụ/bằng chứng chẩn đoán R0 và 3 integration tests được chạy. Không thay baseline RTM/ADR/DB/API trong nhiệm vụ này. Khi được duyệt triển khai, bắt đầu từ R0 và P0 lease; không tự bắt đầu từ layout để bỏ qua blocker.

Commit tài liệu đề xuất khi PO cho phép: `docs(ui): document dashboard and professional editor redesign plan`. Tạo commit/push không thuộc quyền hiện tại.
