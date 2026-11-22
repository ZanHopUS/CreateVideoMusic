# Open Questions & Architecture Decision Backlog — 22/11/2026

Trạng thái: **Đã được Product Owner xác nhận theo các phương án đề xuất**, ngày **22/11/2026 (Asia/Saigon)**, qua yêu cầu: “xác nhận tài liệu open_questions như đề xuất”.

Phạm vi xác nhận là **định hướng và các điều kiện của cả 18 phương án bên dưới**. Những phương án yêu cầu benchmark, kiểm tra quota/privacy hoặc phê duyệt ngưỡng sau đo vẫn giữ nguyên các điều kiện đó; không coi chất lượng, khả năng tương thích hoặc số liệu chưa đo là đã được kiểm chứng.

Xác nhận này không phải lệnh bắt đầu PoC, cài dependency, tải model, gửi dữ liệu lên cloud, commit hoặc push. Các quyết định A–G giữ nguyên. Những chi tiết mới trong Technical Discovery như checkpoint cụ thể, license aligner Việt, corpus, ngưỡng Go/No-Go và Remotion vẫn cần phê duyệt tương ứng trước thử nghiệm.

| ID | Câu hỏi kỹ thuật | Phương án đã xác nhận; giữ nguyên điều kiện kiểm chứng | Gate | Mức rủi ro |
|---|---|---|---|---|
| AI-01 | Gemini Free Tier có đủ quota/tính năng và điều khoản dữ liệu cho caption/style? | Thử Gemini **chỉ khi** quota miễn phí và privacy chấp nhận được; local rules fallback. Không chọn model cứng trước khi thử. | PoC | Cao |
| AI-02 | OpenAI API có được dùng khi ngân sách free? | Không làm dependency bắt buộc; billing API riêng ChatGPT, chỉ bật khi người dùng tự thay đổi ngân sách. | Requirements | Cao |
| AI-03 | Model local nào nhận dạng hát Việt/Anh trên CPU 16 GB đủ tốt? | Benchmark ít nhất một faster-whisper checkpoint; test ASR trên vocal/music và tự nhận biết lỗi. | PoC | Cao |
| AI-04 | Word alignment Việt/Anh đạt chất lượng nào? | Benchmark theo thể loại, fallback câu và sửa timestamp thủ công. | PoC | Cao |
| AI-05 | Có cần tách vocal (tốn CPU) không? | Chỉ tích hợp nếu benchmark cải thiện rõ so với chi phí tài nguyên. | PoC | Trung bình–Cao |
| AI-06 | Dữ liệu nào được gửi lên API và có cần xác nhận mỗi lần? | Default không gửi; explicit opt-in theo provider/loại dữ liệu, log không lưu nội dung nhạy cảm. | Architecture | Cao |
| ST-01 | Định dạng project portable (JSON + assets hay SQLite + manifests)? | SQLite runtime + snapshot package có schemaVersion, checksums, đường dẫn tương đối. | Architecture | Cao |
| ST-02 | Người dùng chọn folder arbitrary bằng cách nào trên browser local? | Backend local được cấp quyền và validate đường dẫn; không cho frontend gọi path bất kỳ. | PoC | Cao |
| ST-03 | Google Drive sync project mà không làm hỏng DB? | Đồng bộ package snapshot bất biến, không live SQLite/temp. Thử restore sang folder khác. | PoC | Cao |
| ST-04 | Chính sách thiếu dung lượng, quota local, cache/temp và GC? | Cảnh báo, quota cấu hình, cleanup temp có xác nhận, giữ asset dùng chung. | Architecture | Trung bình |
| MED-01 | Có cần ảnh/video/nhạc từ URL ngoài upload và thư viện không? | Không trong Core. Chỉ thêm adapter URL được cấp phép nếu có nhu cầu mới. | Requirements | Trung bình |
| MED-02 | Copyright/license cho bài nhạc và stock assets được xác định ra sao? | User xác nhận quyền sử dụng; không làm downloader TikTok/YouTube/Spotify. | Requirements | Cao |
| MED-03 | Thư viện nhạc gợi ý theo metadata/mood hay phân tích audio? | Metadata/tags thủ công + heuristics trước; benchmark phân tích audio sau. | PoC | Trung bình |
| MED-04 | File caps: upload max MB, codecs, max track count, concurrent jobs? | Đề xuất sau PERF/codec feasibility, công bố giới hạn UI. | Architecture | Trung bình |
| UX-01 | Editor Core hỗ trợ cụ thể bao nhiêu track/layer/effect trước Complete? | 4–5 loại track cốt lõi, không hardcode tổng số; chốt test cases trước Sprint 1. | Planning | Trung bình |
| UX-02 | Template blank builder đủ tiêu chí nào trong Complete? | Add layer, placeholder, edit layout, save/reuse, validate schema. | Planning | Trung bình |
| ARC-01 | Vercel sau MVP dùng Local Agent hay cloud renderer? | Hoãn đến khi Core local ổn định; nếu Local Agent cần auth/CORS/private-network security. | Later | Cao |
| ACC-01 | Threshold latency, RAM, lyrics WER/timing, render quality ra sao? | Baseline bằng benchmark trên máy đích, rồi phê duyệt định lượng. | PoC | Cao |

