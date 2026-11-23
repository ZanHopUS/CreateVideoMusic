# MVP Implementation Status — S0 / S1

**S2 Music Card:** [kết quả triển khai](S2_MUSIC_CARD_RESULTS.md) có TPL-02
chọn được, tên bài/nghệ sĩ, ảnh bìa và progress cùng scene. MP4 chức năng 3s
đã kiểm bằng test-only admission 3 GiB; production 4 GiB chưa đủ RAM để qua gate.

**Drive trực tiếp:** [thiết lập và kết quả](DIRECT_DRIVE_SETUP.md) có OAuth/Picker,
sao lưu, tìm backup và khôi phục project mới. Tài khoản thật đã kết nối; bản cloud
4 project/0 media/0 MP4 đã restore 4/4 vào workspace thử. Fixture khác có PNG,
H.264 MP4 nguồn, WAV và MP4 xuất đã round-trip SHA; media trùng được dùng lại.
Tự sao lưu 30 giây là tùy chọn, mặc định tắt; chưa đo chạy dài hoặc chuyển PC.
Chưa coi kho Drive chính hoàn tất.

Ngày: **23/11/2026**. PO đã duyệt [ADR-0001](../decisions/ADR-0001-LOCAL_MVP_ARCHITECTURE.md)
và [contracts](../architecture/MVP_CONTRACTS.md) qua “duyệt theo đề xuất”. Conditional
entry được chấp thuận, không phải G2/G4/G5 Passed. Git `dev`.

**Cập nhật S2:** [nhiều media + launcher](S2_MEDIA_EDITOR_RESULTS.md) đã có evidence
17 Vitest, 14 pytest, 2 browser render cases + 1 partial-import case. Nội dung S0/S1
bên dưới là checkpoint lịch sử `90d3d60` đã push; thay đổi S2 thuộc lượt triển khai này.
Chưa coi toàn bộ S2 hoặc Core hoàn tất.

## Đã triển khai

| Phần | Hành vi thực tế |
|---|---|
| Foundation | npm workspaces, Next/TS/Tailwind, FastAPI/Uvicorn env riêng, lockfiles và Ruff/Prettier |
| Domain | JSON Schema versioned cho project/template/job, TS generated types, Python validation; JCS/hash golden parity |
| Local access | Loopback UI/API, session header, exact Origin/Host, opaque folder grant; native picker Unicode/cancel |
| Read media | Authorized IDs, ranged streaming; HttpOnly SameSite cookie chỉ cho GET/HEAD asset/output, không thay header cho API ghi |
| Project | SQLite WAL/FULL, optimistic revision, managed image/audio import, dirty hash tách manual save |
| Editor TPL-01 | Layer ảnh/nhạc/caption, Player dùng shared scene, chọn/kéo clip, trim/duration/source offset/volume, caption font size/color, Undo/Redo |
| Save/open | Checkpoint JSON stage/validate/replace, working state nền, sidebar reopen/manual-file endpoint; source/shared bytes giữ nguyên |
| Render | Immutable snapshot, single heavy slot, admission 4 GiB/10 samples, Node Remotion + FFmpeg, validate trước publish; job progress/cancel/retry và status sau mở lại browser |
| Launcher | Một PowerShell command khởi UI/API ports động, session không persist, Ctrl+C dọn owned processes; smoke mode tự dừng |

Không import code từ PoC vào application. Model types ở `packages/domain/`; controller
ở `apps/web/hooks/`, view/inspector/timeline tách riêng, shared scene ở composition.
Native `<img>/<audio>/<video>` cần read-only session cookie vì không gắn bearer header;
chi tiết này đã được ghi trong ADR, không mở endpoint nhận arbitrary filesystem path.

## Verification thực hiện

- **11 Vitest tests**: canonical hash cùng Python, Unicode/float fixture, time
  mapping, invalid version/range/reference/track/preset, history rollback/branch,
  template placeholder và job DTO.
- **11 pytest integration tests**: auth/origin/host/forged grant, 16 MiB JSON budget,
  optimistic conflicts, manual dirty/checkpoint và replace failure, corrupt upload,
  read-only cookie, shared asset không xóa khi delete project, DB newer-version
  preservation, template/job schema, queued cancel/snapshot isolation và **real
  child/grandchild cancellation** giữ process không liên quan.
