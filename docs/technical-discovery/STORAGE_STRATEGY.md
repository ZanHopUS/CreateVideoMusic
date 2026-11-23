# Storage Strategy — Đề xuất để kiểm chứng

**Cập nhật yêu cầu 23/11/2026:** người dùng chọn Google Drive trên web trực tiếp.
[ADR-0002](../decisions/ADR-0002-DIRECT_GOOGLE_DRIVE.md) thay phương thức Drive
desktop bên dưới bằng adapter OAuth/API tùy chọn. Các phần desktop là lịch sử
discovery; không còn là yêu cầu cài đặt. SQLite/temp vẫn local; cloud chưa nghiệm thu.

Ngày: **22/11/2026 (Asia/Saigon)**. Trạng thái: **định hướng SQLite runtime + portable snapshot đã được xác nhận; chi tiết còn Proposed**; POC-05 **Not run**. Giữ yêu cầu E/F/G: manual save, mở lại đầy đủ state, folder local, recovery riêng, personal library và Drive desktop snapshot.

**Cập nhật xác nhận 22/11/2026:** Product Owner đã xác nhận ST-01–04 theo [OPEN_QUESTIONS.md](../../OPEN_QUESTIONS.md). Định hướng SQLite runtime, package versioned/checksummed/relative paths, backend kiểm quyền folder, immutable snapshot sync và cleanup có xác nhận đã được chấp nhận. Driver/schema/container, copy policy, retention/quota và bằng chứng crash/restore chưa chốt; chưa được phép chạy POC-05.

## 1. Phân biệt runtime, bản lưu và bản đồng bộ

Runtime cache/database phục vụ app, không mặc định là project người dùng đã lưu. Manual save là checkpoint chính thức. Recovery bảo vệ thay đổi chưa lưu, không tự nâng thành manual save. Portable package là bản nhất quán có manifest và assets để chuyển folder/máy; Drive chỉ vận chuyển package, không vận hành live database.

