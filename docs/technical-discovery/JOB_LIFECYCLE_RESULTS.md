# Render Job Lifecycle Results

Ngày: **23/11/2026 (Asia/Saigon)**. POC-04 harness local, không phải job service
của ứng dụng. Đã render/hủy/retry thật, không dùng mock renderer.

## Hủy API và hủy toàn worker là hai phép đo

Controller gửi cancel sau khi nhận ít nhất 30 rendered frames của job 90s/2700
frames. Worker dùng Remotion `makeCancelSignal`, logs phase và final-file state.
Controller theo dõi worker và descendants bằng **PID + creation time**, tránh
nhầm PID được tái sử dụng; đo bằng monotonic clock.

| Lượt | Cancel request→API terminal | Toàn worker tree thoát | Kết luận |
|---|---:|---:|---|
| `run-01`, API only | **0.015s** | **30.062s** | Không đạt child-exit ≤10s |
| `run-02`, supervised | **0.016s** | **2.063s** | Đạt trong scope thử |

Lượt đầu có 0 PID còn sống sau khi cuối cùng thoát, nhưng vẫn fail deadline.
Không kết luận rò Chrome hoặc nguyên nhân timer upstream khi chưa xác minh.

Supervisor candidate chờ tối đa khoảng 2s sau cancel trước khi kết thúc các PID
thuộc worker đã ghi nhận và vẫn khớp creation time. **Có forced cleanup** trong
run-02; không được báo thư viện đã tự cleanup trong 2s. 19 PID identities được
theo dõi, cuối phép đo **0 còn sống**. Exit code của worker bị kill được phân loại
theo cancel đã acknowledged và output chưa publish, không coi là success render.

## Retry và immutable snapshot

Sau cancel, controller tạo job retry ở thư mục mới từ snapshot TPL03 12s:

- Worker đọc snapshot một lần, deep-freeze object và lưu source hash.
- Trong lúc đang render (≥30 frames), controller sửa caption của **working copy**.
  Working hash thay đổi, snapshot file/hash gốc giữ nguyên.
- Retry hoàn tất MP4 thật, decode đủ **360 frames**. Frame 150 so PNG từ snapshot
  gốc đạt **32.78dB**; so PNG từ working edited chỉ **22.76dB**. Đạt ngưỡng gốc
  ≥30dB và hơn bản edited >3dB đã đặt trước.
- So hình là một frame kiểm chứng cộng với hash/freeze, chưa là kiểm toàn bộ
  semantics multi-track, save/reload, undo/redo hoặc template reuse.

Progress harness chỉ tới ≤90 trong render, 95 khi finalize; **100 chỉ sau khi kiểm
duration/video payload và rename output cuối**. Cancelled job không có `final.mp4`.
File `.partial` có thể giữ làm evidence; retry không dùng lại thư mục bị hủy.
Không tuyên bố toàn bộ temp/cache đã được dọn hoặc cleanup disk-full đã đạt.

## Resource và phạm vi gate

Run supervised gồm cancel/retry/reference checks: wall **23.219s**, sampled private
peak **1.174 GiB**, min available RAM **5.840 GiB**, không resource abort.

**R4/R5 partial evidence:** render-phase cancel, isolated worker cleanup, clean
retry, publish-last và immutable snapshot có phép đo đạt trên harness. Các phần
còn thiếu: cancel trong finalize/mux/publish, crash/restart, timeout/error injection,
disk-full, editor thực khi render, 100-item timeline, 50 edits + undo/reuse và save/reload.
Không đánh toàn bộ R4/R5 hoặc FR-409/410 Verified từ kết quả này.

## Bằng chứng và quyết định

Raw `.poc/evidence/poc-04/lifecycle/`, Git-ignored:
[API-only failure](../../.poc/evidence/poc-04/lifecycle/run-01/cancel-result.json),
[supervised validation](../../.poc/evidence/poc-04/lifecycle/run-02/validation.json),
[resources](../../.poc/evidence/poc-04/lifecycle/run-02-resources/resources.json).
Worker logs gồm snapshot hash, phases, renderedFrames và trạng thái finalExists.
[Runbook](../../poc/render/fidelity/README.md).

Đề xuất giữ **worker isolation + bounded supervisor cleanup** làm candidate
nghiên cứu tiếp; chưa phê duyệt kiến trúc sản phẩm hoặc mở quyền kill process ngoài
worker ownership. Giữ baseline lỗi để kiểm regression trước thay đổi renderer.
Tiếp theo: lifecycle ở các phase khác, state/undo/template harness rồi storage recovery.
