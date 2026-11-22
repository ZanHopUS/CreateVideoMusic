# Vietnamese Lyrics Preview — PoC Review Artifact

Ngày: **22/11/2026 (Asia/Saigon)**. Trạng thái: **đã được user xác nhận “đạt” cho preview 33.9s**, sau khi xuất và kiểm tra kỹ thuật. Đây là nghiệm thu định tính trong phạm vi clip, chưa có annotation timing từng từ độc lập. User ưu tiên tiếng Việt; tối ưu tiếng Anh được hoãn, không tự xóa yêu cầu song ngữ trong baseline.

## 1. Preview đã tạo

[Mở video MP4](../../.poc/evidence/poc-03/vi-lyrics-review/vi-lyrics-review.mp4)

- Audio thật của mẫu `vi-001`; lời từ SRT user gửi, word timing từ author-loader alignment đã chạy.
- Phạm vi bài gốc **0:43.000–1:16.900**, duration **33.9s**; không thay đổi file nguồn.
- **720×1280, 30FPS, 1.017 frames**, MP4 H.264/AAC stereo 48kHz; file **2,022,468 bytes**.
- Bao gồm cues **3–9**: **6 câu word draft**, **cue 5 fallback theo câu**.
- Hiển thị đủ câu, tô vàng và gạch chân từ đang active; câu fallback giữ nguyên cả câu, không tạo timing từng từ giả. Mọi nhãn hiển thị bằng tiếng Việt và video được đánh dấu bản nháp.
- Câu fallback ở khoảng **10.61–15.00s trong clip**, tương ứng **53.610–57.998s của bài gốc**.

Đây là preview PoC đã được user chấp nhận để kiểm tra kết quả alignment; chưa nghiệm thu editor hoặc toàn bài.

### Phạm vi nghiệm thu

Phản hồi user: **“đạt”**, ngày **22/11/2026**. Áp dụng cho đúng MP4 được gửi, đoạn nguồn **43.000–76.900s**, cues **3–9**, gồm cả word mode và câu fallback. [user-acceptance.json](../../.poc/evidence/poc-03/vi-lyrics-review/user-acceptance.json) lưu SHA-256 của video để ràng buộc phản hồi với artifact cụ thể.

Không suy rộng sang toàn bộ 68 câu Việt, mẫu Anh, ASR khi thiếu lời, ma trận export hoặc release. Không đổi phản hồi định tính thành word MAE/P95 hoặc bằng chứng đạt ≤100ms. Xác nhận này chưa cho phép commit/push.

## 2. Timeline và audio

Một mapping duy nhất dùng cho lyric state: `sourceTime = 43 + frame / 30`. Audio được crop từ cùng source ở 43s, decode PCM16 stereo/48kHz trước khi Remotion encode AAC. Không dùng timestamp của clip như timestamp bài gốc hoặc cộng/trừ offset lần hai.

Trạng thái cue/word dùng khoảng `[start,end)`. Trước render, kiểm tra trạng thái ngoài cue, tại cuối fallback và một frame chứa word active thực tế. Hiển thị 30FPS lượng tử hóa thời điểm đổi chữ tối đa một frame khoảng **33.33ms**, chưa tính lỗi alignment của model.

## 3. Kiểm tra bản MP4 thực

| Hạng mục | Kết quả |
|---|---|
| ffprobe metadata | H.264/AAC, dimensions/FPS/duration đúng |
| Decode video | Đủ 1.017 frames, không lỗi decode |
| Word frame | Frame 66, source 45.2s: có underline vàng liên tục dài 154px |
| Fallback frame | Frame 384, source 55.8s: không có underline; longest gold-like run 1px |
| Audio correlation | Ba cửa sổ 2s bắt đầu tại giây 1/15/30 của clip: offset peak **0ms**, correlation **0.99988–0.99994** |
| Visual review | Đã xem PNG ở cả hai chế độ; dấu Việt và dòng chữ không bị cắt ở các ảnh đó |

Pixel màu lẻ ở viền glyph có thể do subpixel antialiasing/nén 4:2:0, nên phép kiểm highlight dựa trên underline liên tục thay vì đòi fallback có đúng 0 pixel giống màu vàng. Audio correlation xác nhận bảo toàn audio crop qua encode, **không chứng minh từ tô sáng khớp âm tiết đang hát**.

Run cuối renderMedia mất **100.46s** (RTF khoảng **2.96**); supervisor gồm bundle/stills mất **108.14s**. Peak private workload sampled **1.02 GiB**, min system available **4.15 GiB**, không chạm điều kiện dừng. Đây là một run, không phải performance SLA hoặc kết quả 1080p60/300s.

## 4. Bằng chứng và tái lập

- [input.json](../../.poc/evidence/poc-03/vi-lyrics-review/input.json), [provenance.json](../../.poc/evidence/poc-03/vi-lyrics-review/provenance.json): cue/word data, source offset, hash alignment/audio và crop command.
- [render-result.json](../../.poc/evidence/poc-03/vi-lyrics-review/render-result.json): duration/config, code hashes và thời gian.
- [validation.json](../../.poc/evidence/poc-03/vi-lyrics-review/validation.json), [ffprobe.json](../../.poc/evidence/poc-03/vi-lyrics-review/ffprobe.json), [resources.json](../../.poc/evidence/poc-03/vi-lyrics-review/resources/resources.json).
- [Word PNG](../../.poc/evidence/poc-03/vi-lyrics-review/word.png), [fallback PNG](../../.poc/evidence/poc-03/vi-lyrics-review/fallback.png).
- [Hướng dẫn chạy lại](../../poc/render/LYRICS_REVIEW.md).

Không thêm dependency, không dùng cloud inference hoặc upload media. Media, lời và output tiếp tục ở `.poc/`, Git-ignored; source harness ở `poc/render/`. Chưa commit/push thay đổi mới.

## 5. Chưa thể kết luận

User đã chấp nhận chất lượng preview chứa cả word mode và cue 5 fallback. Chưa có annotation word boundaries độc lập, chưa đo word MAE/P95, chưa chứng minh fidelity interactive Player. Chưa chạy đủ 36 preset hoặc stress 300s; không đánh toàn bộ FR Verified từ preview này. `validation.json` giữ nguyên trạng thái máy đo trước phản hồi user; nghiệm thu được ghi riêng trong `user-acceptance.json`.

Có thể tiếp tục mở rộng đoạn/bộ dữ liệu và rendering matrix từ checkpoint preview đã được chấp nhận. Nhánh audio-only vẫn cần benchmark `medium`/tiền xử lý so với `small` theo kế hoạch riêng; preview dùng lời có sẵn chưa cải thiện nhận dạng tự động.

Commit đề xuất khi được user duyệt: `test(render): add Vietnamese lyric timing review preview`.
