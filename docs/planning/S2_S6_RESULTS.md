# S2–S6 — kết quả triển khai và nghiệm thu còn mở

Ngày **24/11/2026**, nhánh `dev`, baseline `65a6bef`. Người dùng giao tự lập kế
hoạch/triển khai tới S6, giải phóng RAM và xác nhận tiếp tục toàn bộ kiểm S6.
Không tự commit, push hoặc phát hành. [Kế hoạch](S2_S6_EXECUTION.md).
**Code S2–S5 đã tích hợp; S6 có evidence ứng dụng thật, chưa đóng Core/release.**

## Hành vi đã triển khai

| Mốc | Module và kết quả |
|---|---|
| S2 | `packages/domain`: LRC/SRT/manual lyrics, validation, review/draft, source-time trim/rate/clipping, history pins; `composition`: effects/typography/animation, word highlight và Music Card theo canonical track order; editor ba mẫu, 12 presets, nhiều typed tracks, zoom/playhead/view, Undo/Redo. |
| S3 | `services/local-api/amvs`: faster-whisper CPU INT8 và WhisperX offline qua environment/model đã chuẩn bị, không import PoC code. Local mặc định; Gemini/OpenAI disabled và không có network implementation. Render/ASR/alignment/package chung một heavy slot. Kết quả AI là draft tách riêng, không tự sửa timeline; thiếu alignment thì fallback cấp câu. |
| S4 | Recovery 30s riêng manual save, cap 10 bản/200 MiB, checksum/revision/consent; ZIP `.amvs` có manifest/project/assets và validation budgets/path/version/hash/probe; relink cùng SHA; preserve manual dirty/hash khi restore portable/Drive; editor lease 5s/expiry 30s/takeover, server fences stale writer. Disk preflight, cache quota, temp/source cleanup có preview/consent, validate output trước atomic publish. |
| S5 | Catalog tên/tags/thumbnail/listen/reuse; immutable personal templates có typed slots và instance IDs mới; energy suggestions bằng PyAV + standard library, người dùng nghe/chọn; Drive snapshot/restore có templates, media SHA dedup và không overwrite project đang sửa. |
| S6 | Regression/API/browser, real render matrix, VFR, local AI, preview/MP4 comparison, native picker, Drive cloud; runner 300s/contention/CPU/private/RAM. Mỗi evidence ghi rõ phạm vi và phần chưa nghiệm thu. |

Không thêm dependency. Schema v1 thêm optional `sourceAudioItemId`, metadata `role`
và style fields; fixture hash cũ giữ nguyên, project cũ vẫn đọc được. Preview/export
dùng chung scene, chuẩn hóa CSS inheritance để không phụ thuộc Tailwind browser.

Source GC xét working/manual/legacy/recovery/template/job/session-history pins,
kiểm lại dưới lock trước xóa và rollback metadata nếu file bị khóa. Manual/legacy
pins giữ bảo thủ; không tự thu hồi. Cache quota 32–4096 MiB chỉ dọn generated
thumbnails; disk reserve 2–64 GiB. Không tự xóa source để đạt quota. Windows Job
Object sở hữu từng command tree, kể cả khi root đã thoát; cleanup không kill toàn
bộ Node/Python. Stage publish được dọn khi cancel/copy/fsync lỗi; source giữ nguyên.

## Kiểm chứng đã đạt

- **26 Vitest**: parser/range/review, lyric source mapping, giữ ID/style khi remap,
  history, schema/hash parity và 12 presets.
- **63 pytest integration**: auth/origin/path/schema, optimistic save/recovery,
  portable corruption/duplicate/traversal/symlink/budgets, imported view validation, manual dirty restore,
  template/library/energy decode thật, quota/pins/locked-file rollback,
  lease/takeover, model unavailable/no-egress disabled providers, package isolation,
  owned process cancel/root exit/crash, publish cancel/fsync và queued-save takeover. Fsync là fault injection,
  không coi là disk-full/power-loss thực.
