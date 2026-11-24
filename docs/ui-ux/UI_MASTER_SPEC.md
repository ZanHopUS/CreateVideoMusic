# HÒA ÂM — UI/UX MASTER SPEC & IMPLEMENTATION PLAN v2.1 — FULL R1–R6 EXECUTION

**Dự án:** AI Music Video Studio — Hòa Âm
**Repository:** `ZanHopUS/CreateVideoMusic` · nhánh mục tiêu `dev`
**Baseline đã kiểm tra:** `72303821a811e18195f071e5159d4373771d593f` (24/11/2026)
**Trạng thái:** **PO phê duyệt hướng triển khai toàn bộ UI redesign R1–R6 và các phương án mặc định trong tài liệu này**. Đây **không** phải xác nhận code đã chạy, nghiệm thu test, hay cho phép tự động commit/push/merge/xóa dữ liệu thật.
**Nguồn ưu tiên:** `AGENTS.md`, PRD/SRS/RTM/ADR/MVP Contracts, `DESIGN_SYSTEM.md`, UI-01…UI-06, `UI_GAP_ANALYSIS.md`, `UI_REDESIGN_PLAN.md`, R0 Lease results. Tài liệu này tổng hợp quyết định PO và điều phối triển khai, không thay thế hợp đồng nghiệp vụ/bảo mật đã có.

## 1. Chỉ đạo tổng thể của Product Owner

PO đã phê duyệt:
- **MR-01:** Navigation chính: **Tổng quan / Dự án / Lưu trữ / Cài đặt**. Editor mở theo project/template; Export là dialog; Recovery thuộc Project Management.
- **MR-02:** Dashboard: CTA ngắn → **3 template thật TPL-01/02/03** → dự án gần đây; không dùng quota, thumbnail, ngày mở hay sản phẩm giả.
- **MR-03:** Một application controller giữ authority; chuyển *workspace* không tự mất project/dirty/history/lyrics draft/job/lease. Chuyển *project* bắt buộc dirty/draft guard; lúc về Editor kiểm lại lease.
- **MR-04:** Đồng bộ tất cả tài liệu và code theo cấu trúc trên, sửa tham chiếu cũ/mâu thuẫn.
- **UI-02:** Editor ba cột, Preview và Timeline dock, no page scroll khi Editor normal, inspector theo selection, Lyrics workflow đầy đủ.
- **UI-03 ST-01…07:** Storage workspace riêng với 4 tab (Tổng quan/Bản sao lưu/MP4 khôi phục/Cấu hình), transfer progress/error/cancel thật, lịch sử snapshot khác lịch sử tác vụ, auto backup off mặc định, cloud acceptance thật có consent, giữ Editor state.
- **UI-04:** Export **dialog hai cột**, đóng dialog **không hủy render**, job ngoài component.
- **UI-05 PM-01…03:** Project Management workspace Grid/List, Recovery section riêng, delete bằng chọn action rồi dialog xác nhận.
- **UI-06 STG-01…03:** Settings workspace sidebar/content, Hybrid Save, Google Drive chỉ summary/link UI-03.
- **Design System:** Minimal Professional; dark slate/charcoal, muted lavender, **tất cả góc giao diện ứng dụng bằng 0**, không glow/gradient/shadow trang trí; Segoe UI v1, body14/label13/caption12; không đổi video composition của người dùng.

**Phạm vi cho Codex (PO cập nhật):** **Triển khai liên tục toàn bộ R1.A→R1.B→R2→R3→R4.A/B→R5.A/B→R6 trong một nhiệm vụ dài, không dừng xin PO nghiệm thu giữa các phase.** Tự kiểm thử, sửa lỗi và ghi checkpoint vào tiến độ, rồi chuyển phase tiếp theo nếu các điều kiện an toàn đều đạt. Nếu cần thay đổi breaking schema/API/domain/bảo mật, thao tác dữ liệu thật, cloud upload thật hoặc gặp quyết định có nguy cơ mất dữ liệu chưa xác định: cô lập phần đó thành **Blocked — Needs PO Decision**, tiếp tục các phần độc lập, không ngầm làm liều hoặc bỏ hẳn phạm vi. **Không tự commit/push/merge.**

## 2. Kiến trúc và điều hướng chuẩn