## Các lựa chọn mặc định đã xác nhận

1. **Gemini caption/style: tắt mặc định.** Chỉ xem xét bật sau khi kiểm tra quota miễn phí, privacy phù hợp và có opt-in rõ theo provider/loại dữ liệu; chưa được phép gửi dữ liệu trong lần xác nhận này.
2. **OpenAI API: không dùng khi chưa có ngân sách được cho phép.** Không làm dependency bắt buộc; không suy luận ChatGPT subscription là ngân sách API.
3. **Có portable project package khi chuyển PC/Drive.** Định hướng ST-01: SQLite runtime + snapshot package có schemaVersion, checksums và đường dẫn tương đối. Định dạng package/schema/driver cụ thể còn phải kiểm chứng.
4. **Không nhập URL ngoài trong Core.** Chỉ xem xét adapter nguồn được cấp phép khi có yêu cầu mới.
5. **Dùng media upload cá nhân có quyền sử dụng.** Chưa xác nhận nguồn stock cụ thể hoặc quyền với từng file; kiểm tra nguồn/license trước dùng làm dữ liệu PoC. Không triển khai downloader TikTok/YouTube/Spotify.

## Phần còn phải kiểm chứng hoặc cụ thể hóa

- AI-03/04/05: checkpoint, chất lượng hát Việt/Anh, word/sentence timing và lợi ích tách vocal so với tài nguyên.
- AI-01/06: quota/account, điều khoản dữ liệu và phạm vi consent thực tế trước bật cloud.
- ST-01–04: schema/package, driver, quyền folder, crash/restore, Drive round-trip, quota/cache/recovery/GC cụ thể.
- MED-02/03/04: quyền của bộ dữ liệu thực, chất lượng gợi ý đoạn/nhạc, codecs/file caps và concurrency.
- UX-01/02: test cases chi tiết cho Core và blank builder Complete; 4–5 loại track không là giới hạn tổng số track.
- ACC-01: đo baseline trước, sau đó trình phê duyệt ngưỡng định lượng; xác nhận này không tự duyệt các con số đề xuất trong `docs/technical-discovery/POC_PLAN.md`.
- ARC-01 tiếp tục hoãn tới khi Core local ổn định; không chọn kiến trúc Vercel trong lần xác nhận này.

Trạng thái kiểm chứng thực nghiệm: **Not run**. Các tài liệu Technical Discovery vẫn là đề xuất ngoài phần định hướng đã được xác nhận tại đây.

## Nguồn tham khảo official, cần kiểm tra lại khi triển khai
- Gemini API pricing/tiers: https://ai.google.dev/gemini-api/docs/pricing
- OpenAI API pricing: https://developers.openai.com/api/docs/pricing
- ChatGPT Plus API separate: https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus
- Drive desktop sync: https://support.google.com/drive/answer/13401938
- Vercel Functions limits: https://vercel.com/docs/functions/limitations
