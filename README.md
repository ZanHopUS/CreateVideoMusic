# AI Music Video Studio

Studio video âm nhạc local trên Windows 11, giao diện tiếng Việt. Kiến trúc đã được
duyệt; hiện có **bản nội bộ TPL-01**: nhập nhiều ảnh/video/nhạc → caption/timeline → preview →
lưu/mở project → xuất MP4 thật. Chưa hoàn tất MVP Core; Lyrics AI, Music Card và
các chức năng S2–S6 vẫn đang phát triển.

## Chạy trên máy

Cần Node **24.14.1+ trong nhánh 24.x**, Python **3.12**, Windows 11. Mở PowerShell tại
repository root. Lần đầu setup cần mạng để tải dependencies và browser render;
không tự tải model AI hoặc gửi media lên cloud.

```powershell
./scripts/setup.ps1
./scripts/start.ps1
```

Setup dùng `python` trên PATH; có thể truyền `-Python <đường-dẫn-python.exe>` nếu
máy có nhiều bản. `./scripts/setup.ps1 -CheckOnly` kiểm versions mà không cài gì.

Máy hiện tại đã được setup. Launcher tự chọn ports trên `127.0.0.1`, mở browser
với session tạm, không in/lưu token. Giữ terminal chạy; **Ctrl+C** để dừng UI/API
và owned children. Launcher dùng Windows Job Object để API/Next không tồn tại
khi launcher đóng đột ngột; mutex chặn mở hai phiên cùng workspace. Session ở
memory; nếu reload/mất session, mở phiên mới bằng `./scripts/start.ps1 -Restart`.
`./scripts/stop.ps1` dừng đúng launcher theo PID/create-time/cwd đã xác minh;
không dừng browser hay ứng dụng khác, không xóa dữ liệu project.

## Thử luồng đầu tiên

**Music Card (TPL-02):** từ dashboard chọn Music Card, nhập hai ảnh (ảnh đầu
làm đoạn mở, ảnh thứ hai là bìa thẻ) và một file nhạc. Đổi tên bài/nghệ sĩ trong
panel Thuộc tính. Thẻ và thanh tiến trình dùng cùng scene cho preview/MP4;
hiện chỉ xuất preset dọc 720×1280/30 FPS. Chọn/đảo thứ tự clip có thể thay đổi
ảnh bìa; kiểm preview trước khi xuất.

1. Chọn **Tạo video mới**. Xác nhận quyền dùng media, chọn nhiều PNG/JPEG, MP4
   H.264 và WAV PCM16/MP3/M4A AAC trong một lần nhập. Batch đầu chia thời lượng
   hình ảnh/video theo project và giới hạn nguồn; nhập thêm nối clip, không thay
   clip đã chỉnh, tự tăng độ dài khi cần (tối đa 300s).
2. Chỉnh caption, vị trí/thời lượng clip, đoạn nguồn nhạc, âm lượng; Undo/Redo và
   preview. Video nền tắt âm thanh gốc, dùng các clip nhạc riêng. Chọn clip để
   đổi fit, trim, xếp trước/sau hoặc gỡ; đổi thứ tự xếp liền các clip trong track,
   giữ source cuts. Gỡ clip không xóa file trong thư viện; Undo/Redo khôi phục được.
   Project tối đa 300s, nhưng app mới E2E với fixtures 2–3s.
3. **Lưu project** mở native folder picker. Checkpoint JSON phụ thuộc thư viện
   media local; **chưa là portable package**, không chuyển máy bằng JSON riêng.
4. **Xuất video** chọn folder xuất. Preset hiện có: **720×1280, 30FPS, H.264/AAC**.
   Job chờ 10 mẫu RAM trống ≥4 GiB trước khi chạy; có progress/hủy/thử lại.

SQLite/media/job temp ở `.local/workspace/`, không đưa vào Git. SQLite/temp không
upload lên Drive; media/project/MP4 có thể sao lưu qua mục **Kho Google Drive**.
Xem [thiết lập Drive trực tiếp](docs/planning/DIRECT_DRIVE_SETUP.md): cần OAuth
client riêng, chưa kiểm chứng cloud thật và chưa tự đồng bộ/restore.
Working
state lưu nền không thay thế manual save; dirty indicator vẫn báo chưa lưu thủ
công. TPL-02/03, recovery UI, portable/Drive, AI và presets khác chưa được công bố
hoàn tất. Dữ liệu/media cá nhân chỉ dùng khi có quyền sử dụng.

## Kiểm tra phát triển

```powershell
npm.cmd run build
npm.cmd run typecheck
npm.cmd test
npm.cmd run format:check
./.venv-api/Scripts/ruff.exe check services/local-api scripts tests
./.venv-api/Scripts/python.exe -m pytest tests/integration -q
npm.cmd run test:e2e
./.venv-api/Scripts/python.exe scripts/verify_e2e.py
./.venv-api/Scripts/python.exe scripts/dev.py --smoke
```

Browser E2E dùng media tự tạo và API/DB/renderer thật; riêng chọn folder OS được
thay bằng grant của test server disposable. Native folder chọn/hủy/Unicode có
helper riêng `scripts/check_native_picker.py` (chỉ điều khiển owned picker PID).
Raw evidence ở `.local/e2e/`, `.local/native-picker/`, Git-ignored. E2E cần đủ RAM;
admission chờ không được tính là render pass. Tests không phụ thuộc media `.poc/`.

Source: `apps/web/`, `services/local-api/`, `packages/domain/`,
`packages/composition/`, `workers/render/`; Python 4 spaces, TS/TSX 2 spaces;
Ruff/Prettier, schema types sinh bằng `npm run types`. `poc/` là harness lịch sử,
không được import vào ứng dụng.

[MVP start/architecture](docs/MVP_START_HERE.md) ·
[Trạng thái triển khai](docs/planning/MVP_IMPLEMENTATION_STATUS.md) ·
[S2 nhiều media](docs/planning/S2_MEDIA_EDITOR_RESULTS.md) ·
[Kết quả PoC](docs/technical-discovery/POC_STATUS.md).