```text
AppController (mounted once: project, lease/revision, dirty/history/drafts,
               jobs, Drive status, app preferences, navigation)
├── DashboardWorkspace (UI-01: CTA/templates/recent)
├── EditorWorkspace (UI-02: header + left tools | preview | inspector + timeline)
├── ProjectManagementWorkspace (UI-05: Grid/List + Recovery)
├── StorageManagerWorkspace (UI-03: 4 tabs)
├── SettingsWorkspace (UI-06: 6 sections)
└── DialogHost (UI-04 Export, Rename, Delete, Import/Package, confirmations)
```

**Navigation matrix:**

| Hành động | Yêu cầu |
|---|---|
| Từ Dashboard tạo template | Dùng TPL-01/02/03 thực; only transition sau controller success. |
| Mở project | Load + valid lease claim; read-only nếu không có quyền; bỏ stale responses theo generation. |
| Editor → Dashboard/Projects/Storage/Settings | Đổi view, **không đồng nghĩa đóng project**; giữ draft/jobs/lease theo session; không release vì đổi view. |
| Editor A → Editor B | Dirty/manual-save guard + lyrics draft guard; không âm thầm discard; tránh auto-adopt sau import. |
| Quay lại Editor | Đọc lease hiện hành; không tự phục hồi quyền writable stale. |
| Export dialog đóng | Render tiếp tục theo jobId/snapshot; mở lại xem progress/result. |
| Drive backup/restore hoặc local import hoàn tất | Refresh đúng list; không tự chuyển project/xóa dirty draft. |
| Settings đổi section | Settings draft guard riêng; project dirty không bị thay đổi. |

**Routes:** Giai đoạn đầu giữ origin `/` và chuyển workspace bằng application state vì session/bootstrap hiện phụ thuộc origin/Referer; không tự thêm deep-link Next.js trước security review.

**Ownership:** Không nhân đôi writer/controller; status and async operations keyed by projectId/jobId/operation epoch; request cũ không được ghi đè state mới. Job/transfer sống ngoài dialog/workspace. Không dùng reload trang như cách đồng bộ list.

## 3. Các màn hình — phạm vi khóa

| UI | Thiết kế bắt buộc | Phần cần xác minh trước khi hiển thị |
|---|---|---|
| UI-01 Dashboard | Sidebar 4 mục, hero gọn, 3 template trước recent; CTA và links hoạt động; scroll khi danh sách dài | `GET /projects` baseline chỉ id/name; recent timestamp cần TC-01; không fake metadata |
| UI-02 Editor | 3 cột, Timeline adjustable, Preview contain, no body scroll, inspector contextual, 5 tool tabs/Lyrics, R0 lease | D-05 compact min sizes và renderer parity; advanced D-02 triển khai qua giai đoạn B |
| UI-03 Storage | Workspace riêng 4 tabs, OAuth/consent/auto-off, snapshot/history phân biệt, safe restore | Drive status có nhưng full progress/cancel/history contract chưa có; chỉ cloud test thật với tài khoản/consent |
| UI-04 Export | 2-col modal, preview/validation + config, grant native, render background/reopen | Không fake filename custom/preflight, preserve project preset/history; snapshot/job metadata thật |
| UI-05 Projects | Workspace Grid/List, Recovery riêng, dialogs Save/Package/Import/Relink/Delete | Local recovery cùng project ID; delete chưa bảo vệ stale revision; không hứa Trash/Undo |
| UI-06 Settings | Workspace 6 sections, hybrid persistence, Drive summary/link, storage/AI/system | D-04 store chưa có; cache/source GC và model chỉ theo API capabilities thật |

**UI-01 phê duyệt ở mức thiết kế:** thứ tự, nav, hierarchy, hai desktop viewport thử nghiệm; các số đo chỉ là **implementation targets** chứ không bảo đảm đã đo: sidebar ~208 px, header ~56 px, content padding ~24 px, 3 template cùng hàng desktop, recent ngay sau; chỉnh theo browser geometry để đạt first fold tại 1366×768 và 1920×1080.

## 4. Nguyên tắc bắt buộc và ranh giới an toàn