- Production build, typecheck, Ruff/Prettier checks và `pip check` đã chạy.
  Test client có một warning upstream về httpx; chưa là lỗi runtime của app.
- Native Windows folder chooser: **2 cases thật**, cancel + chọn directory tiếng
  Việt; helper chỉ gửi Windows messages tới owned PID tree, không global keys.
  Lượt helper đầu chưa theo PID tree của venv launcher không tìm thấy window;
  không tính pass; bản sửa đã đạt. Launcher smoke kiểm UI→API session và cleanup.
- Browser E2E: tạo project → nhập PNG/WAV tự tạo → caption → Undo/Redo → save/reopen
  → render với browser vẫn mở → tải MP4 → mở browser lại vẫn thấy job/output.
  Folder dialog trong E2E được thay bằng grant của fixture server; native test riêng.

Output fixture E2E đã kiểm độc lập: **720×1280, 30FPS, H.264/AAC, 2.000s,
60 frames, 0 timestamp errors**, decode audio có AAC padding (96,256 samples,
không coi decoded padding là duration container). Source tone/ảnh đều tự tạo.
Đây là functional evidence cho một slice, không phải 300s/all-preset/fidelity hoặc
perceptual quality acceptance. FFmpeg finalization còn cần listening review.

Hai E2E attempts ban đầu không đạt vì job chờ RAM; vẫn giữ evidence. Sau khi user
đóng bớt ứng dụng, full flow đã chạy với ngưỡng 4 GiB nguyên vẹn. Resource verdict
job chỉ bao phủ render/finalize children sampled; không chứng nhận toàn bộ API/
preview process memory, UI P95 hoặc R0 cho mọi workload.

## Evidence và reproducibility

Raw/private artifacts Git-ignored: `.local/e2e/<run>/results.json`, job resources,
admission, independent-validation và screenshots; `.local/native-picker/<run>/`
và `.local/evidence/s0/dependency-inventory.json`. Installed Node 24.14.1, Python
3.12.6, SQLite 3.45.3; Next 16.4.6/React 19.3.1/Remotion 4.0.545, FastAPI 0.165.0.
Exact transitive versions: root npm lock + API requirements lock. Browser đã tải
trong setup riêng; không cài/tải model AI mới. License metadata/hashes đã inventory,
không coi đó là pháp lý clearance cho phân phối hoặc mọi model/font/codec use.

[Summary local](../../.local/evidence/s0-s1/summary.json) chứa run IDs/hashes và
source inventory của checkpoint hiện tại. [README](../../README.md) có setup/start
và lệnh verification thực; restart launcher nếu session memory đã mất.

## Chưa hoàn tất và bước tiếp theo

**S0 foundation có evidence trên máy hiện tại; S1 là slice nội bộ có chức năng,
chưa nghiệm thu đầy đủ Core FR.** Playhead/manual view được kiểm thêm trong E2E;
panel/selection/timeline zoom và long-run/history/resource behavior chưa đủ.

Tiếp theo S2 theo [kế hoạch](MVP_IMPLEMENTATION_PLAN.md): đủ TPL-02/03, nhiều
media, editor interactions và Player/export regression. S3 tích hợp ASR/alignment
local thật + review; S4 recovery/package/permissions hardening/jobs faults; S5
library/template reuse/suggestions/Drive. Không tự bỏ các phần chưa có evidence.

Release blockers còn mở: lyrics quality/gold, VFR policy, UI FPS/P95, 300s ứng dụng
thật + contention/repetitions, full preset matrix, audio listening, TOCTOU/service
audit, disk/temp/GC, project recovery, portable/migration/Drive restore. Không
quảng cáo manual-only là Core hoặc lấy harness PoC thay RTM Verified.

Commit application đề xuất: `feat(mvp): bootstrap local studio and TPL-01 workflow`.
Hồ sơ và PoC follow-ups chưa commit có thể tách commit theo mục đích, sau user duyệt.
