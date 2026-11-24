# Hợp đồng bổ sung UI — TC-01/TC-02

Trạng thái: implementation contract cho Master v2.1, trên `dev`. Đây là metadata ứng dụng độc lập project content; không đổi project schema, renderer, revision, manualSavedHash hoặc lease.

- `GET /api/v1/ui-state`: `{schemaVersion:1,recent:[{id,openedAt}],preferences:{timelineHeight,projectViewMode},version}`. Recent chỉ có project còn tồn tại; timestamp ISO UTC do backend tạo. Tên lấy từ `GET /projects`, không ghi đè bằng metadata.
- `POST /api/v1/projects/{id}/opened` body `{}`: chỉ gọi sau load/create thành công; backend kiểm project còn tồn tại, cập nhật gần đây tối đa 30 theo ID. Không dùng GET/poll làm sự kiện mở. Trả state mới. Read-only được tính là mở.
- `PATCH /api/v1/ui-state` body `{key,value}`: allowed keys `timelineHeight` số nguyên 180–900 và `projectViewMode` `grid|list`. Ghi từng key dưới lock và atomic replace, tránh whole-object overwrite từ tab cũ. Client clamp chiều cao theo viewport; giá trị persist giữ độc lập.
- Tệp `runtime/ui-state.json` tách `storage-policy.json`, không chứa secret/draft/media. Read corrupt fallback defaults và không xóa file hỏng tự động. API dùng auth/session middleware hiện có. Không thêm migration project.

Verification: integration temp workspace; reload, launcher restart, cổng localhost đổi, hai tab cập nhật hai key, không đổi project hash/revision/Manual Save.
