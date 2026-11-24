# MVP Domain, Storage and API Contracts

Ngày: **23/11/2026**. Status: **Accepted** theo xác nhận “duyệt theo đề xuất”, cùng
[ADR-0001](../decisions/ADR-0001-LOCAL_MVP_ARCHITECTURE.md). Đây là design contract,
đã có triển khai một phần; trạng thái/evidence xem [S2–S6](../planning/S2_S6_RESULTS.md).
Các fields/API dưới đây vẫn là contract mục tiêu, không mặc định toàn bộ đã nghiệm thu.

Ghi chú triển khai 24/11: schema v1 bổ sung optional `sourceAudioItemId` để remap
lyrics theo clip nhạc, `role` cho metadata Music Card khi clone với IDs mới, cùng
style fields cơ bản. Dữ liệu cũ vẫn đọc được. Editor lease chỉ ở memory, heartbeat
5s/expiry 30s; tab khác chỉ đọc/takeover rõ ràng. Portable có manifest.json,
project.json và assets; source GC có preview/chọn/xác nhận, xét pins của working,
manual, legacy, recovery, template, job và lịch sử phiên. Manual/legacy pins giữ
bảo thủ, không tự thu hồi. Cache quota chỉ áp dụng generated thumbnails, không
xóa source để đạt quota. ASR/alignment local và 36 preset outputs đã chạy thật;
quality/listening và acceptance đầy đủ vẫn theo báo cáo S2–S6.

## 1. Versioning và timeline canonical

Project schema ứng dụng `amvs-project/1`, template `amvs-template/1`; không reuse
`poc-fidelity-1` như production contract. Unknown newer version bị từ chối, giữ
file gốc. Migration chạy trên copy, có backup/test trước cập nhật DB user_version.

| Entity | Trường và bất biến chính |
|---|---|
| Project content | id, name, schemaVersion, timebase=48000, durationTicks, preset, templateRef, orderedTracks, items, lyrics, assetRefs |
| Project view | playheadTicks, timelineZoom, selection, panels; restore khi hợp lệ, không đưa vào content dirty hash |
| Track | id, kind background/music/lyrics/text, order; nhiều tracks cùng loại, không hardcode tổng số |
| Item | id, trackId, startTicks, durationTicks, assetId hoặc text/lyric ref, sourceStartTicks, speed numerator/denominator, transform/style/effects |
| Asset | id/hash, managed relative location, bytes, verified MIME/codec, duration/timebase, dimensions, provenance; absolute paths chỉ backend |
| Lyrics | original source ticks, sentence/word units, source=user/import/asr/aligner, draft/reviewed, alignmentStatus và raw score provenance |
| Template | immutable id/version, default project content, typed slots/item refs, required/optional; instance copy có IDs mới |

Mọi tick là integer an toàn JSON, không NaN/Infinity; project duration ≤14,400,000
ticks (300s). Interval `[start, start+duration)`; positive duration, item thuộc
project, source window nằm trong asset, reference IDs phải tồn tại. Thứ tự tracks
quyết định layer; item order phá hòa trong track; không giữ thêm z-order mâu thuẫn.

Frame time = `frameIndex * 48000 / fps`: 30FPS=1600 ticks, 60FPS=800 ticks. Adapter
lấy vị trí frame tuyệt đối, không cộng delta/rounding tích lũy. Audio/ASR seconds
đổi một lần về ticks theo nearest; source PTS luôn chuyển qua rational timebase.
Tick storage không làm model hoặc source media chính xác đến mức tick.

Source time tại timeline tick t: `sourceStart + (t-start)*speedNum/speedDen`.
Cắt lyrics theo source interval đã chọn rồi map sang timeline; renderer và Player
dùng cùng adapter/rounding/clipping. Style edits không làm đổi timestamps. Có lời
text-only không đồng nghĩa có cue windows để align; thất bại cần user chỉnh câu,
không chia đều chữ rồi gắn nhãn word-aligned. Đơn vị highlight Việt có thể là
whitespace units; UI không gọi đó là từ ngữ nghĩa hoặc accuracy đã xác nhận.

