# Open Questions & Architecture Decision Backlog — 22/11/2026

Trạng thái: **Chưa xác nhận**. Các đề xuất mặc định bên dưới KHÔNG được xem là quyết định đã chốt.

| ID | Câu hỏi cần quyết định | Phương án và khuyến nghị tạm | Gate | Mức rủi ro |
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

## Các quyết định cần người dùng xác nhận trước triển khai kỹ thuật
1. Có chấp nhận AI caption/style từ Gemini Free Tier khi phải gửi nội dung lên Google không? Default: tắt.
2. Có dùng bất kỳ OpenAI API nào khi không có ngân sách trả phí? Default: không.
3. Media project có cần portable package khi chuyển PC/Drive không? Đề xuất: có.
4. Có muốn nhập từ URL ngoài không? Default: không ở Core.
5. Có nguồn nhạc/ảnh/video bản quyền hoặc stock được cấp phép dự kiến không? Hiện chỉ xác nhận upload cá nhân.

## Nguồn tham khảo official, cần kiểm tra lại khi triển khai
- Gemini API pricing/tiers: https://ai.google.dev/gemini-api/docs/pricing
- OpenAI API pricing: https://developers.openai.com/api/docs/pricing
- ChatGPT Plus API separate: https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus
- Drive desktop sync: https://support.google.com/drive/answer/13401938
- Vercel Functions limits: https://vercel.com/docs/functions/limitations
