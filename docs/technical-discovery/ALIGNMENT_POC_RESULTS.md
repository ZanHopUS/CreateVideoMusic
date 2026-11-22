# Forced Alignment PoC — Việt và Anh

Ngày thực hiện: **22/11/2026 (Asia/Saigon)**. Trạng thái: **đã triển khai và chạy harness local trên hai reference SRT**; chưa nghiệm thu chất lượng timing hoặc ứng dụng chính thức. Không commit/push lượt này.

**Cập nhật sau báo cáo alignment:** user đã xác nhận “đạt” cho preview Việt 33.9s, cues 3–9, gồm word mode và một câu fallback. Xem [VIETNAMESE_LYRICS_PREVIEW.md](VIETNAMESE_LYRICS_PREVIEW.md). Nghiệm thu định tính này không bao phủ toàn bài hoặc thay thế word-boundary annotations/MAE/P95 còn thiếu.

## 1. Đầu ra và giới hạn phạm vi

Đã có pipeline thử nghiệm CPU: audio local + SRT user cung cấp → alignment từng cue → kiểm tra word timing → word draft hoặc sentence fallback → JSON/SRT/TSV để review.

Mẫu Việt dùng đủ **68 cues**, audio **296.681375s** sau decode. Mẫu Anh dùng **102 cues có lời**, loại riêng **9 cue mô tả âm thanh** trong tổng 111 cues; xử lý **300s đầu** của audio 301.418231s. Không sửa các file gốc ở Downloads.

Đây là alignment **trong cửa sổ thời gian SRT đã có**. Chưa chứng minh alignment text-only trên toàn bài không có cue windows, chưa cải thiện ASR audio-only, chưa có editor hoặc release E2E. Các đoạn trong ngoặc ở bài Việt là lời backing và được giữ; không tự xóa mọi nội dung có ngoặc.

## 2. Môi trường và provenance

- Venv riêng `.poc/venv-align/`; giữ nguyên venv ASR cũ.
- WhisperX **3.8.6**, Transformers **4.57.3**, torch/torchaudio **2.8.0+cpu**, torchvision **0.23.0+cpu**; PyAV **16.0.1**. Resolved environment có pandas 3.1.1, NLTK 3.10.4; đầy đủ tại [align-freeze.txt](../../.poc/evidence/poc-00/align-freeze.txt).
- CPU inference, 4 torch threads, một model/một bài tại một thời điểm; không có CUDA build, không gọi cloud inference.
- Decode bản làm việc mono PCM16 16kHz; clip amplitude về [-1,1] khi ghi PCM16, cap 300s. Lưu SHA-256 audio gốc, WAV và reference SRT trong từng report.
- Model Việt: `nguyenvulebinh/wav2vec2-base-vi-vlsp2020`, revision `50a30dadb3ec98a0d4cdb1eb1ea315aff538f7c2`, CC BY-NC 4.0 theo phạm vi cá nhân phi thương mại đã duyệt.
- Model Anh: `facebook/wav2vec2-base-960h`, revision `22aad52d435eb6dbaf354bdad9b0da84ce7d6156`, Apache 2.0.

Model, source handler và config/tokenizer được chuẩn bị trước, khóa revision/checksum. Inference dùng local files/offline flags; NLTK data nằm trong `.poc/` và implicit download bị chặn. Chưa có kiểm thử firewall/network isolation độc lập.

