# State and Local Storage PoC

Harness riêng cho POC-04/05, không phải application/editor code. Chỉ dùng năm
generated assets đã có trong `.poc/render/fidelity-public/`; không đọc nhạc cá nhân.
Không chọn production state library, SQLite driver, schema hoặc package format.

## Điều kiện và chạy lại

Chạy từ repository root trên Windows, dùng Node và venv đã chuẩn bị. Python cần
PyAV/psutil có sẵn; SQLite dùng stdlib. Render bridge dùng dependencies/browser
hiện có của `poc/render/`. Không cần cài thêm để chạy bộ này.

Mỗi lượt dùng ID mới; không ghi đè evidence cũ. Ví dụ sau tạo `run-03`:

```powershell
./.poc/venv-asr/Scripts/python.exe poc/state-storage/prepare.py --run-id run-03
node poc/state-storage/run-state.mjs .poc/state-storage/run-03
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/state-storage/run-03/resources --timeout 300 -- ./.poc/venv-asr/Scripts/python.exe poc/state-storage/run.py --run-id run-03
node poc/state-storage/check-bindings.mjs .poc/state-storage/run-03
./.poc/venv-asr/Scripts/python.exe poc/state-storage/check-extras.py --run-id run-03
./.poc/venv-asr/Scripts/python.exe poc/state-storage/compare-runtime.py --run-id run-03
```

Preparation tạo managed copies/catalog và archive nguồn Python/JS đang chạy.
State suite: 3 templates ×12/100 items, mỗi case 50 edits/undo/redo. Storage suite:
SQLite working state, manual checkpoints, recovery, asset pins, 24 process crashes,
10 restore round trips và malformed packages. Worker exit 77 và duplicate ZIP-name
warning là negative fixtures chủ động; xem kết luận trong `results.json`.
Staging/partial files được giữ làm evidence trong sandbox, không tự cleanup.

`check-extras.py` chỉ import source archive local tin cậy để so guard lịch sử,
không thực thi code từ package nhập. Snapshot mới đã có MIME guard nên số lỗi
guard cũ tái hiện bằng 0 là bình thường. Check mới phải từ chối cả 6 sai bindings.

## Render bridge riêng

Chỉ chạy khi đủ RAM headroom; giữ monitor. Lượt trước concurrency 2 có RAM trống
tụt 1.850 GiB, concurrency 1 bị dừng ở 1.651 GiB: **R0 chưa đạt**. Không tự chạy
thêm render nặng từ kết quả chức năng pass. Khi điều kiện tài nguyên cho phép:

```powershell
./.poc/venv-asr/Scripts/python.exe poc/monitor.py --out .poc/state-storage/run-03/render-resources --timeout 600 --min-start-available-gib 4 --start-samples 10 --admission-timeout 30 -- node poc/render/state-storage-bridge.mjs .poc/state-storage/run-03 --concurrency 1
./.poc/venv-asr/Scripts/python.exe poc/state-storage/validate-render.py --run-id run-03
```

Bridge render TPL02/03 từ package restore bằng composition hiện có; validator
decode MP4 và so PNG trước/sau restore. Không tính output partial hoặc lượt bị
monitor dừng là pass. Monitor dừng RAM <2 GiB liên tục 10s; strict R0 còn đòi hỏi
mọi sample đạt ngưỡng, nên không bị dừng chưa đủ để kết luận R0 pass.

Admission tùy chọn yêu cầu 10 samples liên tiếp, cách khoảng 1s, RAM trống ≥4 GiB
trong tối đa 30s. Đây là policy thử nghiệm của harness, không tăng yêu cầu RAM
sản phẩm hoặc sửa R0 ≥2 GiB. Không đủ headroom: exit 4, ghi `admission.json`,
không khởi chạy child. Khi bật admission phải dùng thư mục output mới; monitor
từ chối ghi đè evidence. Threshold không bảo đảm background load giữ nguyên.
`resources.json` thêm `r0_sampled_pass`; completion/exit 0 vẫn có thể fail R0.
Không truyền admission flags thì monitor giữ cách khởi chạy cũ.

Kiểm tra admission/reset/timeout, child launch bị chặn và R0 strict:

```powershell
./.poc/venv-asr/Scripts/python.exe -m unittest discover -s poc -p test_monitor.py -v
```

## Giới hạn và đọc kết quả

Junction follow-up: `check-junctions.py --run-id junction-03` kiểm 10 escape cases
với 3 junction thật trên Windows; dùng ID mới và terminal có quyền tạo junction.
Canary chỉ ở `.poc/path-canaries/<id>/`, không nhận folder người dùng. Giữ nguyên
junction/canary làm evidence, không cleanup qua alias. [Kết quả và giới hạn TOCTOU](../../docs/technical-discovery/WINDOWS_PATH_SAFETY_RESULTS.md).

Follow-up `render-admission-01` đã qua admission và R0 sampled, min available
2.725 GiB; hai video 12s vẫn qua validation. Đây là một lượt riêng, không thay
fail trước hoặc chứng minh 300s/editor UI. Xem [resource follow-up](../../docs/technical-discovery/RENDER_RESOURCE_ADMISSION_RESULTS.md).

Writes/moves chỉ trong `.poc/state-storage/`. GC cần explicit confirmation và chỉ
xóa managed orphan tự tạo; không xóa source. Recovery confirmation là API policy,
chưa có UI. Process crashes khác power loss; file ENOSPC được inject, SQLite FULL
là lỗi thực trong DB disposable. Drive, concurrent junction replacement, long paths
và app security chưa kiểm. ZIP budgets 16 MiB/entry, 64 MiB tổng là giới hạn fixture PoC.

`results.json` chỉ kết luận chức năng. Đọc `resources.json` riêng cho RAM/timebox.
Manual JSON timings gồm media hashing; dùng `comparison-results.json` cho phép
so working-state cùng scope (5 warm samples), không suy ra SLA/driver lựa chọn.

Báo cáo: [state/template](../../docs/technical-discovery/STATE_TEMPLATE_POC_RESULTS.md),
[storage/recovery và R0](../../docs/technical-discovery/STORAGE_RECOVERY_POC_RESULTS.md).
