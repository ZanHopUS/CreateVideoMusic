# MVP Implementation Plan

Ngày: **23/11/2026**. Status: **Approved for S0 → S1**, theo “duyệt theo đề xuất”.

Cập nhật: user yêu cầu “triển khai” sau kế hoạch tiếp theo, cho phép bắt đầu S2;
[task nhiều media đầu tiên](S2_MEDIA_EDITOR_RESULTS.md) có evidence, các phần S2
khác vẫn tiếp tục theo acceptance dưới đây. Không tự nâng gate release.
[ADR](../decisions/ADR-0001-LOCAL_MVP_ARCHITECTURE.md), [contracts](../architecture/MVP_CONTRACTS.md)
và conditional entry đã được duyệt; application implementation đã bắt đầu.
[Trạng thái thực tế](MVP_IMPLEMENTATION_STATUS.md) tách khỏi kế hoạch dưới đây;
bảng FR là baseline planning, không tự đánh RTM Verified. S0–S6 là thứ tự delivery,
không phải cam kết ngày hoặc bỏ tính năng Core.

Cập nhật **24/11/2026**: người dùng yêu cầu tự lập kế hoạch và triển khai toàn bộ
hạng mục tới S6. Phạm vi kỹ thuật S2–S6 đã được giao; không suy thành quyền
commit/push/release hay phê duyệt các quality gates. [Kế hoạch thực thi](S2_S6_EXECUTION.md)
và [kết quả hiện tại](S2_S6_RESULTS.md) là nguồn tiến độ; bảng mapping cuối tài liệu
vẫn là baseline planning, không phải trạng thái implementation mới nhất.

## S0 — Foundation và smoke, trước feature work

Tạo layout ADR, launcher local, exact lockfiles; Next/TS/Tailwind, Python API/env,
SQLite migration, shared schemas/composition. Thiết lập tests/check commands thực
trong repo sau bootstrap, không ghi `npm test` như lệnh đã tồn tại ở bước tài liệu.

Acceptance: clean setup Windows, UI→API có session/origin checks; native picker
chọn/cancel folder Unicode; schema/hash parity TS/Python; một shared scene preview
và MP4 thật qua child supervisor; SQLite read/write/migration. Lưu versions/licenses
và evidence. Fail boundary/security/smoke: dừng feature phụ thuộc, sửa ADR nếu cần.

Tests: Vitest cho domain/components, pytest cho API/storage, Playwright cho E2E;
version/tool install chỉ ở S0 sau duyệt. Không đặt coverage % giả; yêu cầu positive,
negative và race/fault coverage cho các invariants có nguy cơ mất dữ liệu.

## S1 — TPL-01 dùng được từ đầu đến cuối

Dashboard chọn mẫu → nhập ảnh/nhạc → caption → editable draft → trim/volume/text
→ preview → manual save → đóng/mở → MP4 thật 720p30 dọc. Có dirty warning, basic
job progress/cancel/retry; các preset chưa triển khai không giả hiển thị dùng được.

Acceptance: project giữ layer, sửa caption/trim hiện đúng ở preview và output;
save/reopen giữ content/view hợp lệ, edit trong lúc save/render không đổi snapshot
đã chốt. Không mock output hoặc thao tác chỉ lưu vào browser memory. Kiểm E2E-01,
E2E-23/24 và E2E-30/31 cho slice này. Đây là bản nội bộ đầu tiên, **chưa là Core**.

## S2 — Editor và đủ ba template

Thêm nhiều ảnh/video và TPL-02 Music Card/TPL-03 lyrics nền; multi-track/playhead,
drag/trim/duration/reorder, command Undo/Redo, crop/fit/blur/brightness cơ bản,
fade/slide/scale, fonts Việt/colors/stroke/shadow. Cùng scene/time mapping cho
Player/render, lyrics thủ công/import draft có thể dùng trước khi tích hợp AI.

Acceptance: E2E-02/16/21 và IT-14/17/19/20/22; 12/100 items là fixtures, không cap
tracks. Preview FPS và interaction P95 đo ở UI thật, không dùng model timings làm
UI latency. VFR/trim/rate/z-order regression gồm các mốc từng fail trong PoC.

## S3 — Lyrics AI local thật và review

Hai nhánh có lời (text/LRC/SRT) và audio-only; parse/report line errors, ASR local,
alignment draft/fallback câu, sửa text/timing và duyệt trước dùng. Job cancellation,
missing model/error/offline không làm mất edit. Tiếng Việt ưu tiên trước; Anh vẫn
phải có integration và evidence trước nghiệm thu cam kết, không âm thầm bỏ scope.

Acceptance: AI-01/02/03, IT-09, UT-10, IT-33/34, SEC-35. Review độc lập timing/lỗi,
correction time và corpus bổ sung theo POC_PLAN; instrumental/rap/remix/sped-up/
slowed/multiple voices phải có cases và giới hạn rõ. Không lấy ASR làm gold hoặc
gọi raw confidence là calibrated. Không đủ quality → chưa release FR liên quan,
không đổi thành manual-only Core. Cloud adapter off, chưa cài/gọi provider API.