- **11 browser regression tests**: ba luồng render, editor/history/save/reopen,
  lyrics review/style/preset/recovery/package, library/templates, lease hai tab,
  Drive settings/bootstrap. ASR polling thành công/thất bại dùng transport fixture
  được ghi rõ, không thay evidence model thật. Folder grant E2E là fixture.
- **4 native chooser cases thật**: cancel/Unicode folder/media/package;
  `.local/native-picker/1795460576786011000/results.json`.
- **36/36 MP4**: 3 templates × 12 presets, fixture 2s; decode H.264/AAC,
  dimensions/30–60FPS/60–120 frames/duration và 0 timestamp errors. Giữ admission
  4 GiB/10 samples. Tất cả sampled child resource checks đạt, không suy thành
  peak guarantee cho toàn bộ app. Raw `.local/evidence/s6/1795463206089895000/results.json`.
- **6 AI jobs local thật**: small/medium/alignment trên đoạn 20s Việt và Anh đã có
  quyền dùng local; tất cả succeeded, all-draft và editor unchanged. English align
  có 6 câu fallback, 0 word draft; không coi succeeded là timing quality pass.
  Đây là **development**, không phải held-out corpus/gold. Raw cùng matrix run.
- **VFR regression đạt**: input delta 33.333/66.667ms, trim .25s/rate 2×;
  kiểm frame 7 đỏ và 19 xanh, output timestamps/frame count đạt.
  **2 instrumental ASR** trả 0 dòng trên tone 440Hz; **2 alignment fallback**
  trên supplied text/tone đạt pipeline. Raw `.local/evidence/s6/1795464820430740700/results.json`.
- **7/7 preview/MP4 frames**: TPL-01 caption, TPL-02 hai mốc progress và TPL-03
  bốn word highlights. Global MAE lớn nhất **3,93/255**, tile-P95 MAE **7,59/255**,
  dưới bounds regression 8/15 đặt trước. Đây là fixture image regression,
  không phải human perceptual/glyph audit. Browser 1 test riêng đạt, raw
  `.local/e2e/1795464621324/preview-render-comparison.json`.
- **2 Drive cloud round-trips thật**: 1 generated project + 1 template + 3 media,
  SHA khớp, dedup và project/manual-dirty preservation. Workspace disposable,
  upload fixture tự tạo vào child test folder, không media cá nhân; bản credential
  clone đã dọn. `.local/evidence/s6-drive/1795460827029814200/results.json`.
- Production build, TypeScript, Ruff, Prettier và pip dependency check đạt.
  Full pytest cuối sau hardening: 63/63; diff whitespace check đạt.
  Starlette/httpx deprecation warning và duplicate ZIP warning của negative test
  được giữ; không phải test failure.

Matrix/development-AI runner dừng sau các kết quả trên do hàm đo VFR gọi NumPy
không cài trong API env. Đã sửa bộ đo sang packed RGB, không thêm dependency;
VFR/AI smoke còn thiếu được chạy lại riêng và đạt. Không sửa/xóa raw lần lỗi hoặc
đổi cả lượt lỗi thành pass. `releaseBlockers` trong raw runner là checklist tĩnh;
báo cáo này xác định VFR đã đạt đúng regression nêu trên, không chứng nhận mọi VFR.

Browser regression raw `.local/e2e/1795463014654/`: independent decode 3 outputs
2s/3s đúng frame/H.264/AAC/timestamps. UI 12/100 clip lần mới: P95 selection→
double-rAF **34,7/34,4 ms**, preview **29,05/29,23 FPS**, 30 samples và ~1,5s mỗi
fixture. Không suy thành drag/trim hoặc 100 independent sources. Lần cũ có outlier
1,22s vẫn giữ evidence.

## Video 300s và contention

Lượt `.local/e2e/1795465166402` bị gián đoạn phiên trước khi hoàn tất;
trạng thái DB còn running không được tính pass. Lượt chạy lại
**`.local/e2e/1795483226053` đạt E2E và independent decode**. Giữ admission
4 GiB/10 samples; lúc đầu chờ RAM và người dùng giải phóng thêm rồi mới chạy.

