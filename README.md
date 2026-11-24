# AI Music Video Studio

Studio video âm nhạc local trên Windows 11, giao diện tiếng Việt. Đã có luồng dựng
nhiều ảnh/video/nhạc, ba template, lyrics nhập/duyệt, worker AI local, lưu/mở,
recovery, portable và thư viện/mẫu cá nhân. **Chưa hoàn tất MVP Core hoặc S6**:
đã chạy ma trận render và AI local thật; chất lượng lyrics, listening và các
release gates vẫn cần nghiệm thu theo báo cáo liên kết dưới đây.

[Kết quả và giới hạn hiện tại](docs/planning/S2_S6_RESULTS.md) ·
[Kế hoạch](docs/planning/S2_S6_EXECUTION.md) ·
[RTM](RTM_v1.0.md) · [Contracts](docs/architecture/MVP_CONTRACTS.md)

## Chạy trên máy

Node **24.14.1+ trong nhánh 24.x**, Python **3.12**, Windows 11. Setup lần đầu cần
mạng cho dependency/browser; không tự tải model hoặc gửi media lên AI cloud.

```powershell
./scripts/setup.ps1
./scripts/start.ps1
```

Máy hiện tại đã setup. Launcher chọn ports trên `127.0.0.1`, giữ session ở memory,
Ctrl+C dọn owned processes. `start.ps1 -Restart` mở lại phiên, `stop.ps1` dừng đúng
launcher, giữ media/project. Không sync live SQLite/temp lên Drive.

## Các luồng sử dụng

1. Chọn Ảnh + Caption, Music Card hoặc Lyrics Video; xác nhận quyền dùng media,
   nhập PNG/JPEG, MP4 H.264 và WAV PCM16/MP3/M4A AAC. Một batch thêm nhiều file;
   file lỗi báo riêng, clip đã chỉnh được giữ. Project tối đa 300s.
2. Chọn/kéo/sắp xếp/trim clip; chỉnh fit, vùng cắt, blur, brightness, font/màu/
   viền/shadow và hiệu ứng. Undo/Redo, playhead/seek/zoom; preview dùng shared scene.
   Video nền tắt âm thanh gốc, nhạc dùng clip riêng.
3. Lyrics: nhập LRC/SRT hoặc câu có mốc nguồn; có thể nhận dạng/căn từ local khi
   model đã chuẩn bị. Sửa, **Lưu bản nháp lời vào project**, duyệt rồi **Áp dụng lời
   đã duyệt**. Mốc theo bài hát nguồn, ánh xạ qua trim/rate. Kết quả AI cần review;
   [cấu hình và giới hạn AI](docs/planning/LOCAL_AI_SETUP.md).
4. **Lưu project** tạo checkpoint JSON phụ thuộc thư viện local; không chuyển PC
   bằng JSON riêng. Working save không xóa dirty-state. Trong **Dữ liệu project**
   có recovery riêng (30s, tối đa 10 bản/200 MiB), restore có xác nhận, kiểm/relink
   file gốc cùng SHA và **Đóng gói di chuyển (.amvs)** chứa project + media.
   Mở `.amvs` bằng **Mở file project đã lưu**; restore không ghi đè project đã có.
5. **Thư viện media** tìm theo tên/tags, thumbnail/nghe/dùng lại; gợi ý đoạn dựa trên
   năng lượng, không nhận biết mood/đoạn hay. **Mẫu cá nhân** lưu typed placeholders
   từ project và tạo instance với media/chữ mới, không sửa mẫu gốc.
6. **Xuất video** chọn 720/1080p, 30/60 FPS, dọc/ngang/vuông và folder. Các preset
   đã có UI/backend nhưng **chưa nghiệm thu đủ matrix output mới**. Admission giữ
   RAM trống ≥4 GiB/10 samples, có chờ/hủy/retry; không coi chờ RAM là render pass.
   Chỉ một heavy job AI/render tại một thời điểm.

Một tab ghi/project; tab khác chỉ đọc và có nút nhận quyền rõ ràng. Lease ở memory,
heartbeat 5s/expiry 30s. Takeover nạp state mới nhất; không tự ghi đè bản ở tab khác.

**Kho Google Drive** là opt-in storage riêng, không bật AI cloud. Có backup/restore,
tùy chọn tự sao lưu mặc định tắt; xem [thiết lập và phạm vi evidence](docs/planning/DIRECT_DRIVE_SETUP.md).
Không xóa local sau upload. `.local/workspace` chứa SQLite/library/jobs; không đưa
media, credentials hoặc raw private evidence vào Git. Dọn temp cần xem trước/xác nhận,
chỉ xóa bản tạm của job terminal; source library và output đích được giữ.

## Kiểm tra phát triển

```powershell
npm.cmd run build
npm.cmd run typecheck
npm.cmd test
npm.cmd run format:check
./.venv-api/Scripts/ruff.exe check services/local-api scripts tests
./.venv-api/Scripts/python.exe -m pytest tests/integration -q
npm.cmd run test:e2e -- tests/e2e/core-workflows.spec.ts tests/e2e/drive-settings.spec.ts
./.venv-api/Scripts/python.exe scripts/verify_core.py --matrix --long-run --ai-smoke
```

Browser suite trên kiểm workflow và UI, không thay render E2E hoặc model quality;
AI transport fixture được ghi trong tên test. Suite render cũ: `npm.cmd run test:e2e`
và `scripts/verify_e2e.py`, cần đủ RAM. Runner `verify_core.py` dùng API/renderer thật,
media tự tạo/workspace disposable, ghi blocked riêng. Không hạ admission để tính pass.
Native OS chooser trong browser test dùng fixture grant, khác native picker smoke.

Nguồn: `apps/web`, `services/local-api`, `packages/domain`, `packages/composition`,
`workers/render`. `poc/` là harness lịch sử, không được application import.
