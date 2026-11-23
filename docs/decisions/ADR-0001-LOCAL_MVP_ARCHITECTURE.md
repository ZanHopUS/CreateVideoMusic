# ADR-0001 — Local MVP Architecture

Date: **23/11/2026**. Status: **Accepted**.
Owner: Product Owner. Approval date: **23/11/2026 (Asia/Saigon)** qua xác nhận
“duyệt theo đề xuất”, gồm ADR/contracts, conditional entry và S0 → S1. Scope: MVP Core local, Windows 11,
RAM 16 GB, một người dùng, cá nhân phi thương mại; không đổi A–G.

## Context

[PoC exit review](../technical-discovery/POC_EXIT_REVIEW.md) cho thấy render,
snapshot/state và SQLite khả thi trong fixtures; lyrics quality, VFR policy,
permissions và release verification còn mở. Đề xuất bắt đầu có điều kiện sau
duyệt ADR này và [contracts](../architecture/MVP_CONTRACTS.md), không công nhận
toàn bộ G2 Passed. SRS mục 8 yêu cầu chốt các blockers trước viết code.

## Accepted decision

| Boundary | Lựa chọn và trách nhiệm |
|---|---|
| UI | Next.js App Router, TypeScript strict, Tailwind; tiếng Việt, desktop/dark. Không truy cập filesystem/DB trực tiếp |
| Shared domain | JSON Schema versioned cho project/template/job; TS types và Python validation theo cùng schema, golden fixtures kiểm parity |
| Preview/render | Shared React/Remotion scene và time adapter, Player cho preview; Node subprocess render MP4 + FFmpeg finalization khi đã kiểm chứng |
| Local service | Python 3.12 + FastAPI/Uvicorn, một API process; sqlite3 stdlib, media/catalog, capabilities và job supervision |
| AI | Python subprocess/env riêng cho faster-whisper/alignment; không load model trong mỗi API worker. Adapter local là default |
| Storage | SQLite working state/job/catalog; manual JSON checkpoint độc lập; recovery riêng; managed immutable media + portable ZIP snapshot |
| Jobs | Một heavy job AI/render đang chạy; queue persistent, UI vẫn edit được. Snapshot bất biến, owner PID tree, publish output sau validation |
| Launcher | Một lệnh PowerShell khởi UI/API, tạo session và mở local browser; không Docker, cloud, Redis hoặc login bắt buộc |

Runtime hiện có trong PoC không tự chứng minh stack ứng dụng tương thích. S0 pin
exact versions qua lockfiles sau smoke; không dùng `latest` trong hướng dẫn tái
lập. Next/React/Remotion phải được thử cùng nhau, không copy mọi dependency PoC.
App/AI env tách để tránh xung đột alignment. Không cài gì trong ADR step.

## Intended source organization

```text
apps/web/                  Next UI, same-origin API proxy
services/local-api/        FastAPI, SQLite repository, file permissions, supervisor
workers/ai/                ASR/alignment entrypoints, isolated envs
workers/render/            Node renderer, fixed argv/JSON job input
packages/domain/           schema, generated types, migration fixtures
packages/composition/      shared Player/render scenes and time mapping
tests/{unit,integration,e2e}/
scripts/                   Windows launcher and environment checks
poc/                       historical experiments, not production imports
```

Đây là layout đề xuất, chưa tạo scaffold. Không di chuyển baseline root hoặc
private `.poc/`. Refactor PoC vào module ứng dụng chỉ sau kiểm tra/viết test phù hợp.

## Local permissions and service boundary

- Bind UI/API vào `127.0.0.1`; launcher chọn ports còn trống, không fallback ra LAN.
  Browser gọi một origin UI; proxy tới API cố định, không forward URL tùy ý.
- Session token ngẫu nhiên đưa qua URL fragment một lần rồi xóa khỏi location,
  giữ trong memory; chuyển bằng header. Không token query/log/localStorage. API và
  proxy kiểm token, exact Origin/Host, không wildcard CORS hoặc tin loopback là auth.
  Chi tiết triển khai: authenticated session bootstrap cấp thêm cookie session
  HttpOnly/SameSite=Strict chỉ để đọc asset/output bằng native image/audio/video
  elements (không gắn được bearer header). API ghi vẫn bắt buộc header; cookie
  không có Max-Age, không lưu vào project và không cấp quyền ghi.