1. **Local-first:** Editor hoạt động không cần Google Drive. Không tự cloud-first/collaboration.
2. **Content/hash:** Preferences, navigation, scroll/panel layout không thay `project.contentHash`, revision, undo/history hay `manualSavedHash`.
3. **Manual Save B/Edit C:** Save B trong khi tiếp tục edit C không đánh dấu C là saved. Working save ≠ Manual Save ≠ Recovery ≠ Backup.
4. **Lease R0:** Không tự bỏ guard/TTL/expected revision/409 handling để UI “mượt”. Nếu canWrite thay đổi, Editor phải chuyển read-only trung thực.
5. **Snapshot immutable:** Render và package dựa trên pinned snapshot/revision; edit sau submit không đổi output.
6. **Native grants:** File/folder qua chooser/grant hiện hành; không ghi/chuyển arbitrary absolute paths từ frontend.
7. **Delete/GC:** Project DELETE không đồng nghĩa xóa source. Source GC có preview, consent, backend recheck pins; không xóa backup/recovery/job staging khác scope.
8. **Drive:** Backup 202=accepted, chưa success; verify manifest/checksum; auto-off, consent; closing workspace≠cancel.
9. **No fake UI:** Không fake progress/metadata/quota/model/thumbnail/error/success. Trường chưa biết hiện “Chưa có thông tin” hoặc trạng thái không hỗ trợ minh bạch.
10. **Security:** Không persist credentials/tokens/capability secrets trong project, logs, localStorage, diagnostics, backups hoặc tracing.
11. **Style scope:** Tokens/css chrome không rò vào Player/Remotion composition.
12. **Không tự commit, push, merge, xóa dữ liệu thực, chạy cloud transfer thật khi chưa có tài khoản/quyền và consent.**

## 5. Phương án kỹ thuật mặc định PO chấp thuận — triển khai có điều kiện

Các quyết định bên dưới là **default kiến trúc** được PO chấp thuận để Codex không liên tục hỏi lại. Tên field/endpoint/schema chính xác **phải dựa trên code và backward compatibility**; không xem default là đã có implementation.

### TC-01 — D-01: Recent Projects
- Lưu recent theo workspace/local backend, **ngoài project content**; ưu tiên app-owned metadata store có version và atomic persistence.
- Event ghi: project thực sự được mở thành công (kể cả read-only nếu load thành công); không tính GET/polling. Time server canonical nếu có; ID là khóa định danh, tên trùng hợp lệ.
- Giới hạn đề xuất **tối đa 30 recent entries**, Dashboard chỉ hiển thị tối đa **6**, Project Management xem đầy đủ; giá trị là default để triển khai/test, có thể thay khi UX đo cho thấy cần.
- Project missing/deleted → loại khỏi danh sách mở được sau reconcile; data migration an toàn; tests restart/port change/multi-tab; không đổi content dirty.

### TC-02 — D-04: Application UI Preferences
- Dùng app-level local backend storage **riêng namespace/schema** với TC-01, có version, defaults, bounds, atomic write và corrupt fallback.
- Keys khởi điểm: `timelineHeight`, `activeTool`, `lyricsMode`, panel display/width khi khả dụng, `projectViewMode` Grid/List; không lưu lyrics draft/secrets/lease.
- Conflict multi-tab: ưu tiên **per-key compare-and-set version** nếu có cơ chế thực tế; nếu quá nặng, dùng last-write-wins theo từng key với version/timestamp và công khai trong contract, không overwrite cả object stale.
- Immediate settings chỉ báo saved khi persistence xác nhận; reset layout không reset projects/manual content; test reload/restart/different localhost port/two tabs.

### TC-03 — Application controller & navigation
- Một controller ownership; navigation state tách `project === null`; giữ live project/draft/history/lease/job tracking.
- Dùng guards trước **switch project** (save/continue with warnings/cancel theo capability), không yêu cầu mỗi lần chỉ mở workspace đều Manual Save.
- Background job registry theo stable jobId/projectId; không restart job khi view mount; khi reload chỉ hiển thị trạng thái nếu backend có endpoint/metadata xác thực, không hứa resume job sau launcher shutdown.

