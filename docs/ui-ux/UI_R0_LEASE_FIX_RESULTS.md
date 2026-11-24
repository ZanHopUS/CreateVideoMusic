# R0 — Editor Lease / Read-only: implementation và regression

**Ngày:** 24/11/2026 (Asia/Saigon) · **Nhánh:** `dev` · **Trạng thái:** đã triển khai, kiểm bổ sung; **PO Accepted — R0 Editor Lease / Read-only**, xác nhận ngày 24/11/2026 (Asia/Saigon).

Phạm vi này được PO cho phép riêng cho R0 lease. Không triển khai Dashboard/Editor redesign, không thay backend, project schema, renderer, Drive, lease TTL hoặc optimistic concurrency. UI-01 vẫn Proposed; UI-02 nguyên văn vẫn Approved for Design — Not Implemented.

<a id="po-acceptance-r0"></a>

## PO acceptance — R0 Editor Lease / Read-only

**Quyết định:** Product Owner xác nhận nghiệm thu R0 ngày **24/11/2026 (Asia/Saigon)** trong hội thoại, qua trả lời **“xác nhận”** cho đề nghị “Bạn xác nhận nghiệm thu R0, tôi sẽ cập nhật bản ghi đó rồi tiếp tục xây dựng tài liệu Design System v1.0, không sửa code giao diện”. Đây là quyết định của PO, không phải agent tự chuyển Passed từ số tests hoặc việc push.

**Đối tượng nghiệm thu:** bản sửa R0 Editor Lease/read-only tại commit `d12015a` trên `dev`, cùng evidence trong báo cáo này: unit36/integration47, browser chính27/28 với failure cũ giữ nguyên, C06 retest2/2 và regression hiện hữu6/6. PO acceptance không sửa lịch sử failure thành28/28 pass.

**Giới hạn bảo toàn:** chưa benchmark latency reconnect dài hạn/SLO12s; native OS picker chưa kiểm lại; không nghiệm thu toàn bộ R0 wireframe/contracts, UI-01/02 redesign, cloud quality hoặc các gate phát hành còn mở. R0 lease acceptance mở điều kiện đọc/soạn Design System; **chưa cho phép code R1**, commit/push/merge trong nhiệm vụ tài liệu mới.

Các đoạn “sẵn sàng trình PO” trong phần bàn giao bên dưới được giữ là diễn biến trước xác nhận; bản ghi này là trạng thái hiện hành mới nhất. Bằng chứng test, build ID và phạm vi không đổi.

## Nguyên nhân và giải pháp

| Lỗi đã tái hiện | Giải pháp |
|---|---|
| Claim cũ cùng project ghi đè takeover mới | `EditorLease` có epoch theo mỗi open/acquire/loss; response chỉ được commit khi đúng controller và epoch. Takeover vô hiệu hóa claim/heartbeat cũ ngay từ đầu. |
| Heartbeat dừng sau trạng thái sai | Một timer 5s do controller sở hữu; request renewal không chồng nhau. Writable chỉ lấy từ lease còn hạn. Cleanup hủy requests/timer; callback cũ không cập nhật state. |
| Takeover failure bị nuốt | Bỏ empty catch ở nút; controller hiển thị lỗi takeover/reload, denial và hướng retry. `ApiError` giữ HTTP status/code để phân biệt 401/409. |
| GET project sau takeover thất bại nhưng writable | Claim → GET latest → confirm claim → adopt record/history/revision → writable. Bất kỳ bước lỗi/denial đều giữ read-only; không thay bản nháp bằng dữ liệu tải lỗi. |
| Heartbeat/network/expiry không phản ánh backend | Lỗi khóa ghi ngay; timeout request 8s, deadline tính từ lúc gửi claim (bảo thủ hơn lúc nhận). Focus/visibility và mọi mutation kiểm deadline. Reconnect chỉ tiếp tục nếu claim hợp lệ và revision trên server khớp record; revision khác giữ bản nháp/read-only và yêu cầu explicit takeover/reload. |

Working-save queue kiểm authority trước khi gửi và sau khi nhận. Callback save/render/upload/open/reload/job/media cũng được giới hạn theo identity controller và epoch hoặc vòng đời request thích hợp. Không retry draft cũ với revision mới. Khi 409/401, không tự takeover hoặc đổi expected revision để ghi đè.

