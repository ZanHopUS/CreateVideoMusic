# State, Undo and Template Reuse PoC Results

Ngày: **23/11/2026 (Asia/Saigon)**. POC-04, model/harness riêng; chưa triển khai
editor UI hoặc chọn production state library/architecture.

## Kết quả

Sáu kịch bản: TPL01/02/03 × **12/100 items**, bốn nhóm background/music/lyrics/
caption. Mỗi kịch bản chạy **50 chỉnh sửa → 50 undo → 50 redo**, so hash/JSON tại
từng bước. Một lượt gồm **300 edits, 300 undo, 300 redo**, tất cả khớp state mong đợi.
Đã lặp lại trên thư mục mới sau thay đổi catalog guard, vẫn đạt; đây là lặp cùng
fixtures, không phải corpus độc lập hoặc benchmark có kiểm soát.

Các kiểm tra bổ sung đạt:

- Trim giữ source-end và timeline-end theo rate; reorder không đổi asset reference.
- Edit sai range bị từ chối và không làm đổi state/history; external read copy
  không mutate nội bộ. Edit mới sau undo xóa redo branch.
- Undo về manual-save state làm dirty=false; sửa tiếp trong khi một snapshot cũ
  được đánh dấu saved vẫn dirty=true. Storage suite kiểm thêm tình huống I/O thật.
- Tạo hai instances từ template: project/item IDs khác nhau, selection references
  được remap; sửa instance A không đổi template hoặc instance B.
- Asset references được tái sử dụng; không nhân bản bytes media khi clone state.
- Sáu binding placeholder hợp lệ áp dụng đúng, template gốc không đổi.

## Thiếu sót được tìm thấy và sửa

Model kiểm cấu trúc/time ranges, còn catalog/storage phải kiểm loại media.
Guard trước đó chấp nhận **6 binding sai MIME** (ví dụ audio trong image slot).
Đã tái hiện trên nguồn archive, thêm guard tương thích `image/`, `video/`, `audio/`:
**6/6 bị từ chối**, 6 binding hợp lệ và 10 package cũ vẫn qua validation.
Đây là tương thích MIME metadata, chưa phải MIME sniffing/security scanner cho
media không tin cậy.

Fixture state lấy từ fidelity và clip caption cuối về project end trước phép thử;
không thay snapshot hoặc output fidelity trước đó. Timeline dùng frame-time units
của PoC hiện có, không chốt contract mili-giây/ticks của ứng dụng. 100 items là
tổng items, không phải 100 lớp đồng thời; project duration 300s, nội dung không
phủ kín toàn bộ 300s. UI state được giữ trong schema PoC để kiểm round trip.

## Hiệu năng quan sát, không phải UI latency

| Kịch bản, lượt đầu | Items | Model edit P95 |
|---|---:|---:|
| TPL01 | 12 / 100 | 0.940 / 1.927ms |
| TPL02 | 12 / 100 | 0.204 / 1.262ms |
| TPL03 | 12 / 100 | 0.511 / 1.313ms |

Mỗi số lấy từ 50 thao tác model (clone/edit/validate/history), không gồm UI,
rendering, asset I/O hoặc end-to-end dirty hashing. V8 heap ở checkpoints khoảng
6.9–16.2 MiB trong lượt đầu; không phải process RSS/private peak. Memento full-copy
chỉ là cách thử nhỏ, chưa chọn cho production hoặc chứng minh history dài.

R5 có evidence cho state/undo/reuse trong các fixtures; chưa đóng gate editor
thực, UI P95, interactions hoặc state migration. [Storage/render resource caveat](STORAGE_RECOVERY_POC_RESULTS.md)
phải được đọc riêng, không coi model checks đạt là toàn bộ R0/R3 đạt.

## Bằng chứng

Raw Git-ignored dưới `.poc/state-storage/run-01/`:
[state results](../../.poc/state-storage/run-01/state-results.json),
[fixtures](../../.poc/state-storage/run-01/state-fixtures.json),
[binding checks](../../.poc/state-storage/run-01/extra-results.json).
Lượt lặp hiện tại: [run-02](../../.poc/state-storage/run-02/state-results.json).
Nguồn trước/sau guard được archive riêng. [Runbook](../../poc/state-storage/README.md).
