# Local Storage and Recovery PoC Results

Ngày: **23/11/2026 (Asia/Saigon)**. POC-05 local trên máy Windows 11/RAM 16 GB,
Python stdlib SQLite **3.45.3**; không cài thêm dependency/model hoặc dùng cloud.
Giữ hướng SQLite runtime + portable snapshot đã xác nhận. **Driver ứng dụng,
schema/container/retention trong harness vẫn Proposed**, không phải ADR Accepted.

## Kết luận theo phạm vi

State/storage chức năng đạt các phép thử local: sáu fixtures 12/100 items,
**24 process-crash runs ở 12 ranh giới**, **10 portable round trips**, recovery,
shared/pinned assets, checksum/relink và malformed packages. Lượt lặp trên thư mục
mới với guard hiện tại cũng đạt 32 checks/24 crash cases/10 round trips.

**R0 render bridge chưa đạt trong điều kiện RAM hiện tại**. Hai video restore
đạt chức năng nhưng có available RAM dưới 2 GiB; lượt concurrency 1 bị monitor
dừng. Không kết luận toàn bộ POC-05/Core hoặc máy 16 GB đã được nghiệm thu.
Google Drive sync/restore chưa chạy do scope local; ST-03 còn mở.

## Hợp đồng thử nghiệm

- SQLite WAL/FULL chứa working project JSON, revision/hash và relational asset
  references; không lưu binary media trong DB. Schema này chưa normalize toàn bộ
  timeline hoặc chọn Node/production driver.
- Manual save là checkpoint JSON độc lập: stage → flush/fsync → validate → replace
  trong cùng vùng local. Working DB có thể mới hơn manual; dirty so semantic hash.
- Recovery riêng, chỉ restore vào working khi `confirmed=True`, không ghi đè manual.
  Đây là policy/API check, chưa là hộp thoại xác nhận trong UI.
- Managed library giữ **bản sao** theo content hash. Portable ZIP_STORED chứa
  manifest/project JSON + đúng asset bytes đang tham chiếu, relative paths/hashes.
  Không đóng gói live SQLite/WAL, model, render temp hoặc library không liên quan.
- ZIP/schema/version/budget là cấu hình PoC: ≤16 MiB/entry, ≤64 MiB/archive,
  ≤64 entries, compression ratio ≤200. **Không phải giới hạn media sản phẩm.**

## Fault, restore và pinning

| Phép thử | Bằng chứng thực tế |
|---|---|
| SQLite crashes | begin/update-before-commit/after-commit ×2; reload đúng A/B, integrity_check ok |
| Manual crashes | written/fsynced/before-publish/after-publish ×2; canonical save cũ hoặc mới hợp lệ |
| Package crashes | zip-open/asset/zip-closed/before-publish/after-publish ×2; package cũ nguyên, file mới chỉ hiện khi publish |
| Save khi đang edit | Pause worker sau fsync B, working DB đổi C; manual B, working C, dirty=true |
| Recovery | Không consent bị chặn; có consent cập nhật working, manual/recovery cũ vẫn nguyên |
| SQLite backup API | Bản DB đóng giữ B, working đổi C; không copy live DB file |
| SQLite FULL | PRAGMA max_page_count giới hạn DB disposable, lỗi SQLITE_FULL=13, rollback giữ A |
| File ENOSPC | Hai lỗi quota **injected**, không làm đầy volume thật; manual/package cũ nguyên |
| Windows locked file | CreateFileW deny-sharing thực sự chặn replace; save cũ nguyên, unlock rồi retry đạt |
| Restore | 10 folders Unicode/có khoảng trắng; project semantics và tất cả asset hashes khớp |
| Shared/GC | Gỡ project A giữ asset của B; manual/recovery/template/job pins chặn xóa; chỉ orphan tự tạo được xóa sau confirm |
| Missing/relink | Thiếu asset hoặc bytes relink sai bị chặn; copy đúng hash rồi load được |

Crash worker dùng `os._exit(77)`, không chạy Python cleanup: đây là process crash,
**không phải mất điện**. Không suy atomicity/durability xuyên volume, Drive hoặc
mọi filesystem từ local replace/fsync. GC mới kiểm các reference sets được cấp;
chưa chứng minh retention, concurrent GC/job pins hay crash trong GC production.

## Package validation

**14 malformed cases** bị từ chối trước restore publish: traversal, absolute/drive/
backslash, ADS, reserved Windows name, duplicate/case collision, archive symlink,
asset hash mismatch/missing, format không hỗ trợ, unreferenced member và bomb budget.
Existing destination và path ngoài disposable root cũng bị chặn. Không thấy ghi
escape trong các fixtures; chưa audit Origin/Host/capability service, reparse/junction
thực, long paths >260 hoặc toàn bộ parser/media security của ứng dụng.

