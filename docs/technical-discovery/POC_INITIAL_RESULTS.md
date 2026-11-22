# Initial PoC Results — Local ASR and Rendering

Ngày thực hiện: **22/11/2026 (Asia/Saigon)**. Phạm vi: environment readiness, executable smoke và **một mẫu hát Việt exploratory**. Chưa hoàn thành bộ PoC, chưa nghiệm thu ứng dụng và chưa phê duyệt ADR/stack chính thức.

**Cập nhật sau báo cáo ban đầu:** user đã gửi SRT lời gốc. Đã đo text error trên reference đó; xem [LYRICS_INPUT_WORKFLOW.md](LYRICS_INPUT_WORKFLOW.md). Các đoạn “chưa có ground truth” bên dưới ghi trạng thái lúc chạy smoke ban đầu; chưa có word timing gold hoặc timing reference được kiểm chứng độc lập.

**Cập nhật rendering:** đã hoàn tất ma trận 36 preset; xem
[RENDER_MATRIX_RESULTS.md](RENDER_MATRIX_RESULTS.md). Các ghi chú “chưa chạy matrix”
bên dưới là trạng thái lịch sử của smoke ba file, không phải trạng thái hiện tại.

## 1. Môi trường đã thực thi

| Thành phần | Thực tế |
|---|---|
| OS | Windows 11 Home Single Language, build 26300 |
| CPU | Intel Core i7-13620H, 16 logical CPUs được Python báo |
| RAM | 16,857,817,088 bytes hệ điều hành nhìn thấy, khoảng 15.70 GiB |
| Python | 3.12.6, venv riêng `.poc/venv-asr/` |
| ASR | faster-whisper 1.2.1, CTranslate2 4.9.1, CPU INT8, 4 threads, beam 5 |
| Model | `Systran/faster-whisper-small`, multilingual; revision `536b0662742c02347bc0e980a01041f333bce120` |
| Decode | PyAV **16.0.1**; xem lỗi tương thích bên dưới |
| Standalone FFmpeg | imageio-ffmpeg 0.8.1 cung cấp FFmpeg 9.0.2; tách khỏi wrapper global |
| Rendering | Node 24.14.1, Remotion 4.0.545, React/React DOM 19.3.1 |
| Browser | Chrome Headless Shell 158.0.8127.2, binary local |
| Encode | H.264/AAC, hardware encoding disabled, concurrency 1 |

Model/dependencies/browser được tải về để chạy local; không gọi cloud inference hoặc upload audio. ASR dùng local_files_only và Hugging Face offline flags; chưa có kiểm thử network isolation độc lập. Browser có thể dùng iGPU/software; chưa đo chế độ GPU render thực tế, không suy từ CPU encode thành “toàn bộ browser chỉ dùng CPU”.

Model files có SHA-256; package versions đầy đủ trong [asr-freeze.txt](../../.poc/evidence/poc-00/asr-freeze.txt), [environment.json](../../.poc/evidence/poc-00/environment.json), [model-inventory.json](../../.poc/evidence/poc-00/model-inventory.json). npm có package-lock riêng tại `poc/render/`.

## 2. Vấn đề tương thích đã phát hiện

1. `ffmpeg`/`ffprobe` global trỏ tới wrapper Panda3D và không chạy được trong phép thử ban đầu. Không sửa Python global; dùng binary riêng từ imageio-ffmpeg và ffprobe trong Remotion.
2. Resolver ban đầu chọn PyAV 19.0.2, trong khi faster-whisper 1.2.1 gọi `av.open(..., metadata_errors=...)`; PyAV đó báo `TypeError`. Pin `av==16.0.1` trong venv riêng khắc phục được lỗi decode trên các mẫu đã thử. Điều này không chứng minh mọi codec đều tương thích.
3. Lưu lỗi ban đầu tại [av19-compatibility-error.json](../../.poc/evidence/poc-01/av19-compatibility-error.json); không che lỗi bằng input giả lập.