- Folder picker chạy local fixed-script subprocess qua `tkinter.filedialog`;
  S0 phải kiểm availability/cancel/Unicode. Kết quả do backend giữ và trả opaque
  capability (scope project/export/backup, revoke khi hết session). Browser không
  gửi path để được cấp quyền. Nếu picker không hoạt động, báo ADR delta trước đổi.
- Upload do user chọn qua browser; backend stream vào staging, validate type,
  probe codec/duration/limits rồi publish managed copy. Asset API chỉ nhận IDs,
  stream có Range bounds; không endpoint đọc path bất kỳ.
- Resolve/containment tại mọi thao tác, chống archive escape/junction; kiểm soát
  staging ownership và handle/permissions trước publish. TOCTOU còn phải audit,
  không dùng riêng `resolve()` làm chứng minh bảo mật đầy đủ.

## State, media and jobs

Contracts chốt ticks **48,000/s**, interval half-open, ordered tracks/items; một
source of truth cho preview/export. SQLite là authoritative working persistence;
manualSavedHash độc lập với autosave/recovery. Backend optimistic revisions chặn
stale writes; frontend history transaction theo một thao tác người dùng.

Managed library giữ source copy immutable/content hash; delete project chỉ bỏ
refs. GC phải tính project/manual/recovery/template/job pins và có consent.
Manual checkpoint gồm state + inventory, cần library local để mở; portable ZIP
chứa đủ asset bytes khi chuyển máy. Không đóng gói live SQLite hoặc model/cache.

AI/render dùng chung một heavy-job slot, không chạy inference trên request loop.
Default render concurrency 1; benchmark rồi mới tăng. Admission ≥4 GiB/10 samples
là candidate setting cho máy thử, không thay R0 ≥2 GiB hoặc requirement RAM 16 GB.
Cancel phải dọn owned children; crash/restart ghi interrupted và yêu cầu retry,
không coi partial MP4 là output thành công.

ASR medium là ứng viên Việt, small là cấu hình nhẹ để benchmark; không gán chất
lượng mặc định đã duyệt. Hai luồng lời sẵn/audio-only đều có review; import SRT có
cue windows khác text-only toàn bài. Low confidence không tạo word timing giả.
Cloud adapters chỉ interface/disabled trong Core local hiện tại, opt-in mới mới bật.

## Alternatives and consequences

- Node-only backend giảm một service nhưng cần quyết định/kiểm Node SQLite driver
  và vẫn cần Python AI. Chọn Python coordinator để tái dùng sqlite3 đã có evidence.
- FFmpeg-only composition khó chia sẻ React preview; Remotion dùng chung scene,
  vẫn cần xử lý VFR và memory. Seek-nudge là candidate, không bật toàn cục khi chưa
  có regression; normalized proxy phải đo lại, không coi CFR tự chữa mọi lỗi.
- Python API + Node UI/render tăng số processes và hai hệ type/validation; chấp
  nhận chi phí này, bù bằng schema parity, supervisor và heavy-job serialization.
- Electron/Tauri và Vercel/local-agent ngoài lựa chọn này; không thêm desktop shell.

## Dependencies, cost and verification

Next installation docs liệt kê Windows và Node tối thiểu 20.9; đó không là bằng
chứng full stack chạy trên máy này. [Next official installation](https://nextjs.org/docs/app/getting-started/installation).
FastAPI ghi rõ nhiều worker process có thể nhân bản memory; đây là lý do chọn API
single process và model child có kiểm soát. [FastAPI process/memory](https://fastapi.tiangolo.com/deployment/concepts/).

Remotion FAQ công bố Free License cho cá nhân; dùng như căn cứ xem xét mục đích
cá nhân đã xác nhận, không gọi Remotion là MIT hoặc suy mọi use case đều miễn phí.
S0 lưu license của phiên bản pinned, model/font/FFmpeg build và kiểm terms áp dụng;
thay đổi mục đích sử dụng phải xem lại. [Remotion FAQ](https://www.remotion.dev/docs/license/faq),
[terms](https://www.remotion.dev/docs/terms). Không có cloud/API cost bắt buộc.

S0 phải chứng minh: clean install/build, UI→API session, native picker, SQLite
migration/save, TS/Python contract parity, một scene Player + MP4 qua subprocess.
Thất bại thay đổi boundary/time/storage/security phải sửa ADR trước tiếp tục.
Chỉ Product Owner chuyển trạng thái Accepted và ghi ngày; commit/push là quyền riêng.