## 2. Revision, history và manual save

- `workingRevision` tăng sau successful optimistic commit. Update mang expected
  revision; mismatch trả conflict, không last-write-wins. Một project editor write
  session; tab thứ hai read-only hoặc takeover rõ ràng, chưa có collaboration.
- `contentHash` = SHA-256 của content theo JCS; loại view state, revision, timestamps,
  paths và job progress. Giữ nguyên Unicode text user; normalization để đo WER là
  thao tác riêng. JS/Python golden vectors phải cho cùng bytes/hash. [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785).
- Dirty = current content hash khác `manualSavedHash`. Undo về đúng nội dung đã
  save làm sạch dù working revision khác. Autosave working DB không clear dirty.
- History command batch một drag/trim thành một thao tác; edit sai rollback toàn
  bộ, edit sau undo clear redo. Cách lưu history được chọn qua latency benchmark,
  không copy full snapshots vô hạn từ harness; undo history xuyên restart chưa
  thuộc cam kết save/reopen, nhưng content/view hợp lệ phải restore.
- Manual save snapshot B: pin assets → stage JSON checkpoint cùng volume với đích
  → flush/validate → publish → xác nhận đúng hash B. Nếu user đã sửa C, vẫn dirty.
  Nếu DB bookkeeping fail sau publish, báo lỗi/dirty bảo thủ, đối chiếu checkpoint
  khi mở; không khẳng định DB/file là một transaction chung.
- Recovery riêng mỗi 30s khi có thay đổi; candidate cap 10 snapshots hoặc 200 MiB/
  project, chạm cap cảnh báo/tạm dừng và cho cleanup có xác nhận. Không tự xóa bản
  manual/source/shared asset. Restore cần user chọn, chỉ cập nhật working copy.

## 3. Storage, portable và technical budgets

```text
<workspace>/runtime/              SQLite + migration/job journal, không sync
<workspace>/library/assets/       immutable managed copies theo hash
<workspace>/recovery/<project>/   recovery snapshots
<workspace>/jobs/<job>/           pinned snapshot, staging, logs đã lọc
<workspace>/cache/                proxies/thumbnails/waveform, tái tạo được
<chosen-project-folder>/          manual checkpoint JSON + asset inventory
<chosen-backup-folder>/*.amvs     closed portable ZIP snapshot
<chosen-export-folder>/*.mp4      output đã validate
```

Manual checkpoint phụ thuộc library local; UI phải phân biệt với **portable**.
`.amvs` đề xuất ZIP_STORED/ZIP64 khi cần: `manifest.json`, `project.json`, chỉ các
`assets/<hash>.<ext>` được tham chiếu và fonts có quyền phân phối; checksums/size/
MIME/schemaVersion đầy đủ. Restore vào staging mới, verify trước publish, không
overwrite destination hoặc thực thi JS/template code nhập. Checksum không là chữ
ký/xác thực tác giả. Không dùng giới hạn 16/64 MiB của harness cho project thật.

Budgets khởi điểm **đề xuất để S0/S4 đo và công bố**, không phải năng lực đã chứng
minh: import ≤2 GiB/file, portable tổng expanded ≤8 GiB, ≤4096 members, JSON ≤16
MiB, manifest ≤4 MiB, ratio ≤200. Stream/hash theo chunks; không đọc cả media vào
RAM. File/codec không hỗ trợ bị từ chối với lỗi Việt, giữ source. S0 probe input
JPEG/PNG, MP4 H.264/AAC, MP3/M4A/WAV trước công bố support list; VFR là case riêng.
Giới hạn thay đổi cần evidence và UI cập nhật, không ngầm loại yêu cầu video/media.

Preflight disk tính source copies + staging/package + temp + output, reserve
candidate max(2 GiB, 10% estimated bytes). Không đủ thì báo và giữ bản save cũ.
GC xét working/manual/recovery/template/job pins, preview danh sách + consent.
Package Drive tạo/verify local trước copy immutable; chỉ báo local-ready cho tới
khi sync-download-restore đã xác minh. Không sync runtime/WAL/temp hoặc merge
hai revision cùng ID tự động.