`pip check`, Python compilation, Node syntax check và `npm ls --depth=0` đạt sau pin. Không có application code hoặc dependency global được thay đổi.

## 3. Negative-control executable smoke

Tự tạo 3 WAV mono 16kHz × 20s: silence, sine tone và seeded noise. Mỗi mẫu chạy tiếng Việt/Anh, VAD on/off: **12 lượt**.

- Cả 12 lượt hoàn tất, model load khoảng **1.03s** trong lần chạy này.
- **3/6 lượt VAD-off có text trên tín hiệu không lời**: silence Việt, silence Anh, noise Việt.
- **0/6 lượt VAD-on có text** trên ba tín hiệu này.
- Peak sampled process-tree private memory khoảng **3.37 GiB**; minimum system available khoảng **3.20 GiB**.

Đây không phải kiểm thử nhạc instrumental thật, không chứng minh VAD nhận biết giọng hát đúng, không phải kết quả WER/CER. Trong harness, mọi output được đánh dấu draft/review_required và không áp dụng vào project; chưa có editor để nghiệm thu review workflow sản phẩm.

Bằng chứng: [generated-smoke/results.json](../../.poc/evidence/poc-01/generated-smoke/results.json).

## 4. Mẫu hát Việt người dùng cung cấp

Sample ID **vi-001**, AAC stereo 44.1kHz, **296.681361s**, 9,549,146 bytes. Bản gốc được copy vào vùng local riêng; không chỉnh/xóa file nguồn ở Downloads. Hash và provenance ở [manifest](../../.poc/data/user/vi-001.manifest.json).

Mẫu được người dùng gửi trong ngữ cảnh đã đồng ý dùng dữ liệu có quyền cho mục đích cá nhân phi thương mại. Quyền không được kiểm chứng độc lập. Không nhập URL/downloader vào ứng dụng; toàn bộ inference chạy trên file local. Đây là **development/exploratory**, không phải held-out corpus.

| Cấu hình | Audio còn sau VAD | Đoạn ASR | Model load | Inference/decode | RTF theo toàn file | Peak private / min available |
|---|---:|---:|---:|---:|---:|---:|
| VAD on | 29.632s | 9 | 0.91s | 7.51s | 0.0253 | 2.98 / 2.70 GiB |
| VAD off | Không cắt bởi VAD | 67 | 0.95s | 49.89s | 0.1681 | 2.98 / 2.67 GiB |

VAD giữ khoảng 10% thời lượng để nhận dạng, nên RTF thấp của lượt VAD-on không thể dùng làm kết luận chất lượng/tốc độ xử lý đầy đủ bài hát. Các mốc trả về được map về source time, có thể bao qua khoảng bị loại; số đoạn và thời lượng segment không phải số giây hát đúng. Cần review các đoạn bị bỏ qua. VAD-off tạo nhiều đoạn hơn nhưng chưa chứng minh đúng hơn, vẫn có thể hallucinate/lặp/mất lời.

Không phát hiện segment ngoài range hoặc timestamp overlap qua kiểm tra cấu trúc ở cả hai run. Điều đó **không chứng minh đồng bộ câu/từ chính xác**. Word timestamps chưa tạo, forced alignment chưa chạy.

Bản để rà soát:

- VAD-off: [draft.txt](../../.poc/evidence/poc-01/vi-001-no-vad/draft.txt), [draft.srt](../../.poc/evidence/poc-01/vi-001-no-vad/draft.srt), [transcript.json](../../.poc/evidence/poc-01/vi-001-no-vad/transcript.json).
- VAD-on đối chứng: [draft.txt](../../.poc/evidence/poc-01/vi-001/draft.txt), [draft.srt](../../.poc/evidence/poc-01/vi-001/draft.srt).

