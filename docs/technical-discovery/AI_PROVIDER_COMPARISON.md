# AI Provider Comparison

Ngày tra cứu: **22/11/2026 (Asia/Saigon)**. Trạng thái: **nghiên cứu tài liệu chính thức, chưa gọi inference/API và chưa xác minh tài khoản**. Giá USD là snapshot để so sánh, không phải báo giá cam kết. Không chọn model cứng trước PoC.

**Cập nhật xác nhận 22/11/2026:** Product Owner xác nhận định hướng AI-01–06 trong [OPEN_QUESTIONS.md](../../OPEN_QUESTIONS.md): local trước, cloud tắt mặc định, Gemini chỉ khi đủ điều kiện và explicit opt-in, OpenAI không là dependency trả phí bắt buộc. Các mục “chưa xác nhận” về quota/privacy/account/credit vẫn chưa được kiểm chứng; xác nhận định hướng không cấp consent gửi dữ liệu hoặc gọi API.

## 1. Vai trò và lựa chọn đề xuất

| Phương án | Lyrics ASR / alignment | Caption/style | Offline / chi phí dịch vụ | Riêng tư và hạn chế |
|---|---|---|---|---|
| Local faster-whisper + aligner | Ứng viên chính; chất lượng hát chưa đo | Không coi ASR là model tạo caption; dùng nhập tay/rules trước | Offline sau khi chuẩn bị đủ artifact; không phí inference API, vẫn tốn CPU/điện/disk | Xử lý local không tự bảo đảm log/cache kín; kiểm tra outbound và licenses |
| Local whisper.cpp | Ứng viên thay runtime ASR | Tương tự trên | CPU/quantized; cần đo packaging | Không coi token timing là forced alignment đã kiểm chứng |
| Gemini Developer API Free Tier | Có model audio, nhưng ngoài baseline PoC local lyrics; không bảo đảm word timing hát | Ứng viên optional cho gợi ý Việt bằng text | Online, miễn phí trong quota model/account đủ điều kiện | Unpaid data-use cần user chấp thuận; không gửi nội dung nhạy cảm |
| OpenAI API | Chỉ xem xét khi có ngân sách/credit và consent riêng | Optional, không dependency Core | Online, tính phí theo endpoint/model; không có bảo đảm quota miễn phí cho dự án | Không train mặc định không đồng nghĩa không lưu dữ liệu |

Đề xuất: local lyrics làm mặc định, manual/LRC/SRT và review luôn có; caption nhập tay/rules khi không có provider. LLM cloud không dùng để “khôi phục” lời hát không nghe được. Thất bại 429/network không chặn edit/render và không tự chuyển sang provider khác.