Guard MIME cũ nhận binding sai loại; nguồn archive tái hiện 6 lỗi. Guard mới chặn
6/6, vẫn nhận 6 bindings hợp lệ và 10 package positive. Lượt fresh run-02 archive
đã có guard mới nên không tái hiện lỗi cũ; không trộn hai phiên bản bằng chứng.

## So JSON runtime với SQLite

So cùng working-state snapshots, assets được xác minh trước timer. JSON dùng
stage/fsync/replace + load/hash; SQLite transaction + load/hash/reference updates.
Thứ tự backend luân phiên, **5 warm samples/backend/case**, median:

| Fixture | JSON runtime | SQLite runtime |
|---|---:|---:|
| TPL01 12 / 100 items | 13.36 / 17.27ms | 1.15 / 2.01ms |
| TPL02 12 / 100 items | 14.11 / 17.87ms | 1.16 / 2.33ms |
| TPL03 12 / 100 items | 17.15 / 18.54ms | 1.14 / 1.96ms |

Không là SLA, cold/warm chuẩn hoặc bằng chứng query/migration scale. Hai backend
có chi phí/publish semantics khác nhau; chưa thử power loss. Các số manual JSON
save/load khác trong suite gồm hash media, không dùng làm speedup comparison.
Giữ hướng SQLite đã duyệt; chưa chọn schema, ORM hoặc driver ứng dụng bằng bảng này.

## Render từ package restore và R0

TPL02/TPL03 được render lại từ thư mục restore Unicode bằng composition hiện có.
Mỗi MP4 decode đủ **360 frames**, 0 lỗi timestamp, duration 12.000s; PNG ở frames
60/150/300 trước và sau restore **giống pixel**. MP4/PNG min PSNR 36.09/32.33dB,
vượt ngưỡng 30dB của phép kiểm. Đây là hai fixture, chưa E2E toàn bộ styles/fonts.

| Lượt | Peak private | Min available | Trạng thái tài nguyên |
|---|---:|---:|---|
| Storage suite run-01 | 0.025 GiB | 2.847 GiB | Qua R0 sampled trong lượt này |
| Render restore concurrency 2 | 1.050 GiB | **1.850 GiB** | Chức năng đạt; R0 strict không đạt |
| Render restore concurrency 1 | 0.965 GiB | **1.651 GiB** | Dừng sau <2 GiB liên tục 10s, không tính pass |

Concurrency 2 có 16 mẫu RAM thấp rải rác, chưa chạm stop condition 10s liên tục;
điều đó **không** làm R0 strict thành pass. Concurrency 1 bị dừng sau 86.984s và
giữ partial evidence. Initial bridge CLI path error được sửa, không tính quality run.
Lượt storage lặp chức năng vẫn đạt nhưng có min available **1.992 GiB**, nên không
coi là R0 strict pass. Sample 1s có thể bỏ sót peak ngắn, nhất là crash workers ngắn.

Không quy toàn bộ biến động RAM cho SQLite hoặc concurrency khi background load
chưa được kiểm soát. Cần đủ headroom và admission/resource measurement trước thử
render lại; giữ yêu cầu phần cứng theo baseline, không tự tăng yêu cầu máy.
Chưa đo peak temp/disk I/O, UI latency hoặc contention của ứng dụng thực.

## Bằng chứng và bước tiếp

Raw Git-ignored dưới `.poc/state-storage/`:
[summary](../../.poc/state-storage/run-01/summary.json),
[suite run-01](../../.poc/state-storage/run-01/results.json),
[fresh run-02](../../.poc/state-storage/run-02/results.json),
[matched timings](../../.poc/state-storage/run-01/comparison-results.json),
[render validation](../../.poc/state-storage/run-01/render-check/validation.json),
[R0 abort](../../.poc/state-storage/run-01/render-resources-concurrency-1/resources.json).
Nguồn trước/sau guard, input/asset/package hashes và crash evidence được giữ riêng.
[Runbook](../../poc/state-storage/README.md), [state results](STATE_TEMPLATE_POC_RESULTS.md).

Tiếp theo: kiểm resource admission/render khi đủ headroom, schema/migration/reparse
và recovery fault coverage rộng hơn. Drive round-trip cần scope/folder riêng;
local copy chưa là cloud backup verified. Không sửa A–G, không chốt container/driver
hoặc đánh FR-401–407 Verified. Thay đổi hiện trên `dev`, chưa commit/push.
Commit đề xuất: `test(poc): verify state history and local storage recovery`.