## 4. Jobs và AI

Job có id, kind, snapshotId/hash, asset pins, phase, progress, output IDs, error,
cancelRequested và timestamps. Lifecycle:

```text
queued → preparing → running → finalizing → validating → succeeded
queued → cancelled
active → cancelling → cancelled
active → failed / interrupted
```

Admission chưa đạt: giữ queued/waiting-resources, giải thích và cho cancel; không
spawn child. Retry là job/attempt mới, giữ evidence cũ. Progress theo phase, không
100% trước validate/publish; cancel/kill owned tree, không kill process không sở
hữu. Render uses only pinned snapshot; edits tiếp theo không đổi output job.
Một heavy slot cho AI/render; không block API requests/preview. R0 monitor vẫn
chạy sau admission, không xem exit 0 thay cho resource/quality verdict.

Provider request gồm assetId, language, selected source range, optional approved
lyrics và cancellation. Output draft kèm provenance/raw scores, không gọi score
chưa hiệu chuẩn là xác suất đúng. Local ASR khi không có lời, alignment có/fallback
câu khi có lời; instrumental/no-vocal/ambiguous phải hiện trạng thái có thể sửa,
không auto publish lyrics. User duyệt text/timing trước dùng trong composition.
Provider interface có disabled/cloud state; không egress khi chưa có opt-in mới.

## 5. API boundary đề xuất

Prefix `/api/v1`, JSON DTO có schemaVersion khi là persisted content. Session,
Origin/Host và folder capability theo ADR; URLs asset/job chỉ ID. Request không
được kèm arbitrary backend paths hoặc subprocess args. Read media có range bounds.

| Endpoint group | Hành vi |
|---|---|
| `GET /session`, `GET /health` | Session capabilities; health không lộ paths/token |
| `POST /folder-grants`, `DELETE /folder-grants/{id}` | Mở native chooser hoặc revoke opaque scope; cancel không cấp grant |
| `POST /assets`, `GET /assets`, `GET /assets/{id}/content` | Streaming import, catalog/search, authorized media reads |
| `POST /projects`, `GET/PATCH /projects/{id}` | Tạo/load/update optimistic working revision; DELETE bỏ project refs |
| `POST /projects/{id}/save` | Checkpoint revision được chỉ định qua folder grant; trả savedHash |
| `GET /projects/{id}/recoveries`, `POST /projects/{id}/restore` | List metadata; chọn recovery có confirmation và revision check |
| `POST /projects/{id}/packages`, `POST /package-imports` | Export immutable package/restore staged; scope grant và validation |
| `GET/POST /templates`, `POST /templates/{id}/instances` | Immutable version/typed bindings/new project IDs |
| `POST /jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/cancel` | ASR/alignment/render/package job, status polling ~1s, cancellation |
| `GET /outputs/{id}`, `POST /outputs/{id}/open-folder` | Validated output/authorized folder open, không nhận path từ client |

Tác vụ dài trả 202 + job ID; không trả success khi mới queued. Lỗi có
`code/message/fieldErrors?/requestId`, không stacktrace/absolute path; 401 session,
403 capability/origin, 409 revision, 413 budget, 422 schema/media, 507 thiếu disk.
Grant/session hết hạn phải chọn lại, không persist capability token trong project.
Native chooser và OS-folder-open chạy fixed scripts/argv; không shell ghép user input.

## 6. Acceptance trước khi dùng contracts cho feature

S0: schema parity/hash vectors gồm Unicode/float boundaries, duplicate keys,
unknown version, dangling IDs, time clipping/rounding/source bounds. Test forged
grant/origin/path và native chooser Unicode/cancel. S1–S6 thêm save B/edit C race,
crash/pins/recovery, template instance independence và Player/export fidelity.
Các defaults đã được PO duyệt cùng ADR ngày 23/11/2026. Phát hiện khác biệt kiến
trúc phải báo để cập nhật quyết định; triển khai Accepted design không đồng nghĩa
mọi acceptance case đã có evidence.
