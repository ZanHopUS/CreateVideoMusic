# UI Gap Analysis — Dashboard & Professional Editor

**Cập nhật implementation R0:** PO đã cho phép sửa riêng Editor Lease/read-only; đã triển khai, chạy regression và kiểm lại C06. Sẵn sàng review chức năng R0 lease với giới hạn timing/native picker; xem [kết quả triển khai và evidence](UI_R0_LEASE_FIX_RESULTS.md). Các mô tả “chưa sửa” bên dưới là baseline/chẩn đoán lịch sử; R1–R6 và UI redesign chưa triển khai.

**Trạng thái:** khảo sát mã + đề xuất, chưa triển khai

**Ngày:** 24/11/2026 (Asia/Saigon) · **Baseline:** `dev`, `ba60ab0`

**Thẩm quyền:** UI-01 Proposed; [UI-02 nguyên văn](UI_02_VIDEO_EDITOR.md) Approved for Design — Not Implemented. Bản đầy đủ UI-02 đã được PO bổ sung trong phiên khảo sát.

## 1. Phương pháp và phạm vi

Phần khảo sát ban đầu chỉ đọc repository và viết bốn tài liệu `docs/ui-ux/`, chưa chạy application/browser tests. **Cập nhật R0:** PO đã giao tái hiện và xác định nguyên nhân; browser diagnosis trên production/development và 3 integration tests đã chạy, kết quả ở [UI_R0_LEASE_DIAGNOSIS](UI_R0_LEASE_DIAGNOSIS.md). Application code/API/DB/lease vẫn không đổi. “Có trong mã” không đồng nghĩa đạt nghiệm thu. Các kết quả S6 ở [báo cáo cũ](../planning/S2_S6_RESULTS.md) là evidence lịch sử, không phải kết quả kiểm redesign hôm nay.

Nguồn đã đối chiếu:

- `AGENTS.md`, `apps/web/AGENTS.md`; PRD/SRS/RTM và OPEN_QUESTIONS tại **root**. Đường dẫn `docs/requirements/*`/`docs/decisions/OPEN_QUESTIONS.md` trong AGENTS chưa khớp vị trí thật; không di chuyển file.
- [ADR-0001](../decisions/ADR-0001-LOCAL_MVP_ARCHITECTURE.md), [ADR-0002](../decisions/ADR-0002-DIRECT_GOOGLE_DRIVE.md), [contracts](../architecture/MVP_CONTRACTS.md). Dùng ADR-0002 cho Drive trực tiếp thay vì mô tả desktop-sync cũ trong SRS.
- Toàn bộ frontend ứng dụng: `app/{page,layout}.tsx`, `app/globals.css`, API proxy `[...path]/route.ts`, `next.config.ts`, `lib/api.ts`, `hooks/use-studio.ts`, sáu component `studio`, `timeline`, `inspector`, `project-tools`, `lyrics-panel`, `drive-panel`.
- Shared `packages/domain` (schema/types/history/editing/lyrics), `packages/composition/src/scene.tsx`; backend `amvs/app.py`, `edit_leases.py`, `store.py`, catalog/snapshot/jobs và Drive status/backup/restore boundary liên quan.
- Tests unit/domain, integration local-api/MVP/Drive/launcher và bảy file browser specs; fixture server, Playwright config và runners S6 để xác định vùng coverage/điểm coupling. Không dùng đọc test làm bằng chứng test pass.

## 2. Cấu trúc hiện tại và dependency

```mermaid
flowchart TD
    Page[app/page.tsx] --> Studio[Studio]
    Studio --> Controller[useStudio: session, record, history, jobs, lease]
    Studio --> Drive[DrivePanel: own polling / consent / OAuth state]
    Studio --> Dashboard[Inline Dashboard khi project null]
    Studio --> Editor[Inline Editor khi có project]
    Editor --> Preview[Remotion Player]
    Preview --> Scene[Shared ProjectScene]
    Editor --> Tools[ProjectTools: data + library + templates]
    Editor --> Lyrics[LyricsPanel: local draft + AI job polling]
    Editor --> Timeline[Timeline: selected + Player ref + move/change]
    Editor --> Inspector[Inspector: selected item + edit/change]
    Controller --> Domain[domain history / validation / remapLyrics]
    Controller --> Api[Api: token + editor ID per instance]
    Tools --> Api
    Lyrics --> Api
    Drive --> Api
    Api --> Proxy[Next same-origin proxy]
    Proxy --> Backend[FastAPI / SQLite / local workers / Drive]
```

