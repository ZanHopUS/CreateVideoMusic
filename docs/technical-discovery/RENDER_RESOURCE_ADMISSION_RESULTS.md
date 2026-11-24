# Render Resource Admission Follow-up

Ngày: **23/11/2026 (Asia/Saigon)**. Follow-up local POC-04/05; không triển khai
ứng dụng hoặc đổi quyết định A–G. Bộ state/storage đã push tại `de401aa`.

## Thay đổi và mục đích

Hai lượt render restore trước có min available 1.850/1.651 GiB, một lượt bị dừng.
`poc/monitor.py` thêm admission tùy chọn để từ chối khởi chạy khi thiếu headroom:

- Candidate policy: RAM trống ≥4 GiB ở **10 samples liên tiếp**, cách khoảng 1s,
  tối đa chờ 30s. Admission không đạt: exit 4, ghi lý do, không tạo child.
- Khi bật admission phải dùng evidence folder mới; không ghi đè lượt cũ.
- `resources.json` thêm `r0_sampled_pass`: phải có samples, exit 0, không abort,
  tất cả samples private ≤12 GiB và available ≥2 GiB.
- Giữ nguyên điều kiện dừng available <2 GiB liên tục 10s và private >12 GiB.
  Không truyền flags thì giữ cách khởi chạy cũ.

4 GiB là headroom đề xuất cho harness, **không phải yêu cầu RAM sản phẩm mới**,
không thay R0 ≥2 GiB và không phải reservation bảo đảm RAM. Background load có
thể đổi sau admission; monitor trong khi chạy vẫn bắt buộc.

## Kiểm chứng

Năm unittest đạt: reset chuỗi khi gặp sample thấp, timeout từ chối, boundary bằng
ngưỡng, completed child không che R0 fail, và CLI từ chối thực sự không khởi chạy
marker child. Test CLI cũng kiểm từ chối ghi đè admission evidence. Không cấp phát
RAM lớn hoặc đóng ứng dụng khác để tạo tình huống thiếu RAM.

Lượt thật `render-admission-01`: cùng fixtures TPL02/TPL03, managed assets và
composition của bridge trước; concurrency **1**. Không đổi chất lượng/output
preset, không cài dependency. 10 admission samples có min available **4.033 GiB**.

| Đo trong child workload | Kết quả |
|---|---:|
| Wall time, không gồm admission | 79.828s |
| Resource samples, khoảng 1s | 79 |
| Peak private, process tree | 1.047 GiB |
| Min system available | **2.725 GiB** |
| Samples available <2 GiB | 0 |
| Exit / abort | 0 / không |
| R0 sampled trong lượt này | **Pass** |

Sau render, validator decode H.264/AAC của cả hai MP4: mỗi bản 12.000s,
360 frames, 0 timestamp errors, có audio. Sáu PNG pairs trước/sau restore giống
pixel; MP4/PNG min PSNR TPL02 **36.09dB**, TPL03 **32.33dB**, đều ≥30dB.
Không thay video preview lời Việt đã được user duyệt.

## Kết luận và giới hạn

**Conditional Go cho candidate admission + bridge trong lượt 12s này**: chức năng
và R0 sampled cùng đạt. Không thay kết quả fail cũ hoặc coi admission đã chữa mọi
memory issue. Chưa là cold/warm repetitions có kiểm soát, 300s stress với admission,
editor UI contention, OOM/paging audit hoặc chứng minh mọi máy 16 GB đều chạy được.
Không suy cải thiện hiệu năng từ so wall time khi background load không kiểm soát.
Sampling 1s có thể bỏ sót peak; chưa đo peak temp/disk I/O.

State/storage checks giữ kết quả ở [báo cáo trước](STORAGE_RECOVERY_POC_RESULTS.md).
Drive/power loss chưa chạy; schema/container/driver vẫn Proposed. Các gate Lyrics
quality, VFR policy và editor nghiệm thu vẫn mở theo [POC_STATUS.md](POC_STATUS.md).

## Tái lập và bằng chứng

### 300s follow-up attempt

Harness stress và validator thêm `--run-id` để tách output/bundle, từ chối unsafe
ID và không ghi đè config/raw/bounded/error evidence. TPL03 dọc 300s/1080p60,
concurrency 2 như baseline, đã yêu cầu chạy trong `admission-01`. Preflight không
có 10 samples liên tiếp ≥4 GiB trong 30s nên exit 4, **child không khởi chạy**.
Đây là admission denial, không phải 300s render fail hoặc pass; chưa có R0/R3 mới.
[Admission evidence](../../.poc/evidence/poc-04/tpl03-9-16-300s-1080p60-admission-01/resources/admission.json).

Kiểm tra CLI thật: renderer/validator từ chối run ID có traversal; renderer từ
chối output baseline đã tồn tại, hash config cũ không đổi. [Stress runbook](../../poc/render/STRESS_RENDER.md)
có lệnh chạy lại với ID mới khi RAM đủ. Không hạ ngưỡng hoặc tự đóng ứng dụng user.

[Runbook](../../poc/state-storage/README.md) có flags admission và lệnh unittest.
Raw evidence Git-ignored dưới `.poc/state-storage/run-01/`:

- [admission](../../.poc/state-storage/run-01/render-admission-01/admission.json),
  [resources](../../.poc/state-storage/run-01/render-admission-01/resources.json),
  [summary](../../.poc/state-storage/run-01/render-admission-01/summary.json).
- [validation](../../.poc/state-storage/run-01/render-check-admitted-01/validation.json),
  source snapshot/inventory và output artifact hashes giữ cùng lượt.

Thay đổi follow-up trên `dev`, chưa commit/push. Commit đề xuất:
`test(poc): gate render startup on stable memory headroom`.