Local baseline dùng checkpoint multilingual `small` CPU INT8; chỉ tăng lên `medium` sau đo. Không dùng `.en` làm baseline Việt. faster-whisper hỗ trợ CPU INT8, whisper.cpp công bố Windows; chất lượng và tương thích dependency đầy đủ vẫn cần máy đích. [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [whisper.cpp](https://github.com/ggml-org/whisper.cpp).

## 2. Gemini: hạn mức, chi phí và data-use

Pricing hiện có Free Tier cho một số model. Ví dụ `gemini-3.5-flash-lite`: input/output Free Tier được niêm yết miễn phí; paid Standard input **$0.30/1M tokens**, output **$2.50/1M tokens**, gồm thinking output. Đây là ứng viên khảo sát caption, không phải lựa chọn triển khai. Model khác và tool bổ sung có bảng giá riêng. [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite).

Quota có RPM, input TPM và RPD, áp theo project/model/tier; tạo thêm key không tạo quota project mới. RPD reset theo giờ Pacific. **Chưa xác minh số RPM/TPM/RPD của tài khoản dự án**; xem active limits trong AI Studio trước thử, không dùng con số từ bài viết cũ hoặc suy ra từ quota grounding. [Gemini rate limits](https://ai.google.dev/gemini-api/docs/rate-limits).

Unpaid Services có thể dùng input/output để cải thiện sản phẩm và có human review; terms yêu cầu không gửi thông tin cá nhân/nhạy cảm/bí mật. Có ngoại lệ theo khu vực hoặc cách phân loại dịch vụ, cần kiểm tra account thực tế. Không suy ra rằng trả phí đồng nghĩa zero retention. Terms cũng có điều kiện tuổi, khu vực và mục đích sử dụng; mức phù hợp với app cá nhân/học tập này **chưa chốt**. [Gemini terms](https://ai.google.dev/gemini-api/terms#unpaid-services).

Không cần audio/video thật để PoC caption. Nếu TD-06 được duyệt: dùng text tổng hợp không chứa lời bài hát riêng tư, metadata cá nhân hoặc tên đường dẫn; lưu model ID, tier, giới hạn hiển thị, thời điểm và output đã khử dữ liệu nhạy cảm. Không bật billing/paid fallback để vượt quota.

## 3. OpenAI: hạn mức, chi phí và data-use

API billing tách ChatGPT Plus; không được suy luận mua Plus là có ngân sách API. Tài liệu hiện cũng có API credits dành cho **Pro/Business đủ điều kiện**, phải liên kết/claim và có hạn dùng; đó không phải free tier phổ quát, chưa xác minh user đủ điều kiện. Không mua subscription hay kích hoạt quyền lợi trong task này. [ChatGPT Plus](https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus), [API credits](https://developers.openai.com/api/docs/guides/chatgpt-api-credits).

Ví dụ bảng Standard hiện niêm yết `gpt-6.2-sol` input **$2/1M tokens**, output **$10/1M tokens**; cached input, processing mode, tool và vùng có cách tính riêng. Đây là ví dụ chi phí, không phải model được chọn hoặc giá transcription. Không dùng giá model text cho audio endpoint. [OpenAI pricing](https://developers.openai.com/api/docs/pricing).

Rate limits phụ thuộc model/organization/project/tier và có các chiều request/token/time; **chưa xác minh RPM/TPM, balance hoặc credit expiry của user**. Không thể kết luận “đủ quota” từ thông tin công khai. [OpenAI rate limits](https://developers.openai.com/api/docs/guides/rate-limits).

API data không dùng train theo mặc định trừ opt-in. Retention tùy endpoint và thiết lập: abuse logs thường tối đa 30 ngày; Responses có state mặc định cần xem `store`; bảng hiện ghi audio transcriptions không giữ abuse/application state, còn Files tồn tại đến khi xóa theo chính sách. Không áp một endpoint cho mọi workflow; ZDR có điều kiện và không tự bật bằng `store:false`. [Data controls](https://developers.openai.com/api/docs/guides/your-data).

Với ràng buộc hiện tại, OpenAI chỉ có thể là adapter tùy chọn trong tương lai. Chưa có ngân sách/credit được xác nhận → **không chạy cloud PoC OpenAI**, không đổi A–G.

## 4. Cách ước tính chi phí

Với text-only, không tool/cache: `cost = inputTokens / 1e6 × inputRate + billedOutputTokens / 1e6 × outputRate`. Tính cả retry và thinking nếu model tính phí; không dùng số từ hoặc ký tự thay token usage thực.

Ví dụ giả định 1.000 input và 300 billed output tokens/lần: Gemini paid rate nêu trên ≈ **$0.00105/lần**, 100 lần ≈ **$0.105**; OpenAI ví dụ ≈ **$0.005/lần**, 100 lần ≈ **$0.50**. Chưa gồm thuế, tỷ giá, tool, audio hoặc request lỗi có usage. Free Tier chỉ $0 khi đúng tier/model/quota, không phải lời hứa usage vô hạn. [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing), [OpenAI pricing](https://developers.openai.com/api/docs/pricing).

## 5. Consent và hợp đồng provider đề xuất

- Provider capability tách `transcribe`, `align`, `suggestCaption`, `suggestStyle`; unsupported phải trả rõ, không giả lập thành công. Interface Core không đồng nghĩa phải triển khai mọi adapter trong Core.
- Trước gửi: hiển thị provider/model, dữ liệu text/audio sẽ gửi, mục đích, data-use đã tra cứu; consent có phạm vi và có thể thu hồi. Dữ liệu khác hoặc provider khác cần consent mới.
- Backend giữ key; frontend không nhận key. Log request ID, duration, usage và error code; không log payload/token/key. Chính sách lưu output chờ phê duyệt.
- Timeout/retry hữu hạn, backoff có jitter, không retry lỗi credential/consent; deduplicate thao tác user, giới hạn output. Khi hết quota thì manual/local fallback.
- Quota/credit cap phía provider và kiểm soát app đều cần xem xét; không coi cảnh báo ngân sách là bảo đảm hard cap. Ngân sách hiện tại **0 đồng**, cloud mặc định tắt.

## 6. Những điều chưa xác minh và cổng phê duyệt

| Mục | Trạng thái / điều kiện cần |
|---|---|
| ASR/alignment hát Việt/Anh và instrumental | Not run; POC-01/02, không thay bằng benchmark speech upstream |
| License aligner Việt | Model card ghi CC BY-NC 4.0; cần xem mục đích sử dụng và attribution, chưa duyệt sử dụng |
| Model availability, limits, region, billing của hai provider | Chưa truy cập dashboard; phải xác minh lại trước bất kỳ request nào |
| Gemini đủ miễn phí và phù hợp privacy/terms | Chưa xác nhận; AI-01/06 vẫn mở |
| OpenAI có credit khả dụng | Chưa xác nhận; AI-02 vẫn mở, không giả định có |
| Chất lượng caption/style, latency, refusal/429 behavior | Not run; POC-06 optional sau explicit opt-in |

TD-06 đề nghị **giữ cả hai cloud provider tắt**, chỉ cho thử Gemini text tổng hợp khi user phê duyệt riêng. Tài liệu này không cấp quyền gửi media hoặc thay đổi ngân sách.