**WER/CER, correction time, word/sentence MAE/P95: chưa đo** vì không có ground truth đã review. Không lấy chính output ASR làm ground truth. Mới có một bài Việt, chưa có mẫu Anh, chưa đủ phân tầng thể loại/held-out. Chưa chọn mặc định VAD hoặc phê duyệt model từ kết quả này.

## 5. Rendering executable smoke

Ba fixture tự tạo: TPL-01 ảnh/caption/audio; TPL-02 một artwork/Music Card/progress/audio; TPL-03 video test pattern/lyric highlight minh họa/audio. TPL-02 chưa thử đầy đủ hai ảnh như template sản phẩm. Highlight dựa trên thời gian fixture định trước, **không phải AI alignment**.

| Fixture | Output | Render wall time | RTF |
|---|---|---:|---:|
| TPL-01 | 15s, 720×1280, 30FPS, H.264/AAC | 40.51s | 2.70 |
| TPL-02 | Như trên | 34.68s | 2.31 |
| TPL-03 | Như trên | 55.87s | 3.72 |

Các thời gian trên là **một lượt đo**, bao gồm renderMedia, không gồm bundle/browser setup/renderStill; không là median hoặc SLA. Tổng supervisor wall time khoảng 168.36s gồm các phần setup và still. Sampling mỗi giây ghi peak private workload **1.26 GiB**, min system available **2.81 GiB**; không vượt điều kiện dừng ở run này. Các peak ngắn có thể bị sampling bỏ sót.

Validation:

- **3/3 output** có đúng width/height/FPS/codecs/duration; decode đủ **450 frames/file** và decode audio bằng PyAV; lưu ffprobe JSON độc lập.
- Flash/click tổng hợp tại 0/5/10s có marker delta khoảng **0.04ms** theo phép đo sample/timestamp. Kết quả chỉ áp dụng fixture này, không phải độ chính xác ASR, lyrics thật, preview hoặc cảm nhận người dùng.
- Đã xem PNG đại diện của TPL-02/03; dấu Việt hiển thị ở các ảnh đó. Chưa font audit đầy đủ hoặc kiểm tra pixel/seek/fidelity preview.
- Chưa chạy 36-case matrix, 1080p60, 300s stress, cancel/retry, interactive Player hoặc so preview/export 20 mốc/project. Không tuyên bố R1/R2/R3 toàn bộ đạt.

Bằng chứng: [render-results.json](../../.poc/evidence/poc-03/render-results.json), [validation.json](../../.poc/evidence/poc-03/validation.json), [resources.json](../../.poc/evidence/poc-03/initial-resources/resources.json).

Outputs: [TPL-01 MP4](../../.poc/evidence/poc-03/TPL01-9-16-720x1280-30.mp4), [TPL-02 MP4](../../.poc/evidence/poc-03/TPL02-9-16-720x1280-30.mp4), [TPL-03 MP4](../../.poc/evidence/poc-03/TPL03-9-16-720x1280-30.mp4).

## 6. Kết luận gate và bước tiếp

**Executable smoke đạt trong phạm vi các lượt trên**: môi trường local chạy được ASR CPU và render ba MP4 thực. Chất lượng lyrics, forced alignment, full render matrix, editor và storage/Drive vẫn **chưa đủ bằng chứng Go/No-Go**. Không đánh FR Verified trong RTM.

Ưu tiên tiếp theo: user review TXT/SRT Việt và cung cấp bản lời đúng/timestamp nếu có; bổ sung mẫu Anh có quyền dùng. Sau đó mở rộng corpus và kiểm alignment trên text đã duyệt. Tiếp tục rendering matrix/stress và storage theo POC_PLAN; cloud không thực hiện. Không yêu cầu duyệt lại kế hoạch đã được chấp thuận, nhưng cần dữ liệu/ground truth còn thiếu cho quality gates.

Trạng thái Git: `dev`, thay đổi chưa commit/push; media/model/raw results dưới `.poc/` và node_modules được ignore. Scripts `poc/` là harness thí nghiệm, không phải ứng dụng chính thức.