Manual Save vẫn chụp B, chỉ cập nhật `manualSavedHash` từ kết quả B và so sánh với nội dung hiện tại; sửa C trong lúc save pending không bị adopt ngược về B. History pins tiếp tục được gửi bởi controller khi heartbeat và `prepareBackup` checkpoint.

Release dùng `pagehide` thay cho `beforeunload` để hủy thao tác đóng tab không vô tình nhả quyền; controller dispose vẫn release. Khi A→B→A, acquire chờ DELETE A cũ hoàn tất, tránh DELETE trễ xóa lease vừa nhận lại. Release không xác nhận được giữ chế độ an toàn; có thể cần tải lại Studio, TTL backend vẫn phục hồi abandoned lease. Không bỏ release/TTL.

## File thuộc bản sửa

- `apps/web/lib/editor-lease.ts`: controller quyền, epoch, renewal, expiry/recovery, release/cleanup.
- `apps/web/hooks/use-studio.ts`: tích hợp authority, scope async callbacks và working/manual save.
- `apps/web/lib/api.ts`: giữ status/code ở client; wire contract không đổi.
- `apps/web/components/studio.tsx`: takeover action hiển thị lỗi qua controller, khóa nút khi thao tác pending; không redesign.
- `tests/unit/editor-lease.test.ts`: regression đảo thứ tự, takeover liên tiếp, reload failure, reconnect/revision, A→B→A/dispose, 401/409, TTL, release ordering và heartbeat overlap.
- `scripts/verify_editor_lease.mjs`: browser assertions cho hành vi đã sửa, khác harness diagnosis giữ nguyên kỳ vọng lỗi trước sửa.
- `scripts/diagnose_editor_lease_server.py`: thêm khả năng chép module application mới chưa commit và Next dev + fixture grants. Không can thiệp lease/API/TTL.
- Báo cáo này, liên kết trạng thái trong Diagnosis/Gap Analysis/Redesign Plan. Các thay đổi D-01…D-06 và diagnosis có từ trước được giữ lại, không gộp thành implementation redesign.

## Evidence và cách tái lập

Evidence trước sửa giữ nguyên tại `.local/evidence/ui-r0/1795493626938273700` và `1795494189506477200`; xem [Diagnosis](UI_R0_LEASE_DIAGNOSIS.md). Lượt thứ hai chứng minh race 3/3 production + 3/3 development, có barrier và quan sát thêm 6s.

Lượt sửa trung gian `1795495297361567000`: production 9/9 observations đúng kỳ vọng mới; development có ba probe failures với timeout 5s. Lượt `1795495624425471800` bổ sung rapid takeover/save B–C; có failure của harness development. Không coi các lượt này là full acceptance của mã cuối. Đã sửa cấu hình timeout của harness bằng **instance trả về từ `expect.configure`**; lời gọi bỏ giá trị trả về trước đó không thay default timeout. Không sửa/giảm assertion tests cũ.

Lượt nguồn cuối: `.local/evidence/ui-r0/1795495998003591400`, build ID `Zit4D2_vD88R__-FF935T`: **28 executions, 27 passed, 1 failed, 0 page errors**. Production 13/13; copied launcher development 12/13; Next dev + native grant fixture 2/2. 52 application/domain/backend files khớp source inventory, không thay đổi sau build; network artifact không chứa bearer token. Có `source-and-trace-check.json` kiểm chứng các số liệu này.

Failure duy nhất là C06 development: UI khóa ghi và expired PATCH409 đã được xác minh, nhưng chưa enabled lại trong chờ reconnect **12s**. Trace có claim sau mở mạng được backend xử lý 200 (web log: 3,2s), trong khi browser chưa ghi nhận response trước timeout assertion. Không có GET recovery/revision response trong trace browser để kết luận recovery hoàn tất; không coi 200 backend đơn lẻ là pass UI.

12s chưa bao trùm trường hợp request cũ cần hết timeout 8s, đợi tick 5s, rồi claim/GET; harness mới chờ tối đa 35s và ghi thời gian reconnect/screenshot riêng. Đây là thay giới hạn kiểm thử do harness mới tự đặt, không đổi timeout ứng dụng, TTL hay tests cũ. Lượt kiểm lại đã thực thi sau khi phiên duyệt hoạt động trở lại: **2/2 passed**, production phục hồi trong **1.494ms**, development trong **5.305ms**, 0 page errors. Cả hai trace có POST renewal 200/canWrite=true và GET project 200/revision sau mốc `network-restored`; screenshot chứng minh UI writable. Không sửa application code giữa lượt chính và retest. Failure 12s ban đầu vẫn giữ nguyên; retest không chứng minh chắc chắn nguyên nhân của riêng failure đó chỉ là timeout và không tạo cam kết latency 12s.