- Global sidebar bên trái là **điều hướng project**, không phải Left Tool Panel. `.editor-layout` chỉ có preview/tools/timeline + inspector (hai cột).
- `Studio` giữ JSX Dashboard, editor và preset-rescale handlers. `useStudio` sở hữu history, `record.revision`, serial working-save queue, Player ref, jobs và lease; component con gọi `change/prepare/reload` nhưng cũng có direct API actions.
- `ProjectTools` gộp recovery/package/delete, local storage/quota/GC, library/tags/suggestions và personal templates; các `<details>` dài nằm trong `.editor-main` trước Lyrics/Timeline.
- `LyricsPanel` có `lines/input/audioId/model/language/job` state riêng. Remount khi đổi mode/tab có thể làm mất draft chưa lưu; polling/restore job cần sống ngoài tab content.
- Inspector đã có nhánh theo `item.type`, nhưng luôn lẫn project/name/duration/preset; Music Card metadata hiện theo template, chưa là inspector riêng.
- Timeline select/move/track order/add text gọi controller. Frame đọc từ Player bằng timer 100ms; trim chủ yếu bằng numeric Inspector, chưa có trim handles.
- DrivePanel mount thường trực phía trên cả Dashboard và Editor, polling 2s kể cả khi đóng form; restore xong chưa gọi `refresh` danh sách project của useStudio.
- CSS `min-height:100vh`, preview 470px/420px, không viewport grid/resize handle; một số danh sách có overflow riêng nhưng toàn Editor vẫn có nội dung dài.

## 3. Quy ước phân loại

**Đã hỗ trợ trong code** = có đường đi hiện hữu. **Hỗ trợ một phần** = có nền/chức năng nhưng chưa đủ UX mới. **Chưa triển khai** = chưa có cấu trúc/capability tương ứng. **Có dấu hiệu lỗi** = thấy nhánh mã rủi ro; phải tách khỏi nguyên nhân đã được chứng minh. **Cần kiểm chứng trên trình duyệt** = chưa có quan sát hiện tại; có thể đi kèm một trong bốn trạng thái trên.

### UI-01

| Yêu cầu | Phân loại | Bằng chứng / khoảng cách | Xử lý đề xuất |
|---|---|---|---|
| Hòa Âm, dark-purple | Đã hỗ trợ trong code | `studio.tsx` brand, `globals.css` tokens accent/panel | Giữ nhận diện, chuẩn hóa tokens |
| Creative Dashboard thay landing | Hỗ trợ một phần | Nhánh Dashboard còn hero/marketing text, không dashboard project content | Tách DashboardWorkspace |
| Hero gọn, ba template vùng nhìn đầu | Hỗ trợ một phần; cần kiểm chứng trên trình duyệt | Ba CTA tạo draft thật; padding 70px, h1 tới 60px, template margin-top 50px | Wireframe ở hai viewport, đo bounds |
| Recent projects | Hỗ trợ một phần | Sidebar có list; API `{id,name}` theo rowid, không last-opened | D-01 đã chốt xuyên phiên; thiết kế persistence ở R0/R1 |
| Sidebar/điều hướng | Có dấu hiệu lỗi; hỗ trợ một phần | “Studio của tôi” không handler; brand anchor không có navigation action | Navigation qua controller/dirty guard |
| Drive khỏi Dashboard chính | Chưa triển khai | DrivePanel render trước nhánh Dashboard | Entry Lưu trữ mở manager riêng |

### UI-02 — đối chiếu đầy đủ nhóm yêu cầu

