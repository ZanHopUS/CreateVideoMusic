# Kế hoạch thực thi S2–S6

Ngày 24/11/2026. Người dùng giao tự lập kế hoạch và triển khai tới S6. Chỉ sửa trên
`dev`; commit/push/phát hành cần chỉ dẫn riêng. Baseline FR/AC và ADR giữ nguyên.

| Mốc | Thay đổi và module | Xác minh |
|---|---|---|
| S2 | Domain lyrics/import/time mapping; composition effects/typography; editor ba mẫu, presets | Parser lỗi/draft/review, source trim/rate, history; browser ba mẫu |
| S3 | Provider local thực qua worker, job dùng chung heavy slot; model offline, result review | ASR thật với model đã có; cancellation/missing model; không tự apply draft |
| S4 | Store recovery/checksum/package; relink; export 12 presets, metadata validation | Restore không overwrite, corrupt/traversal/limits, optimistic race, preset output matrix |
| S5 | Catalog/search/reuse, template slots/instances, suggestions và Drive faults | Source bytes/template gốc bất biến, schema/hash, suggestions không tự apply, cloud opt-in |
| S6 | E2E/regression/security/offline/performance và tài liệu | Matrix 36, 300s khi admission đủ; ghi riêng nghe/quality/corpus/ACC-01 chưa nghiệm thu |

Dependency: dùng packages hiện có; AI dùng environment/model local đã chuẩn bị ở
PoC, không import application từ PoC. Không tải model hoặc bật AI cloud ngầm.
RAM admission 4 GiB giữ nguyên. Bằng chứng fixture ngắn không thay long-run.

Rủi ro: ASR hát chưa đạt quality gate; RAM có thể chặn render; timing gold và
listening cần đánh giá độc lập. Mọi giới hạn ghi vào kết quả S6 và RTM, không đánh
Verified chỉ vì có code/unit test. Chỉ hỏi quyết định mới khi thực sự thiếu quyền
hoặc lựa chọn sản phẩm chưa được duyệt; tiếp tục phần không phụ thuộc.