Artifacts bổ sung: `r0-reconnect-retest-results.json`, `r0-reconnect-retest-network.json`, `r0-reconnect-retest-harness/` và `{production,development}/r0-reconnect-retest-expiry-recovered.png` trong cùng evidence run. `source-and-trace-check.json` đối chiếu đầy đủ lượt chính/retest/regression và source hashes.

Ở lần bàn giao trước, lệnh retest bị automatic approval review từ chối trước execution vì access token không refresh được sau logout/đổi tài khoản. Sau lệnh tiếp tục của PO, cơ chế duyệt đã cho thực thi; không chạy lách approval. Retest C06 và regression hiện hữu nay đã hoàn tất.

Regression hiện hữu có một lần startup lỗi `ModuleNotFoundError: tests` do API cwd của config tạm `.local` chưa đặt root. Chưa test ứng dụng nào chạy ở lần đó; giữ `existing-regression/startup-error-results.json`. Đặt `servers[0].cwd = root` trong config tạm rồi chạy lại, **6/6 passed**, không sửa tests cũ hoặc application code. Kết quả cuối ở `existing-regression/results.json`. Mỗi run dùng source copy và private workspace, junction dependencies có sẵn; fresh `next build` riêng. Production dùng `next start`, development chạy copied launcher thật và có ca restart; bổ sung Next dev + fixture API để kiểm Manual Save vì launcher thật không có native folder grant tự động.

Folder grant thử chỉ thay OS picker; lease, GET/PATCH/save/revision/hash/database là backend thật. Fault injection được ghi nhãn: giữ response denial thật, takeover 503, GET abort, heartbeat/working-save abort. Không giả canWrite, không rút TTL 30s, không sửa đồng hồ backend. Native folder picker không được xác minh trong lượt này.

Network artifact chỉ chứa path/method/status/revision/canWrite và editor hash. Không lưu bearer token, credentials hoặc media cá nhân. Screenshots và raw JSON ở `.local` được Git-ignore, chưa commit/push.

```powershell
# 1. Chuẩn bị source copy bằng diagnose_editor_lease_server.py --prepare.
# 2. Junction dependencies và next build trong copy; ghi build/source provenance.
# 3. Chạy với đường dẫn prepared run (bắt buộc fresh build):
node scripts/verify_editor_lease.mjs <prepared-run>
```

## Kết quả kiểm thử

- Unit: **36 passed** (26 existing + 10 lease regressions).
- Integration local API/MVP: **47 passed**, gồm stale writer, lease expiry, queued save sau takeover, revision/hash và save B/edit C. Có Starlette/httpx deprecation warning và cảnh báo archive duplicate name được test chủ động tạo.
- Typecheck root + frontend, Prettier format, Node syntax, Ruff supervisor: đã qua.
- Fresh isolated production `next build`: **passed**; build ID và hashes ở trên.
- Browser R0 source cuối: lượt chính **27/28 passed**; riêng C06 kiểm lại **2/2 passed** như mô tả, failure 12s cũ giữ nguyên. Manual Save/clip property/Undo/Redo và B→C dirty qua production + Next dev grant fixture. Restart launcher qua copied launcher thật.
- Bộ regression browser hiện hữu: **6/6 passed** — lyrics/review/styles/recovery/package, library/template instance, labelled AI transport review, hai tab/takeover, Drive local OAuth cancel/config và session exact-origin protection. Giữ nguyên tests cũ; không coi transport fixture là kiểm chất lượng AI hoặc cloud Drive thực.
- Retest C06 với bound 35s: **2/2 passed**, phục hồi đo được production 1,494s / development 5,305s; TTL vẫn 30s thật. Không thay timeout ứng dụng hoặc backend guard.

## Giới hạn và điều kiện nghiệm thu

Native OS picker, render fidelity/long-run/AI quality, Drive cloud transfer và redesign layout không chạy lại vì không bị thay đổi trong R0. No-page-scroll/always-visible vẫn là lỗi baseline của redesign; không lấy lease fix làm pass UI-ED-01/02 hoặc toàn bộ R0–R6.