| Mục đặc tả | Phân loại | Hiện trạng / khoảng cách cụ thể | Owner giai đoạn |
|---|---|---|---|
| §1–2 dark-first/design tokens | Hỗ trợ một phần | Có palette/type cơ bản; CSS global `main/footer/h1/button`, chưa thống nhất modal/tooltip/tab/toast/semantic states | R1 |
| §3 ba cột | Chưa triển khai | Global nav không thay Left Tool Panel; editor grid hai cột | R3 |
| §3 no page scroll/independent panels | Hỗ trợ một phần; cần kiểm chứng trên trình duyệt | Chỉ lyrics/library có max-height overflow; không `100dvh` shell, min-height 0 chain | R3 |
| §3 Preview/Timeline luôn hiện | Chưa triển khai theo yêu cầu mới | Tools và lyrics chèn giữa preview/timeline; dưới 850px Inspector xếp xuống dưới | R3 |
| §4 Header/back/project/save | Hỗ trợ một phần | Save/export/dirty có; back Dashboard chưa có, undo ở editor toolbar, save pending/error chỉ message/busy chung | R1/R2/R3 |
| §5 lease/read-only/takeover | Hỗ trợ một phần; có dấu hiệu lỗi; cần kiểm chứng trên trình duyệt | Có claim/5s heartbeat/30s expiry/release/takeover + revision. R0 đã chứng minh race C03 và nhánh C04–C06; chưa sửa, xem báo cáo R0 | R0/R2 |
| §6 năm tabs Left Panel | Chưa triển khai | Chưa có tool tabs; nhiều details trong main | R3/R4 |
| §6.1 import/search/tag/reuse | Đã hỗ trợ trong code cho luồng hiện tại | Multiple upload + partial errors, library search/tag/reuse/audio listen; placement chưa đúng | R4 |
| §6.1 type filter/format/video preview | Hỗ trợ một phần | Có kind/duration/mime trong asset DTO; chưa có filter/format label và video player trong library | R4 |
| §6.1 thumbnail fallback/retry/long names | Hỗ trợ một phần | lazy thumbnail, wrapping CSS; chưa onError/retry UI | R4 |
| §6.1 media drag/drop | Chưa triển khai | Không thấy media drag/drop từ library; chỉ có clip reposition timeline | R4, chỉ sau kiểm chứng |
| §6.2 Text tools | Hỗ trợ một phần | Add text ở Timeline, chọn clip và style ở Inspector; chưa text tab/preset browser | R4 |
| §6.3 Effects/Templates | Hỗ trợ một phần | Các animation enum dùng được; personal template typed slots/instances có. Chưa browser preset nhóm/live effect preview | R4 |
| §7 composition/ratio/Play-Pause | Đã hỗ trợ trong code cho nền hiện tại | Shared Player/Scene, dimensions/FPS theo project, Play/Pause thật | Giữ R3/R4 |
| §7 preview controls/safe area | Hỗ trợ một phần | Seek ở ruler; thiếu scrubber/timecode/mute-volume/fullscreen riêng và safe-area overlay | R3/R4; fullscreen policy D-05 |
| §8 contextual Inspector | Hỗ trợ một phần | Có type branches; project/preset/Music Card trộn chung; chưa clear selection dễ dùng | R4 |
| §8 image/video transforms | Hỗ trợ một phần / capability chưa triển khai | fit/crop position/blur/brightness có; schema/scene không có arbitrary zoom/rotation/general transform/filter presets | D-02: R4.A field hiện hữu, R4.B advanced sau review delta |
| §8 audio/video speed | Hỗ trợ một phần | Rational `speed` và playbackRate renderer có; Inspector chưa có input speed. Audio volume=0 có thể mute; chưa toggle riêng | R4, giữ mapping/validation |
| §8 Text/Lyrics typography | Hỗ trợ một phần | Fonts 2 loại, size/color/stroke/shadow/x/y/animation có; rotation chưa contract; highlightColor có schema/scene nhưng chưa control | R4 |
| §8 Music Card | Hỗ trợ một phần | Metadata role/title/artist, cover theo ảnh thứ hai, typography có; layout/progress style là giá trị scene cố định | D-02 giai đoạn B; không dựng field giả |
| §8 numeric/slider/reset/disabled reason | Hỗ trợ một phần | Nhiều numeric, audio range, fieldset read-only; chưa paired controls/reset/reason nhất quán | R1/R4 |
| §9 dock/resize | Chưa triển khai | Timeline trong document flow; chưa separator/resize/reset/persist size | R3 |
| §9 select/reposition/seek/zoom/order/undo | Đã hỗ trợ trong code cho nền hiện tại | Pointer-up commit move, zoom 1–8, track order; trim ở Inspector | Giữ R3/R4, browser regression |
| §9 trim handles/split/duplicate/snapping/visibility | Hỗ trợ một phần / chưa triển khai | Numeric trim có; các thao tác advanced chưa có. Spec cho split/duplicate/snapping/visibility theo capability; không tự mở Complete | R0 D-02 |
| §10 Recognition | Hỗ trợ một phần | Audio/model/language/start/cancel/import/draft/job reopen có; chưa mode riêng, quyền UI chưa thống nhất | R2/R4 |
| §10 Editing/Alignment | Hỗ trợ một phần | Sentence edits/review/apply, align job/fallback có; chưa source audition/word detail UI | R4 |
| §10 Styling/Draft-Reviewed-Applied | Hỗ trợ một phần | Style nằm Inspector, words highlight trong Scene; Applied suy ra lyric items, không enum trong schema | R4; không thêm enum persisted |
| §11 Storage workspace | Chưa triển khai về layout; nền Drive đã có | OAuth/config/folder/backup/auto/restore/exports có trong panel inline | R5 |
| §11 last backup/history | Hỗ trợ một phần | `lastBackup` có backend, chưa trong frontend DriveState; `GET drive/backups` có list, chưa manager history UI | R5, dùng field hiện hữu |
| §11 progress/errors/cancel | Hỗ trợ một phần; thiếu capability | Backend message theo file/phase; không byte-% contract, không cancel backup/restore endpoint; async failure message gộp network/permission/quota | D-03 đã chốt cần capability thật; thiết kế delta trước code |
| §11 consent/safety | Đã hỗ trợ trong code cho các đường hiện tại; cần browser regression | Explicit backup consent, auto default off ở cấu hình mới; snapshot/checksum/no overwrite/no local delete | R5/R6 giữ đầy đủ |
| §12 Export workspace | Chưa triển khai về layout; nghiệp vụ hỗ trợ một phần | Preset trong Inspector, toolbar gọi picker + jobs, kết quả cuối trang | R5 |
| §12 resource preflight/wait/cancel/retry/output | Hỗ trợ một phần | Missing media endpoint; job admission/disk/validation ở backend. Chưa resource-preflight DTO riêng; không hứa trước queued là đủ RAM | R5, hiển thị status/message backend |
| §13 global states | Hỗ trợ một phần | Inline status/alert + busy/dirty/missing/read-only; chưa state taxonomy/toast/retry/error boundaries thống nhất | R1/R2/R5 |
| §14 UI-ED-01…15 | Cần kiểm chứng trên trình duyệt | Suite cũ có một phần flows; chưa assert geometry/resize/keyboard mới | R0 baseline và R6 |
| §15–16 scope/governance | Đã xác định ràng buộc | Không đổi code lúc này; delta cần thiết theo D-01…04 được thiết kế trước code, không mockup thay chức năng | Mọi R |