### TC-04 — D-06: Asset DTO / Media metadata
- Chuẩn hóa **non-breaking**, không thêm field bắt buộc vào legacy projects; field candidate `id,name,kind,mime,tags,bytes,width,height,durationTicks,codec` khi probe có thật.
- Tách `unknown` khỏi `not-applicable`, nullable/optional đúng, ticks=48000/sec nếu dùng timebase; tuyệt đối không suy codec từ extension.
- Schema version/migration/contract tests phải được phân tích **trước khi đổi API**. Nếu yêu cầu breaking API/project schema, dừng delta để PO review.

### TC-05 — Drive lifecycle R5.B
- Operation record có id/type/phase/status/timestamps/error safe/known bytes-files/terminal result, durable history bounded; snapshot manifests là danh sách khác.
- Backend kiểm chứng progress thật; indeterminate nếu không có denominator; request cancel → cancelling → terminal, race thành công vs cancel xử lý theo kết quả backend.
- Retry attempt mới không xóa history cũ; cleanup chỉ staging thuộc operation, giữ local/source/backup đã thành công.
- OAuth configuration, secure credentials, consent và manifest verification giữ ADR-0002; cloud end-to-end chỉ sau khi có tài khoản/consent hợp lệ.

### TC-06 — Export
- Preset draft trong dialog → **Áp dụng vào project** qua controller/history hiện có → mới xuất; Cancel trước Apply không dirty; Apply là một transaction/Undo đúng.
- Tên MP4 tùy chỉnh: ưu tiên hỗ trợ thật bằng contract basename an toàn (Unicode/Windows reserved/extension/collision/no overwrite); **không hiển thị input cho tới khi API hoạt động**.
- Job status/result DTO tối thiểu không leak private paths, snapshot/revision/source summary đủ dùng; retry mặc định “Xuất project hiện tại” tạo attempt mới, không giả resume snapshot B sau restart.
- Không bịa RAM preflight; hiển thị “Hệ thống sẽ kiểm tra khi nhận tác vụ” nếu chưa có API read-only. Resource errors cần structured safe codes nếu muốn UX sâu hơn.
- Job-create permission phải giữ expected revision và bảo mật session/lease; không sửa lease policy chỉ theo UI. Modal width target ~1000px, đo thực tế tại hai viewport.

### TC-07 — Project data safety
- Noncurrent rename phải có valid revision/permissions; không auto takeover.
- **Local recovery là restore working state cho cùng project**, không mặc định tạo project mới; Drive restore/import có semantics riêng.
- Trước DELETE cần hiển thị target+impact theo dữ liệu thật; nếu backend chưa có revision precondition thì xây hợp đồng atomic delete/revision hoặc ít nhất bảo vệ stale target ở UI và ghi rõ giới hạn. **Không tự triển khai destructive backend delta khi chưa có regression và review diff.**
- Project DELETE không auto GC; orphan recovery/retention/access phải được thiết kế và test trước khi hứa restore sau delete.
- Package `.amvs` immutable/verified, import không tự adopt nếu current dirty, native grant; relink đúng asset ID/hash và rights.

### TC-08 — Settings/maintenance
- Settings Hybrid: toggle/reversible field immediate nếu save có xác nhận; policy/config quan trọng có Save/Cancel; separate settings dirty.
- Source GC preview/confirmed IDs/recheck pins; cache/temp cleanup tách biệt, hiển thị partial failures thật.
- AI model status lấy provider API; không thêm install/download/CPU-GPU switch khi không có.
- Drive summary đọc chung Drive state với UI-03, không thêm OAuth owner thứ hai; diagnostics chỉ từ nguồn có thật và lọc secret.

**Hợp đồng kỹ thuật chi tiết** (method/path/DTO/nullable/status/error/upgrade/roll-back) Codex phải lập trong repo khi bắt đầu phase liên quan. Những endpoint/field mới phải có test và migration; khi phát hiện breaking/ambiguous policy, dừng *chỉ phạm vi liên quan* xin duyệt. Đây là ranh giới an toàn, không phải yêu cầu PO duyệt lại các UI choices.

## 6. Implementation backlog và cổng nghiệm thu