Sources: [model Việt](https://huggingface.co/nguyenvulebinh/wav2vec2-base-vi-vlsp2020), [model Anh](https://huggingface.co/facebook/wav2vec2-base-960h), [WhisperX 3.8.6 alignment](https://github.com/m-bain/whisperX/blob/v3.8.6/whisperx/alignment.py).

## 3. Lỗi tương thích đã tìm và sửa ở model Việt

Loader Hugging Face chung của WhisperX dùng lớp `Wav2Vec2ForCTC` tiêu chuẩn. Checkpoint Việt có thêm **`feature_transform` gồm các lớp linear/batch norm**, nằm trong forward path của model tác giả. Loader chung cảnh báo bỏ qua toàn bộ weight của tầng này; trên bài Việt, nó cho **0/555 units** vượt kiểm tra word draft và fallback cả 68 câu.

Hướng dẫn tác giả yêu cầu lớp trong `model_handling.py`. Đã đọc toàn bộ module trước khi dùng; harness tải source đúng revision vào vùng private và kiểm **SHA-256 `ed4178006be431a3f5b51558ec36e3e3557d51dd83e181d5c0d91c312537f83b` trước thực thi**. Không bật automatic remote-code loading. Loader từ chối bất kỳ missing/unexpected/mismatched weight hoặc error nào, rồi đặt model ở eval mode. Run thực tế ghi cả bốn danh sách loading errors đều rỗng.

Đây là sửa cách nạp checkpoint cho khớp architecture, không phải chọn một kiến trúc ứng dụng mới hoặc hạ ngưỡng điểm. Nguồn gốc và forward path: [README tác giả](https://huggingface.co/nguyenvulebinh/wav2vec2-base-vi-vlsp2020/blob/50a30dadb3ec98a0d4cdb1eb1ea315aff538f7c2/README.md), [model_handling.py](https://huggingface.co/nguyenvulebinh/wav2vec2-base-vi-vlsp2020/blob/50a30dadb3ec98a0d4cdb1eb1ea315aff538f7c2/model_handling.py).

Giữ baseline loader chung ở [vi-001-standard/alignment.json](../../.poc/evidence/poc-02/vi-001-standard/alignment.json). Smoke dùng author loader cho ba cue đầu đạt word draft 3/3 trước khi chạy full; không trộn smoke với kết quả full.

## 4. Quy tắc word draft và fallback

- Gọi WhisperX với **`interpolate_method="ignore"`**, không tự lấp timing thiếu bằng nội suy.
- Một unit có chữ/số chỉ được tính là đạt sàng lọc khi có start/end/score hữu hạn, duration dương, nằm trong cue (tolerance 20ms), không chồng bất hợp lý và score **≥0.25**.
- **0.25 là cutoff kỹ thuật chưa hiệu chuẩn**, không là xác suất đúng hoặc acceptance accuracy đã phê duyệt.
- Chỉ dùng word draft cho cả câu nếu đủ mọi unit theo đúng thứ tự text. Nếu thiếu/sai/score thấp: fallback cả câu về **timing SRT user cung cấp, vẫn cần review**; không chia đều thành từ.
- Bỏ pure-symbol tokens khỏi phép đếm, giữ nguyên lời user trong reference. Units ở đây là whitespace units của text trước normalization điểm ASR; không đồng nhất với denominator WER đã xử lý punctuation/contractions.
- Mọi JSON/TSV và draft đều `review_required=True`; không tự ghi đè reference hoặc coi câu đạt sàng lọc là đã nghe kiểm chứng.

## 5. Kết quả thực tế

| Candidate/run | Units đủ kiểm tra | Coverage sàng lọc | Câu word draft | Câu fallback | Load model | Alignment |
|---|---:|---:|---:|---:|---:|---:|
| Việt / loader chung, đối chứng | 0/555 | 0.00% | 0/68 | 68 | 10.14s | 82.11s |
| Việt / author loader | **544/555** | **98.02%** | **59/68** | **9** | 14.69s | 84.45s |
| Anh / HF standard | **310/510** | **60.78%** | **17/102** | **85** | 11.20s | 104.44s |

Không có API exception ở các cue full runs. Coverage tính cả unit đạt trong câu phải fallback vì một unit khác không đạt; vì vậy không đồng nghĩa 98.02% nội dung đã được xuất dưới dạng word events. Hybrid SRT Việt có **483 events**, Anh **146 events**; mỗi fallback cue là một event câu.

Đây là một run/candidate trên development data, chưa là median cold/warm hoặc đánh giá held-out. Alignment time gồm vòng lặp align và ghi partial evidence, không gồm import/load model.

| Run full | Peak private process tree (sampled) | Min system available RAM | Dừng do tài nguyên |
|---|---:|---:|---|
| Việt / author loader | 2.25 GiB | 4.70 GiB | Không |
| Anh / HF standard | 2.20 GiB | 4.72 GiB | Không |

RAM available ban đầu chỉ khoảng 2.1 GiB; user đóng bớt ứng dụng trước các run. Preflight yêu cầu ≥3.25 GiB available; supervisor giữ ngưỡng dừng <2 GiB liên tục 10s hoặc workload private >12 GiB. Sampling mỗi giây có thể bỏ sót peak ngắn; không suy kết quả này sang chạy ASR/render cùng lúc.

Model Anh có cảnh báo `wav2vec2.masked_spec_embed` được khởi tạo mới. Đã giữ log; theo source Transformers đang dùng, tensor này được dùng khi có mask indices hoặc SpecAugment training. Harness đặt eval mode và không truyền mask indices, nên tensor đó không nằm trên nhánh inference hiện tại. Không coi cảnh báo này tương đương việc bỏ tầng forward `feature_transform` ở model Việt. [Wav2Vec2 implementation v4.57.3](https://github.com/huggingface/transformers/blob/v4.57.3/src/transformers/models/wav2vec2/modeling_wav2vec2.py).

## 6. Kiểm chứng đã làm và chưa làm

Đã đạt:

- `pip check`, CPU import torch/torchaudio/WhisperX, Python syntax compilation.
- Regression policy: thiếu từ, score thấp, NaN, timestamp ngoài câu, sai chuỗi từ và pure-symbol tokens.
- Guard từ chối source model handler không đúng hash, trước thực thi.
- Full export validation: đủ 68/102 cue attempts, unique cue IDs, CPU build, reference hash khớp, JSON không NaN/Infinity, SRT parse được/đúng số events/không vượt audio và **0 overlap warning** trên hai exports.
- Author model Việt load đủ checkpoint weights; giữ baseline lỗi, smoke và full runs tách riêng.

Chưa làm: nghe/annotate từng từ độc lập, word/sentence MAE/P95, độ chính xác score, thử lại cả corpus/held-out, alignment text-only không cue windows, A/B waveform normalization hoặc model khác. SRT cue windows **ràng buộc sẵn vị trí** nên sự gần reference không thể thay bằng chứng timing accuracy. Không đánh FR Verified hoặc công bố đạt L2/L3 chỉ từ coverage.

## 7. Quyết định PoC và đầu ra để review

**Go trong phạm vi kỹ thuật:** local CPU pipeline chạy được, loader Việt đã sửa theo checkpoint, word draft/fallback và export có bằng chứng thực.

**Chưa Go cho tự động áp dụng highlight từng từ:** mẫu Việt cần kiểm timing bằng nghe; candidate Anh chỉ đạt 60.78% coverage sàng lọc nên chưa phù hợp tự động word mode trên mẫu này. Fallback theo cue vẫn dùng được để rà soát, nhưng timing đó đến từ SRT user, chưa chứng minh auto sentence alignment khi thiếu timing.

| Mẫu | SRT nháp | Bảng review | Chi tiết |
|---|---|---|---|
| Việt | [hybrid-draft.srt](../../.poc/evidence/poc-02/vi-001-author/hybrid-draft.srt) | [review.tsv](../../.poc/evidence/poc-02/vi-001-author/review.tsv) | [alignment.json](../../.poc/evidence/poc-02/vi-001-author/alignment.json) |
| Anh | [hybrid-draft.srt](../../.poc/evidence/poc-02/en-001/hybrid-draft.srt) | [review.tsv](../../.poc/evidence/poc-02/en-001/review.tsv) | [alignment.json](../../.poc/evidence/poc-02/en-001/alignment.json) |

Validation: [export-validation.json](../../.poc/evidence/poc-02/export-validation.json). Setup/run instructions: [alignment README](../../poc/alignment/README.md). Model/source inventories và media/raw results tiếp tục ở `.poc/`, Git-ignored.

Tiếp theo: nghe review các câu word draft và fallback, annotate subset độc lập để đo timing; điều tra preprocessing/model phù hợp hơn cho English singing. Nhánh ASR thiếu lời vẫn cần thử medium hoặc cải thiện tiền xử lý audio theo POC_PLAN; harness alignment này chưa sửa ASR. Không xây editor chính thức hoặc đổi A–G.

Commit đề xuất khi user phê duyệt: `test(lyrics): add CPU alignment with verified Vietnamese model loader`.