## 4. Lease: dữ kiện, giả thuyết và cách chứng minh

**Cập nhật R0:** đã xác nhận race response claim cũ ghi đè quyền sau takeover (3/3 production + 3/3 development với barrier và quan sát sau 6s), cùng các nhánh lỗi feedback/reload/heartbeat. Xem [báo cáo R0 và evidence](UI_R0_LEASE_DIAGNOSIS.md). Chưa quy kết mọi triệu chứng trong phiên người dùng trước đây cùng một nguyên nhân. Bảng dưới giữ danh sách giả thuyết khảo sát ban đầu; chỉ các case C03…C06 trong báo cáo được nâng thành đã tái hiện.

| ID | Dữ kiện đọc được | Tác động có thể xảy ra / kiểm cần làm |
|---|---|---|
| L-01 | `adopt()` đặt writable=false rồi claim; takeover POST → set true → GET → adopt → claim thêm | Cửa sổ pending và response đến sai thứ tự; cần trace thứ tự request, project ID + generation + editor ID đã che/mã hóa |
| L-02 | Nút takeover gọi `.catch(() => {})`; hàm takeover không tự set error, canWrite=false không có nhánh feedback | Có nhánh lỗi bị nuốt ở UI. Đây là thiếu feedback nhìn thấy từ mã, không chứng minh nguyên nhân permission failure |
| L-03 | Heartbeat chỉ chạy khi `writeRef.current` true; heartbeat error chỉ set message | Read-only không tự biết owner đã đóng; network/expiry có thể để UI vẫn bật trước khi server từ chối. Kiểm TTL/close/background tabs |
| L-04 | Request adopt chỉ kiểm project ID, không generation; queued sync dùng record hiện tại theo ID | A→B→A hoặc load/takeover nhanh cùng ID có thể áp response cũ; cần delayed-response tests trước kết luận |
| L-05 | Release trong effect cleanup + beforeunload, không xác nhận unload thật xảy ra; đang dùng keepalive | Hủy đóng tab/StrictMode/remount có thể đổi lifecycle. Tái hiện cả dev StrictMode và production, không bỏ release bảo vệ |
| L-06 | `Api` tạo editor UUID mỗi instance, token bootstrap riêng; error wrapper chỉ giữ message, bỏ status/code | Remount controller có thể tạo phiên mới; khó phân biệt SESSION/Conflict/DRIVE. Kiểm stable Api identity; giữ HTTP code trong client không đổi DTO |
| L-07 | Inspector/Timeline nhận editable; ProjectTools/LyricsPanel không nhận quyền chung, một số API direct | Project mutation thường bị `change`/server chặn nhưng affordance lệch; phân biệt catalog/global actions với project writes, không disable toàn bộ read actions |
| L-08 | Backend guard chặn khi có lease sai owner/hết hạn; **không có row thì guard cho qua**. PATCH có optimistic revision; save kiểm guard trong worker | Không phải hệ exclusive lease bắt buộc cho mọi write ở mọi endpoint. Nếu cần siết semantics backend phải có reproduction/đề xuất riêng; không tự đổi trong redesign |
| L-09 | Một số job/template/package endpoint dùng revision, không lease.guard | Quyền khởi job khác quyền sửa project. Giữ policy hiện tại, xác định UI permissions rõ trước thay đổi; không quảng cáo mọi endpoint fenced |