| Phase | Scope giao Codex | Done khi |
|---|---|---|
| **R0 gate** | Đọc evidence R0 lease, rà test hiện tại, chụp current UI/browser baseline. Không rewrite R0. | Có baseline commands/results và blockers; R0 regression suite giữ được. |
| **R1.A** | Tokens, scoped CSS, Button/Input/Select/Dialog/Tabs/Status/Progress/ProjectCard primitives + state specimens. | Visual computed radius0/colors/contrast, keyboard/focus, composition CSS isolation; unit/typecheck/build không hồi quy. |
| **R1.B** | Dashboard UI-01, nav MR-01/02, real template CTA, shared Projects primitives, TC-01 recent. | 3 cards first fold hai viewport; recent thực qua restart/port-change; empty/error/dirty guards; UI-DB AC. |
| **R2** | Controller state extraction, navigation ownership, lease generation, TC-02 settings pref foundations, TC-03 job registry. | State không remount; stale responses không vượt quyền; B-save/C-edit và project-switch guards pass. |
| **R3** | Editor header/three columns/Preview/Timeline dock/resize/compact/fullscreen. | No body scroll normal, Preview+Timeline trong viewport, pointer/keyboard resize, D-04 persistence; screenshot geometry và R0 tests. |
| **R4.A** | Media/Lyrics/Text/Templates/Inspector capabilities đang có; không fake controls. | Asset/lyrics draft không mất qua tab, typed Inspector đúng object; preview/render parity. |
| **R4.B** | Advanced capabilities thật theo UI-02 D-02, TC-04 metadata hợp đồng. | Domain/schema/renderer + legacy roundtrip tests cho mỗi feature; không chỉ CSS mock. |
| **R5.A** | Storage workspace hiện có, Export dialog baseline, Projects workspace, Settings workspace; preserve consent/save. | Capability đang có dùng được qua UI mới, không mất jobs/state; không nhận là full Drive nếu cancel còn thiếu. |
| **R5.B** | TC-05 Drive full progress/error/cancel/history + TC-06/07/08 capability deltas cần thiết. | Backend integration/cancel race/no-overwrite/source pins; cloud thật theo consent; error UI, filename/results thực. |
| **R6** | Full regression, accessibility, responsive, UX review. | UI-DB-01…07, UI-ED-01…15, UI-ST-01…11, UI-EX-01…15, UI-PM-01…16, UI-SET-01…16; evidence và PO acceptance. |

**Thực thi tuần tự theo dependencies.** R1.A có thể bắt đầu ngay; không để R5 contracts chặn nó. R4.B/R5.B có thể lên kế hoạch sớm nhưng chỉ code khi contracts cần thiết đã được chốt và bảo vệ compatibility.

## 7. Test & evidence bắt buộc

- Unit/integration/typecheck/format/build và E2E browser **dev + production** theo `AGENTS.md`, README và scripts thực tế; không sáng tạo lệnh nếu repo không có.
- Viewports chính: **1366×768 và 1920×1080**. Zoom/reflow, keyboard/NVDA, reduced motion; Editor compact dưới các ngưỡng phải được test riêng và phân biệt `Blocked` với `Passed`.
- Test flows: create templates, recent restart+port change, project duplicate names, editor lease/takeover/expiry/409, manual B-save/C-edit, switching while dirty, back/forward workspace, job close/reopen, lyrics draft; preview/export parity; missing media/relink; package/import/recovery/delete/GC pins; Drive OAuth/consent/cancel races.
- Test data: fixture synthetic/disposable workspace; không dùng project/media người dùng để chạy destructive tests. Cloud thật cần tài khoản/folder/quyền upload của PO và consent riêng.
- Mỗi AC ghi **Not Run / Passed / Failed / Blocked / Not Applicable**, command/env/HEAD/evidence; skipped tests không được tính pass.
- Không hạ threshold resource/admission hoặc bỏ assertions để làm test xanh; ghi rõ resource-blocked.

## 8. Lịch sử và trạng thái tài liệu

Các file hiện có là nguồn triển khai:
- `docs/ui-ux/DESIGN_SYSTEM.md`
- `docs/ui-ux/UI_01_DASHBOARD.md`…`UI_06_SETTINGS_WORKSPACE.md`
- `docs/ui-ux/UI_REDESIGN_PLAN.md`
- `docs/ui-ux/UI_GAP_ANALYSIS.md`
- `docs/ui-ux/UI_R0_LEASE_FIX_RESULTS.md`
- `docs/architecture/MVP_CONTRACTS.md`