- Fixture TPL-01 **300,000s, 1080×1920/60FPS, H.264/AAC, 18.000 frames,
  0 timestamp errors**, decode audio 14.400.512 samples (AAC padding).
- Render giữ hash snapshot B; UI sửa caption/style thành C vẫn dirty, hash khác B;
  không page error. Test E2E tổng **26,9 phút**, gồm admission/UI/render/validation,
  không coi là pure-render RTF. Output SHA-256:
  `3b2219d14fbe494eb5159c78febf113278cd94bd24806421beb30d0ebc5a9d0f`.
- Mẫu UI trong lúc render: preview **43,47 FPS**, selection P95 **29,4 ms**,
  input P95 **46,5 ms** (20/9 events, ~2s preview). Không suy thành latency mọi
  thao tác hoặc ổn định preview liên tục 300s; ACC-01 chưa được PO chốt.
- Monitor unique owned UI/API/render/test PIDs: **1.326 samples/1.607,662s**,
  sampled peak private **1,681 GiB**, minimum system available **2,998 GiB**
  (bao gồm thời gian chờ admission), peak CPU **428,87% một core**. Scope và
  sampling không phải peak guarantee toàn máy. Render/finalize child samples
  riêng: private peak **1,002 GiB**, RAM trống thấp nhất **4,033 GiB**.
- Independent source-image sparse comparison tại frame 9.000: RGB MAE **1,39**.
  Đây không phải listening hoặc toàn bộ perceptual quality review.

Raw: `long-run-job.json`, `long-run-ui.json`, `long-run-complete.png`,
`application-resources.jsonl`, `application-resources-summary.json`,
`independent-validation-s2.json` trong run mới. Một lượt 300s không thay finalist
repetitions. Evidence lần gián đoạn và lỗi harness trước đó được giữ nguyên.

## Điều kiện chưa thể đóng tự động

1. Independent held-out corpus Việt/Anh/rap/remix/sped/slowed/multiple voices/
   instrumental, word timing gold và correction-time review. Development smoke
   không chứng minh WER/CER hoặc word quality đạt.
2. Human listening A/B AAC, font/glyph/perceptual review; usefulness suggestions
   trên 6 tracks có quyền. Energy test 18s chỉ chứng minh decode/ranking pipeline.
3. ACC-01 thresholds cần PO chốt từ measurements; finalist repetitions theo kế
   hoạch chưa đủ. Không tự nâng G2/G4/G5 hoặc Core/release thành Passed.
4. Full fault matrix mọi phase, power loss/disk-full thật, TOCTOU/service audit,
   portable/Drive khác PC, quota/revoke/large-upload interruptions thật.
   Những regression đang có chỉ chứng minh các fault/scope đã ghi rõ.

## Chạy lại có chủ đích

```powershell
npm.cmd test -- --pool=threads --maxWorkers=1
./.venv-api/Scripts/python.exe -m pytest -q
npm.cmd run build
npm.cmd run test:e2e
./.venv-api/Scripts/python.exe scripts/verify_core.py --matrix --vfr --ai-smoke --alignment-smoke --development-ai
$env:AMVS_TEST_LONG_RUN='1'
npm.cmd run test:e2e -- tests/e2e/long-run.spec.ts
```

Không chạy đồng thời nhiều render coordinators. `AMVS_FIDELITY_RUN` trỏ tới matrix
run hoàn tất để chạy `fidelity.spec.ts`; sau đó `compare_preview_frames.py <e2e-run>`.
`verify_drive_cloud.py` mặc định chỉ plan; `--execute` thực sự upload fixture vào
Drive đã cấu hình, không cần lặp lại khi không có thay đổi liên quan.

Git: chỉ working tree `dev`, chưa commit/push. Files/modules ở bảng đầu và scripts/
tests/docs liên quan. Đề xuất commit sau người dùng duyệt:
`feat(mvp): add lyrics workflows and resilient project tools`; có thể tách domain/
editor, AI, storage/library và verification/docs thành các commit logic.