Thu thập tối thiểu: dev/production, một/hai tab, TTL, suspended/resumed, đóng thường/kill owned test browser, reload launcher, 401/409/timeout, click takeover nhiều lần, request đảo thứ tự, dirty before takeover, Manual Save đang chờ worker. Không log token, OAuth JSON, media contents hay raw project text. Dùng disposable workspace, không tự kill launcher đang chứa dữ liệu người dùng.

## 5. Sổ quyết định D-01–D-06 — cập nhật PO 24/11/2026

Các hàng dưới đây ghi quyết định mới của PO, không phải trạng thái đã triển khai. Phần khảo sát mã tại §2–4 vẫn phản ánh baseline `ba60ab0`. UI-01 vẫn Proposed; UI-02 nguyên văn vẫn Approved for Design — Not Implemented. Chưa có lệnh triển khai code hoặc commit/push trong cập nhật này.

| ID | Vấn đề | Quyết định / định hướng | Trạng thái |
|---|---|---|---|
| D-01 | Dự án gần đây | Lưu lịch sử mở project xuyên phiên | PO đã chốt hướng |
| D-02 | Inspector và Timeline nâng cao | Giữ đầy đủ yêu cầu; triển khai theo hai giai đoạn | PO đã chốt hướng; phân bổ chi tiết hai giai đoạn là đề xuất |
| D-03 | Google Drive | Storage Manager hoàn chỉnh, bổ sung progress/error/cancel thật | PO đã chốt hướng |
| D-04 | Ghi nhớ bố cục Editor | Lưu tùy chọn giao diện trên máy, độc lập dữ liệu project | PO đã chốt hướng |
| D-05 | Màn hình nhỏ và fullscreen | Compact layout + chế độ fullscreen Preview riêng | PO đã chốt hướng |
| D-06 | Asset DTO và Media Metadata | Chuẩn hóa Asset DTO và Media Metadata | Recommended Decision; chi tiết field/nullable/version chưa chốt |

### Tác động tới kế hoạch

- **D-01:** thay phương án recent chỉ trong memory bằng persistence local. Đề xuất lưu metadata theo workspace ngoài project content, không coi mỗi GET là một lần mở. Cần thiết kế ở R0, thực hiện ở R1 sau khi được phép triển khai; test xuyên browser/launcher restart và port thay đổi. Không suy thành lịch sử cloud/cross-PC.
- **D-02:** đề xuất giai đoạn A là cấu trúc workspace và capabilities đã có; giai đoạn B bổ sung capabilities còn thiếu với schema/composition/backend thay đổi tối thiểu khi thực sự cần. Toàn bộ yêu cầu UI-02 giữ nguyên; phase A không được đánh dấu hoàn tất advanced hoặc full redesign. Split/duplicate/snapping/visibility vẫn theo điều kiện capability/task mở rộng trong đặc tả, không tự biến mọi tính năng Complete thành cam kết mới.
- **D-03:** không dừng ở chuyển panel sang dialog. R5 phải có backend transfer progress thật, error categories an toàn và cancel upload/download thật; cancellation phải giữ local bytes, bản backup thành công trước đó, không publish manifest/output dang dở. Không nhầm hủy OAuth/đóng dialog/disconnect với hủy transfer. Contract thiết kế mới cần kiểm backward compatibility và được review trước code; không bịa % từ timer.
- **D-04:** lưu preferences local tách content/DB project/manual snapshots/Drive backups. Đề xuất store có version, validated bounds/defaults/reset; scope dự kiến activeTool/lyricsMode/timelineHeight và trạng thái panel được duyệt, không lưu draft lyrics/token/credentials/lease. Localhost đổi port khiến browser localStorage đơn lẻ không đủ; storage mechanism và multi-tab conflict policy cần chốt ở R0. Thay UI preferences không làm project dirty/revision/history thay đổi.
- **D-05:** normal desktop vẫn ba cột + preview/inspector/timeline đồng thời. Compact phải có lối vào controls đầy đủ; fullscreen Preview do user chủ động là mode riêng, tạm thay workspace thường, thoát thì phục hồi layout/playhead/selection/quyền hiện hành. Không coi compact là mobile Editor đầy đủ; breakpoints/kích thước phải kiểm trên browser.
- **D-06 Recommended:** rà field thật tại API/probe/schema và gom Asset DTO frontend/backend thống nhất; phân biệt ảnh không có duration và metadata chưa biết, dùng ticks/bytes rõ ràng, không lộ path. Các field tối thiểu/candidate, compatibility và xử lý metadata cũ đề xuất trong kế hoạch. Không coi Recommended là quyền tự thêm field/đổi dữ liệu.

