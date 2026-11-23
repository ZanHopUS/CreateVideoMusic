# AI Music Video Studio

Studio video âm nhạc local trên Windows 11, giao diện tiếng Việt. Kiến trúc đã được
duyệt; hiện có **bản nội bộ TPL-01**: nhập ảnh/nhạc → caption/timeline → preview →
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
và owned children. Chỉ chạy một launcher cho workspace. Session ở memory; nếu
reload/mất session, dừng launcher rồi chạy lại để mở tab mới.

## Thử luồng đầu tiên

1. Chọn **Tạo video mới**. Xác nhận quyền dùng media, thêm PNG/JPEG và WAV PCM16,
   MP3 hoặc M4A AAC. Bản này dùng một ảnh và một track nhạc.
2. Chỉnh caption, vị trí/thời lượng clip, đoạn nguồn nhạc, âm lượng; Undo/Redo và
   preview. Project tối đa 300s, nhưng ứng dụng mới E2E với fixture 2s.
3. **Lưu project** mở native folder picker. Checkpoint JSON phụ thuộc thư viện
   media local; **chưa là portable package**, không chuyển máy bằng JSON riêng.
4. **Xuất video** chọn folder xuất. Preset hiện có: **720×1280, 30FPS, H.264/AAC**.
   Job chờ 10 mẫu RAM trống ≥4 GiB trước khi chạy; có progress/hủy/thử lại.

SQLite/media/job temp ở `.local/workspace/`, không đưa vào Git/Drive. Working
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
[Kết quả PoC](docs/technical-discovery/POC_STATUS.md).