**Tài liệu cần đồng bộ ở phase đầu**:
1. Lưu file này tại `docs/ui-ux/UI_MASTER_SPEC.md`.
2. Ghi MR-01…MR-04 Approved trong hồ sơ và UI-01: hướng thiết kế đã Approved, pixel/wireframe implementation targets vẫn cần browser validation.
3. Sửa Design System mô tả Project Management từ “Dashboard list/table” thành workspace riêng, UI-06 Settings riêng; Storage/Export đúng hình thức.
4. Cập nhật plan cây components và phase dependencies; không xóa evidence lịch sử R0.
5. Kiểm tra `AGENTS.md` path docs bị lệch so với PRD/SRS/RTM/OPEN_QUESTIONS ở root; chỉ sửa links xác minh đúng.
6. Tạo `UI_IMPLEMENTATION_PROGRESS.md` ngắn: phase, task ID, trạng thái, commit khi có, test evidence, blocker, next action. Không nhân bản đặc tả 6 UI.

## 9. Quy tắc tác nghiệp Codex

1. Luôn đọc `AGENTS.md` (root và thư mục con), xác nhận branch `dev`, HEAD, git status trước khi sửa.
2. Nếu working tree đã dirty bởi thay đổi khác, không overwrite hoặc reset; giải thích conflict.
3. Mỗi phase: plan file changes → implement minimal diff → test → ghi kết quả vào `UI_IMPLEMENTATION_PROGRESS.md` → **tự động tiếp tục phase tiếp theo**, không chờ PO nghiệm thu trung gian. Nếu test hỏng: tự sửa và chạy lại trước khi tiếp tục; nếu không thể an toàn hoàn tất, đánh dấu blocker thật và tiếp tục task độc lập. Chỉ báo cáo tổng kết khi đã xử lý các phase đến mức tối đa có thể. PO không cho phép thao tác git tự động.
4. Không commit/push/merge; không cài dependency mới nếu không cần.
5. Không thay `main`, không thay server contracts/DB schema/renderer ngoài phase có thiết kế contract và tests tương ứng.
6. Nếu phát hiện yêu cầu mâu thuẫn với PRD/SRS/ADR, cần breaking migration hoặc đụng dữ liệu người dùng, ghi blocker để xin xác nhận **khi kết thúc lượt thực hiện**; tiếp tục phần an toàn độc lập. Không bỏ qua blocker hay tự tuyên bố pass.
7. Kết quả luôn phân biệt **Đã code / Đã test / Chưa test / Blocked / Đang đề xuất**.

## 10. Cách chạy một lượt xuyên suốt

- Không dừng ở R1.A: tiến hành tất cả các phase khả thi trong cùng workflow Codex.
- Không thay thế code/test bằng tài liệu hoặc UI placeholder. Mỗi control xuất hiện phải có backend/domain behavior thật, hoặc phải nêu rõ phạm vi chưa hỗ trợ.
- Mỗi phase có checkpoint **nội bộ** (tests + progress log), không cần approval giữa phase.
- Không che dấu failing tests hoặc bỏ task khó; `Blocked` chỉ khi có lý do kiểm chứng và giới hạn an toàn cụ thể.
- Khi hoàn thành tất cả phần có thể thực hiện, cung cấp một báo cáo kết thúc tổng hợp, phân biệt Passed/Failed/Blocked/Not Run và các phần cần PO cấp quyền riêng (đặc biệt cloud).

## 11. Definition of Done toàn bộ redesign

Toàn bộ UI redesign chỉ được xem là hoàn tất khi:
- Cả sáu màn hình đúng thiết kế đã chốt, CTA và controls có tác dụng thật.
- R0 lease, snapshot/revision, dirty/manual save, renderer fidelity, Drive consent, local source pins không hồi quy.
- R4.B và R5.B được hoàn thiện hoặc có *scope change* được PO phê duyệt rõ (không tự bỏ).
- Acceptance matrix và browser/backend/cloud evidence đủ các mục áp dụng.
- PO xem screenshot/demonstration và phê duyệt cuối.
- Không tự nhận “hoàn thành” chỉ từ commit hoặc build xanh.

---
**Ghi chú:** Các số đo/kích thước/default được đề xuất để Codex thực hiện và kiểm thử, không phải claim kết quả thực tế. Các API/field cụ thể phải được xác minh lại từ HEAD trước khi sửa code.
