# Cấu hình AI local

Ngày 24/11/2026. Backend chạy worker riêng, CPU INT8 cho ASR; không import PoC.
Models không nằm trong Git. App không tải model tự động và không gửi lời/media tới AI cloud.

## Máy đã chuẩn bị

Mặc định tái sử dụng environment/model local hiện có ở `.poc/venv-asr`,
`.poc/venv-align`, `.poc/models`. Đây là reuse binaries/models, không import PoC code.
Đổi vị trí bằng biến môi trường trước khi chạy launcher:

```powershell
$env:AMVS_ASR_PYTHON = 'D:/AI/asr-env/Scripts/python.exe'
$env:AMVS_ALIGN_PYTHON = 'D:/AI/align-env/Scripts/python.exe'
$env:AMVS_MODEL_ROOT = 'D:/AI/models'
./scripts/start.ps1
```

ASR environment hiện có faster-whisper 1.2.1/av 16.0.1; model directories
`faster-whisper-small` hoặc `faster-whisper-medium`, chuẩn CTranslate2 gồm model.bin,
config/tokenizer/vocabulary. Không mặc định gọi model id online để tải thiếu file.
Align environment hiện có CPU torch/torchaudio 2.8.0, WhisperX 3.8.6 và transformers
4.57.3. `align-vi` dùng architecture đã review/hash pin theo discovery; thay source
hash bị từ chối. `align-en` là model local tương ứng. Tokenizer NLTK được chuẩn bị
ở `.poc/cache/nltk`; thiếu tokenizer không tự download.

Cài mới môi trường/model cần lưu revision/license/hash và kiểm offline trước khi
công bố hỗ trợ. Các thông số trên mô tả máy hiện tại, không phải chứng nhận clean
setup AI trên máy khác; xem requirements/discovery cho inventory đã kiểm.

## Sử dụng

Chọn clip nhạc → ngôn ngữ/model → Nhận dạng trên máy, hoặc nhập LRC/SRT/thêm câu
có mốc nguồn rồi Căn từ local. Mốc luôn theo bài hát nguồn, không theo video sau trim.
Không có cue windows thì cần đặt mốc câu trước; không chia đều chữ để giả alignment.

Kết quả là draft. Sửa lời/mốc, dùng **Lưu bản nháp lời vào project** nếu cần giữ qua
mở lại, rồi lưu project thủ công. Duyệt từng câu và **Áp dụng lời đã duyệt** để lên
preview/timeline. Đổi chữ/mốc làm bỏ words cũ và yêu cầu duyệt lại trong panel.
Job không ghi đè editor; bản ASR gốc có thể mở lại từ danh sách bản nháp.

RAM admission giữ 4 GiB/10 samples; dưới ngưỡng job chờ và có thể hủy. Missing model
trả AI_UNAVAILABLE. Gemini/OpenAI chỉ disabled adapter trong Core, không có network
implementation, không phát sinh phí API. Drive OAuth là lưu trữ riêng.

Chất lượng hát và timing chưa nghiệm thu. Word scores/cutoff 0,25 là screening thô,
không phải xác suất đúng hoặc timing accuracy. Nhạc không giọng/không rõ có thể trả
không có lời; luôn cần review. Xem S2_S6_RESULTS.md để biết phần test thật chưa chạy.
