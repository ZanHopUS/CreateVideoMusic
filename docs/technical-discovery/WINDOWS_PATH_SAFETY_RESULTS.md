# Windows Junction Safety Follow-up

Ngày: **23/11/2026 (Asia/Saigon)**. Local POC-05 trên Windows 11/Python 3.12;
chỉ dùng generated assets và canary disposable, không dùng media cá nhân.

## Mục tiêu và kết quả

Các package traversal fixtures trước chỉ kiểm archive paths. Follow-up này tạo
**3 directory junction thật** bằng Windows `mklink /J`, kiểm resolved paths khi
thao tác filesystem. **10/10 tình huống vượt phạm vi bị từ chối** bởi guards hiện
có; không cần sửa storage policy để làm các case này pass.

| Junction / phép thử | Kết quả |
|---|---|
| Alias ra canary ngoài `.poc/state-storage/`, vẫn trong workspace `.poc/` | `owned()` từ chối |
| SQLite write, manual save, package export qua alias này | Từ chối trước ghi |
| Restore vào destination qua alias | Từ chối trước tạo restore staging |
| Library có `assets/` junction ra canary ngoài sandbox | Asset validation/export/GC từ chối |
| Library có `assets/` junction sang sibling library trong cùng sandbox | Asset validation và GC từ chối vì ngoài library được chỉ định |

Inventory/hash canary và sibling library trước/sau khớp; không có file mới ngoài
phạm vi. GC dùng `confirmed=True` vẫn bị path guard chặn, không xóa canary.
Junctions và canaries được giữ trong `.poc/` làm evidence, không recursive cleanup.

Lượt `junction-01` không tạo được junction trong sandbox execution, không có kết
luận pass. Chạy native được cấp quyền ở thư mục mới `junction-02` mới tạo đủ ba
junction và hoàn tất kiểm chứng. Không gộp lượt setup thất bại thành security pass.

## Giới hạn

Đây là **junction tồn tại trước thao tác**, không thay link đồng thời hoặc đo
TOCTOU race. `Path.resolve()` + containment checks chưa chứng minh an toàn nếu
directory bị đổi sau kiểm tra. Chưa audit tất cả reparse types, hardlinks,
permission ACL, long paths, local service Origin/Host/capability hoặc media parser.
Không kết luận FR-406/local service security Verified từ harness này.

## Chạy lại và bằng chứng

Từ repository root, Windows terminal có quyền tạo junction trong workspace:

```powershell
./.poc/venv-asr/Scripts/python.exe poc/state-storage/check-junctions.py --run-id junction-03
```

ID phải mới. Script giữ test data ở `.poc/state-storage/<id>/` và canary riêng
`.poc/path-canaries/<id>/`, từ chối ghi đè. Không nhận target tuỳ ý từ CLI.

[Raw results](../../.poc/state-storage/junction-02/results.json) có danh sách checks,
junctions và canary hashes. Source snapshot/hash giữ cùng lượt; đọc cùng
[storage/recovery](STORAGE_RECOVERY_POC_RESULTS.md). Schema/container/driver và
folder capability của ứng dụng vẫn Proposed; không đổi A–G hoặc thêm dependency.