### Ranh giới thay đổi

Lượt này chỉ sửa tài liệu. Quyết định mới cho phép lập thiết kế các mở rộng có mục đích ở D-01…04, thay cho giả định cũ “chỉ frontend/giữ nguyên mọi contract”. Chưa thực hiện thay DB/API/schema/renderer. Kế hoạch thực thi và các delta kỹ thuật phải được review trước code; không lấy các quyết định này làm quyền viết lại AI Engine, đổi codec, cloud-first hoặc refactor toàn bộ backend. R0 đã xác nhận nguyên nhân cho các kịch bản trong [báo cáo lease](UI_R0_LEASE_DIAGNOSIS.md); chưa triển khai bản sửa.

## 6. Coverage hiện có và phần thiếu

| Nguồn test | Đã có assertion trong mã | Thiếu đối với redesign |
|---|---|---|
| `tpl01`, `multi-media`, `music-card` E2E | Import thật, edit/reorder/trim/undo, manual save/reopen, MP4/job | Entry navigation/DOM selectors mới, viewport no-scroll, dialog export |
| `core-workflows` E2E | Lyrics import/review/style/preset/recovery/package; template; labelled AI transport; 12/100 clips; hai tab takeover | Draft survive mode switch; takeover failure/expiry/close/launcher/manual-save-undo-after-takeover; panel geometry |
| `drive-settings` E2E | Config/cancel OAuth **local**, bootstrap origin restrictions | Storage dialog/focus, last backup/history, restore refresh; không phải Google thật |
| `fidelity`, `long-run` E2E + scripts | Opt-in screenshot-vs-MP4, 300s snapshot/dirty/resource | Rerun theo ảnh hưởng code; không dùng screenshot layout thay độc lập decode |
| `test_local_api`, `test_mvp_completion` | Optimistic conflict/manual hash/race, recovery/package/pins, lease/expiry, queued-save takeover | Kịch bản browser lifecycle và state machine mới |
| `test_drive`, launcher tests | Consent/OAuth/checksum/no overwrite/fault/owned tree | UI focus/semantics; không thay browser/cloud test |
| Unit `domain/editing/music-card/lyrics` | Hash/schema/history, template independence/source mapping | Pure UI reducer/resize math nếu thêm sau duyệt |

Playwright hiện mặc định 1440×1000, 1 worker; nhiều selector dựa `.navigation .current-project`, `.ruler`, `.clip`, labels/summary cũ. Các test này cần di chuyển entry/selector có chủ đích; giữ assertion nghiệp vụ, không xóa test để xanh. R0 ghi artifact baseline mới; R6 phải có 1366×768 và 1920×1080. Lượt khảo sát ban đầu không chạy lại các suite. Lượt R0 hiện có browser diagnosis riêng và 3 integration tests thật; không chạy lại full regression và không coi tái hiện bug là pass UI-ED. Layout baseline đã đo và UI-ED-01/02 chưa đạt; root cause lease và giới hạn từng case ở báo cáo R0.

## 7. Lưu ý hồ sơ

Một số dòng RTM còn nói inference/output bị RAM chặn, và báo cáo implementation cũ nói chưa push, trong khi checkpoint `ba60ab0` và evidence S6 mới hơn đã có. Không dùng dòng cũ làm kết luận hiện tại, không nâng Verified từ số test. Trong nhiệm vụ này chỉ ghi discrepancy ở đây; không sửa RTM/ADR hoặc các quyết định đã chốt.