## S4 — Độ bền dữ liệu và hoàn thiện jobs/export

Recovery riêng, grant folders/relink, portable snapshots, shared asset pins/GC,
disk/temp preflight, queue/restart/interrupted, cancel ở prepare/run/finalize/
validate, publish-last output. Bổ sung tất cả 12 preset combinations; 3 templates
thành matrix 36, không bỏ 60FPS/ratio để né failure.

Acceptance: IT-26/28/32, fault thực/disposable và E2E lifecycle. Save race B/C,
checksum/missing-media, locked file, quota/crash, package restore folder khác,
traversal/junction và capability forgery. ENOSPC injection ghi rõ khác disk thật.
S0 có nền permissions; audit Origin/Host/session, TOCTOU và subprocess ownership
ở đây phải bao phủ luồng ứng dụng, không lấy PoC guard làm chứng minh đủ.

## S5 — Library, template reuse, suggestions và Drive workflow

Media metadata/thumbnail/search; clone project thành template typed slots,
instances không sửa template gốc. Local metadata/tags + heuristics gợi ý nhạc/
đoạn, nghe thử và trim tay; không quảng cáo energy là nhận biết “đoạn hay”.
Portable Drive workflow chỉ thao tác closed snapshots, không sync live DB/temp.

Acceptance: IT-04/06/13/27/29. POC-07 đánh 6 tracks có quyền, ≥2 đoạn khi có thể,
target useful ≥4/6 theo kế hoạch; thiếu cấu trúc phải báo thay vì bịa suggestions.
Drive cần folder/account user cho phép, ≥2 sync-download-restore hash khớp và
pause/offline/conflict/quota cases. Chưa có account/test → giữ FR-407 mở, không
gọi local copy là cloud verified hoặc tự bỏ Core workflow.

## S6 — Core acceptance và release review

Chạy E2E ba mẫu, full preset matrix, 300s/1080p60, offline sau setup, UI/performance,
lyrics/timing/font/listening, crash/recovery/missing-media/quota/cancel. Finalist
repetitions theo POC_PLAN khi tài nguyên phù hợp; không khởi heavy job nếu admission
chưa đủ. Ghi sampling/RTF/disk/temp/CPU và không suy guarantees từ một lượt.

Acceptance: toàn bộ Core FR/AC có evidence, không blocker/critical, cài đặt/khôi
phục hướng dẫn thực, không phí bắt buộc. ACC-01 release thresholds được PO chốt
từ measurements. G2 còn thiếu phải được review/đóng tương ứng; không tự coi approval
khởi công là release waiver. Chỉ cập nhật RTM Implementation/Verification khi có
application commit/tests thực. Release/PR dev→main chỉ sau user yêu cầu.

## Traceability — primary delivery cho đủ 38 FR

Mỗi FR có một primary milestone; validation có thể bắt đầu sớm và tiếp tục S6.
AC/test IDs chuẩn lấy từ SRS/RTM, không tạo catalogue đánh Verified song song.

| Milestone | Requirement IDs | Trạng thái hiện tại |
|---|---|---|
| S1 | FR-101, FR-102, FR-104, FR-106, FR-401, FR-402, FR-403, FR-408, FR-409 | Not implemented |
| S2 | FR-103, FR-109, FR-207, FR-301, FR-302, FR-304, FR-305, FR-306, FR-307 | Not implemented; phần advanced C/M giữ cho Complete |
| S3 | FR-201, FR-202, FR-203, FR-204, FR-205, FR-501, FR-502, FR-503 | Not implemented; cloud interface/off, adapters nhiều provider ở Complete |
| S4 | FR-404, FR-406, FR-410 | Not implemented |
| S5 | FR-105, FR-107, FR-206, FR-405, FR-407 | Not implemented |
| Complete | FR-108, FR-208, FR-303 | Not implemented; blank builder, AI style, timeline advanced giữ nguyên |
| Later | FR-504 | Deferred; Vercel không thuộc local Core |

NFR-01/02/08 đo ở S2–S6; NFR-03/06/12 ở composition/export; NFR-04/05 UI thật;
NFR-07 S3 corpus/gold; NFR-09/14 S4–S5; NFR-10/11 offline/security ở S0 và S6;
NFR-13 dependency/license/mandatory cost review S0/S6. BR-01–13 là invariants,
đặc biệt BR-05/06 thời gian, BR-07/08/09 dữ liệu và BR-11/12/13 privacy/permissions.

## Quy tắc delivery

Chỉ `dev`; mỗi task đọc requirements + ADR, thay đổi nhỏ có test thực phù hợp.
Không tự thêm mock/dependency/refactor ngoài scope. Báo feature/evidence và rủi ro
còn lại sau mỗi milestone; commit/push cần user cho phép riêng. Không đưa media,
lyrics có bản quyền, models, secrets hoặc raw private evidence vào Git.