Browser storage/IndexedDB có thể phù hợp cache/UI preferences nhưng không là nguồn duy nhất cho project cần portability và folder do user chọn. Backend local có quyền giới hạn quản lý filesystem; một handle browser không tự cấp quyền path cho Python/FFmpeg. File System Access API cần quyền người dùng và có ràng buộc trình duyệt/context; cần kiểm tra UX trên browser đích. [Chrome File System Access](https://developer.chrome.com/docs/capabilities/web-apis/file-system-access).

## 2. So sánh lựa chọn

| Lựa chọn | Ưu điểm | Rủi ro / công sức | Khi phù hợp |
|---|---|---|---|
| JSON project + assets local | Đơn giản, dễ inspect/version/migrate | Tự bảo đảm atomic save và consistency nhiều file; library/query cần cách khác | Baseline so sánh đơn giản nhất |
| SQLite metadata/runtime + JSON/package snapshot | Transactions/query/references thuận tiện; tách runtime và backup | Native driver/locking/migration; phải snapshot DB và assets cùng revision | Ứng viên chính để thử nếu query/state đáng chi phí |
| SQLite project portable trong package | Backup DB giữ relations | Debug/migration phụ thuộc schema/driver; vẫn phải kèm assets | Chỉ chọn nếu PoC chứng minh thuận lợi hơn JSON manifest |
| Live SQLite trong folder Drive | Ít thao tác export nhìn bề ngoài | Sync sidecars/locks/partial states và conflicts khó bảo toàn | Không đề xuất, trái BR-12 |
| Chỉ browser IndexedDB/OPFS | Không cần backend cho cache | Quota/eviction/permission/export; worker local vẫn cần media access | Cache hoặc prototype riêng, không mặc định authoritative store |

Hướng đã xác nhận là SQLite local runtime + portable snapshot. Đề xuất chi tiết để **thử**: runtime ngoài Drive; manual project snapshot JSON + assets có schemaVersion; dùng JSON-only làm đối chứng độ phức tạp, không tự thay hướng SQLite. DB không giữ binary media lớn nếu không có bằng chứng cần thiết.

SQLite WAL cho phép reader/writer đồng thời nhưng không đồng nghĩa nhiều writer độc lập hay sync-safe. WAL có sidecar và không hoạt động trên network filesystem theo tài liệu; Drive virtual/mirrored filesystem còn phải đo riêng. Backup API hoặc `VACUUM INTO` là cơ chế tạo bản DB nhất quán, không thay cho snapshot toàn bộ DB + assets của ứng dụng. [SQLite WAL](https://sqlite.org/wal.html), [Backup API](https://sqlite.org/backup.html).

## 3. Layout và hợp đồng package dự kiến

Ví dụ logic, chưa tạo các folder này:

```text
<local-workspace>/
  runtime/          # database/job metadata; không sync
  library/          # bản media đã import, immutable theo content hash
  projects/<id>/    # manual snapshots và recovery tách biệt
  cache/            # thumbnail/proxy/waveform, tái tạo được
  jobs/<job-id>/    # render temp và snapshot job
<user-export-folder>/
  <name>.mp4
<user-backup-folder>/
  <project-id>-<revision>-<unique-id>.package
```

`.package` chỉ là tên minh họa; ZIP/directory/custom extension chưa chọn. Package chứa manifest/version, project snapshot, template instance, lyrics đã duyệt, asset inventory với relative path/size/hash/type, và các file media được tham chiếu. Chọn đóng gói fonts khi license cho phép hoặc ghi dependency thiếu; không đánh portable nếu cần font/asset không có khi offline.

Giữ source trim/speed, track order, transforms/effects, template/version, lyrics provenance/timestamps và export preset. Xác định rõ UI state nào cần mở lại để đáp ứng FR-402; đừng chỉ lưu video phẳng. Không chứa API key, absolute private paths, recovery chưa được chọn, cache/model downloads, temp render hoặc toàn bộ personal library không liên quan.

Content-addressed assets giúp deduplicate; hash phát hiện hỏng, **không phải chữ ký xác thực hoặc mã hóa**. Package private vẫn có thể lộ khi đặt trong repo/public Drive. Chính sách encryption chưa chốt, không ngầm coi Drive đáp ứng mọi nhu cầu privacy.

## 4. Luồng manual save và export snapshot đề xuất

1. Chốt revision của project trong transaction/lock thích hợp; pin tập asset được tham chiếu. Media đã import không sửa tại chỗ; thay asset tạo ID/hash mới.
2. Serialize snapshot vào staging cùng local volume với đích manual save; dùng backup API nếu đóng gói DB. Nếu state đổi tiếp thì staging vẫn dùng revision đã chốt, không trộn dữ liệu mới.
3. Copy/link an toàn hoặc đọc assets pinned, xác minh checksum/size; package chuyển máy phải chứa bytes cần thiết, không chỉ absolute paths hoặc hardlink vào library cũ.
4. Validate schema, references và completeness, flush/close file rồi publish bằng replace/rename phù hợp filesystem. Giữ bản save trước nếu bước mới thất bại. Tính atomic/durability và Windows file-lock semantics phải đo; không khẳng định atomic xuyên ổ đĩa.
5. Chỉ đánh dấu manualSavedRevision cho đúng revision đã save. Nếu user sửa tiếp trong lúc save, dirty state vẫn bật. Recovery không xóa trước khi manual save xác nhận thành công.
6. Với backup Drive: tạo package hoàn chỉnh ở local staging trước, copy sang tên tạm trong folder backup, đóng và verify rồi rename thành tên immutable duy nhất. Consumer chỉ nhập file hoàn tất và validate manifest/hash; rename local không bảo đảm Drive đã upload hoặc người nhận đã có đủ bytes.

Crash tại mọi ranh giới phải giữ được bản manual save cũ hoặc mới hợp lệ, không nửa bản. SQLite transaction chỉ bảo vệ DB, không tự bảo vệ nhiều file media; pinning + immutable assets + publish cuối là giả thuyết cần POC-05.

## 5. Recovery, restore và library

- Recovery checkpoint versioned theo project/revision, khác đường dẫn manual save; chu kỳ và quota chờ duyệt ST-04. Khi mở sau crash, hiển thị thời điểm/revision và hỏi chọn restore/discard; restore sang bản làm việc, không overwrite bản manual trước consent.
- Restore package sang staging mới ngoài Drive runtime; validate archive paths, schemaVersion, checksums, asset references và giới hạn giải nén. Từ chối absolute path, `..`, symlink/reparse escape, decompression bomb và version chưa hỗ trợ. Dữ liệu import không được thực thi code/template JS tùy ý.
- Dùng relative paths trong package; runtime resolver map asset ID tới path hợp lệ. Missing/checksum mismatch cho relink theo user, không tự tìm và đụng file ngoài phạm vi quyền. Kiểm tra Unicode, reserved filenames và path length Windows.
- Library import tạo managed copy hoặc explicit reference mode; lựa chọn cuối chờ ST-01. Đề nghị managed copy cho portability. Gỡ khỏi project chỉ bỏ reference; không xóa file gốc hoặc shared assets.
- GC phải xét project/manual/recovery/job/template references và pin snapshot đang đóng gói; preview danh sách và có consent trước xóa. Cache có thể tái tạo, nhưng không dùng cleanup cache để xóa model/source đang dùng.

## 6. Drive desktop và xung đột

Google mô tả streaming chủ yếu giữ file ở cloud, cần đảm bảo offline availability; mirroring giữ copy local và cloud. Cả hai tiêu tốn quota cloud và local theo chế độ, không cung cấp database transaction cho app. [Drive stream/mirror](https://support.google.com/drive/answer/13401938).

Đề xuất runtime trên ổ local thật, backup folder Drive do user chọn. App không thêm Drive API/OAuth hay login bắt buộc; Drive desktop được user cài/đăng nhập riêng. Kết quả tạo package chỉ là **Local package ready**, chưa là **Cloud backup verified**. Nếu không đọc được trạng thái Drive đáng tin, hướng dẫn user kiểm tra sync và thực hiện restore round-trip; không báo “đã backup cloud” từ thao tác file copy.

Tên package gồm project ID/revision/unique ID để giữ cả hai bản khi conflict; không last-write-wins vào một file DB/project. Conflict cùng revision nhưng hash khác phải hiển thị hai ứng viên, import riêng; không tự merge timeline. Streaming offline, account quota đầy, đồng bộ bị pause và file khóa cần lỗi có thể khôi phục. Multi-machine concurrent editing không thuộc Core.

## 7. Tài nguyên, quyền và kiểm chứng

Dung lượng preflight gồm assets cần copy + staging/package + output + temp và safety reserve; tạm đề nghị reserve **max(2 GiB, 10% estimated required bytes)**, phải benchmark trước chốt. Không đoán output size chỉ từ duration; temp frame/cache có thể lớn hơn MP4 nhiều lần. Kiểm tra space trong từng phase, báo lỗi và giữ source/manual save. Không tự cleanup nguồn để vượt quota.

Backend bind loopback, kiểm Origin/Host và quyền thao tác; không lấy CORS làm cơ chế authorization duy nhất. User chọn folder rồi backend cấp opaque capability/asset ID; validate canonical paths sau symlink/reparse resolution, hạn chế extension/MIME/codec và subprocess argv không shell interpolation. Thử traversal và yêu cầu từ origin không được phép trước chốt ST-02. Không cần login app vẫn cần bảo vệ local service.

POC-05 phải kiểm chứng:

| Thử nghiệm | Bằng chứng / Go đề xuất |
|---|---|
| JSON vs SQLite | Cùng state/asset fixture, ghi save/load time, RAM, migration và packaging effort; chọn sau evidence |
| Crash/locked file/disk-full | ≥20 fault runs trên disposable copy; manual save trước còn nguyên, lỗi rõ và retry được |
| Restore folder khác | ≥10 round trips; semantic state + asset hashes khớp, không phụ thuộc absolute path |
| Recovery/GC/shared assets | Không restore overwrite hoặc xóa shared/pinned asset không consent |
| Drive round-trip | ≥2 package sync-download-restore với hash khớp; thử pause/offline/conflict/quota; chưa đủ account thì Not run |
| Malformed package/paths | Từ chối input nguy hiểm, không ghi ra ngoài folder được cấp quyền |

Phần cần duyệt tiếp trong TD-05/ST-01–04: format/package/schema/driver cụ thể, copy policy, cách cấp quyền folder, recovery retention/GC, quota và quyền chạy thử Drive workflow. Định hướng đã được xác nhận ở OPEN_QUESTIONS; tài liệu này không phê duyệt các chi tiết đó.

## 8. Cập nhật thực nghiệm local — 23/11/2026

User đã cho phép local PoC; các ghi chú chưa chạy/chờ quyền thử ở phần planning
trên phải đọc cùng [POC_STATUS.md](POC_STATUS.md). Harness SQLite runtime + manual
JSON + portable ZIP đạt 24 process-crash cases/10 restores, lặp cùng fixtures cũng
đạt; recovery/shared asset/pinning/locked-file và malformed input có evidence local.
[STORAGE_RECOVERY_POC_RESULTS.md](STORAGE_RECOVERY_POC_RESULTS.md) ghi rõ giới hạn.

Schema/container/driver vẫn Proposed; không biến ZIP fixture thành quyết định
production. Power loss, Drive sync và local service security chưa được kiểm.
Render từ package đạt chức năng nhưng **R0 RAM chưa đạt**, một retry bị monitor
dừng; chưa đóng toàn bộ gate storage/render hoặc FR-401–407.

[Resource admission follow-up](RENDER_RESOURCE_ADMISSION_RESULTS.md) sau đó đạt
R0 sampled + chức năng trong một lượt 2×12s; chưa thay kết luận về toàn bộ gate.