Session launcher restart vẫn phải bootstrap phiên mới; 401 không tự bỏ xác thực. Không có merge tự động cho draft khác revision; draft được giữ trong bộ nhớ cho tới khi người dùng xác nhận nạp lại, không cam kết thêm cơ chế lưu draft xuyên crash.

**Kết luận hiện tại: đã đủ evidence chức năng để trình PO nghiệm thu riêng bản sửa R0 lease.** Toàn bộ nhóm checklist có browser/backend evidence; các kiểm bổ sung và 6 regression hiện hữu đã qua trên nguồn/build cuối. Không ghi thành 28/28 pass của lượt chính, không tự xóa failure hoặc coi failure cũ chắc chắn đã được chẩn đoán tận gốc. Rủi ro còn lại là độ ổn định/latency reconnect trên development khi máy chậm; chưa có SLO 12s được phê duyệt hoặc benchmark dài hạn. Native picker chưa kiểm lại; không tuyên bố nghiệm thu toàn bộ R0 wireframe/contracts hay UI redesign. Quyết định PO Passed vẫn thuộc PO. Tại thời điểm chốt evidence, mã chưa commit/push/merge và vẫn trên `dev`. Sau đó PO yêu cầu push và chạy thử; trạng thái Git/URL được báo trong phiên bàn giao.

Lệnh đã chạy trong lượt tiếp tục (ghi report riêng, giữ nguyên failure chính):

```powershell
$env:AMVS_R0_CASE_FILTER='C06'
$env:AMVS_R0_MODES='production,development'
$env:AMVS_R0_REPORT_NAME='r0-reconnect-retest'
node scripts/verify_editor_lease.mjs .local/evidence/ui-r0/1795495998003591400
Remove-Item Env:AMVS_R0_CASE_FILTER, Env:AMVS_R0_MODES, Env:AMVS_R0_REPORT_NAME
# Các specs hiện hữu đã chạy bằng config isolated, có API cwd đặt root:
npx playwright test -c .local/playwright-r0.config.ts core-workflows.spec.ts drive-settings.spec.ts --grep-invert 'S6 measures'
```

Config `.local/playwright-r0.config.ts` và build/artifacts ở trên chỉ có trên máy hiện tại; không tuyên bố đã được push. Commit message đề xuất khi được PO cho phép: `fix(editor): fence lease requests and recover read-only state`.

## Ma trận checklist PO → evidence

Bảng này xác định nơi kiểm, kết quả cuối phải lấy từ JSON của lượt nghiệm thu, không suy pass từ việc có test.

| Checklist | Browser / integration tương ứng |
|---|---|
| 1. Một tab chỉnh bình thường | C01; tạo project, claim, edit và working-save backend thật |
| 2. Hai tab cùng project | C02; B readonly trước takeover |
| 3. Takeover thành công | C02; B enabled sau load/confirm, A chuyển readonly |
| 4. Claim cũ sau takeover | C03 ×3 mỗi production/development; denial thật bị giữ rồi giao sau confirm, kiểm sau thêm 6s |
| 5. Claim/takeover liên tiếp | C09 ×5 lượt đổi owner mỗi mode; unit deferred responses cho nhiều acquire và A→B→A |
| 6. Reload thất bại | C05; giữ readonly/stale draft, hiển thị lỗi, retry tải đúng tên/revision mới |
| 7. Heartbeat/expiry/recovery | C06, TTL 30s thật; C12 khôi phục gặp revision mới không replay draft; unit suspended-clock và conflict |
| 8. Đóng owner, mở lại | C11 fresh tab reopen; C07 lost release + đợi 32s thật |
| 9. Restart launcher | C08 copied launcher thật, content hash giữ nguyên, session cũ 401 |
| 10. Thuộc tính/Undo/Redo/Save sau takeover | C02; rename, caption edit, undo/redo và save endpoint thật. Save ở production + Next dev fixture grants; native picker launcher không tự động hóa |
| 11. Save B rồi edit C giữ dirty | C10 production + Next dev fixture; hold response save B thật, sửa C, nhận response B, kiểm UI dirty/server C/manualSavedHash B |
| 12. Backend stale writer không overwrite | C02/C03/C09 PATCH409; 47 integration tests bao gồm queued manual save rechecks ownership và revision/hash |
