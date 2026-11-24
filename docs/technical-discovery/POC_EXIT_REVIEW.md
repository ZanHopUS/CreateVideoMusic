# PoC Exit Review and MVP Entry Conditions

Ngày: **23/11/2026**. Kết luận: **Conditional Go vào xây MVP đã được PO duyệt**
cùng [ADR-0001](../decisions/ADR-0001-LOCAL_MVP_ARCHITECTURE.md) qua “duyệt theo đề xuất”. Không tuyên bố G2 hoàn
tất, ứng dụng đã được triển khai hoặc toàn bộ quality gates đã đạt.

## Tổng hợp bằng chứng

| Phạm vi | Evidence hiện có | Kết luận / phần còn mở |
|---|---|---|
| POC-00 môi trường | Python/Node, local AI, renderer chạy được trên máy thử | Corpus/held-out và annotations chưa đủ |
| POC-01 ASR | Mẫu Việt: medium WER 23.74%, CER 15.56%; small 36.69%/25.19% | Có pipeline thật; chưa chọn model chất lượng mặc định. Chưa phân loại mẫu clean; không suy pass/fail corpus từ một bài |
| POC-02 alignment | Việt 59/68 cues word draft, 9 fallback; preview 33.9s user đã duyệt | Chưa có word-boundary gold; coverage không là timing accuracy. Alignment text-only toàn bài chưa chứng minh |
| POC-03 output | 36 presets sau bounded-audio xử lý được duration | Finalizer vẫn cần listening review; không tự chọn production default |
| POC-04 stress | 5×300s/1080p60, 90,000 frames; RTF 2.378–3.477, sampled resources đạt ở những lượt đó | Generated/looped fixtures, chưa finalist repetitions hoặc AI/editor contention |
| Preview/VFR | TPL01/02 27/27 mốc; TPL03 direct VFR fail 3/27, seek-nudge candidate pass 27/27 | Candidate không là policy chính thức; R2 VFR còn mở |
| Lifecycle | API cancel còn worker ~30s; supervisor candidate dọn ~2.063s | Cần tích hợp supervisor thực, cancel/fault ở từng phase |
| State/template | 6 fixtures, 300 edits/undo/redo; clone/bindings và dirty checks đạt | Model harness, chưa UI latency hoặc ứng dụng |
| POC-05 storage | 24 crashes/12 phases, 10 restores, lặp lại cùng fixtures đạt; Windows locks/SQLITE_FULL | Không phải power loss; ENOSPC file injected; schema/driver/container chưa Accepted |
| Path safety | 3 junction thật, 10 escapes bị chặn, canary giữ nguyên | Không chứng minh TOCTOU/service security |
| RAM admission | Hai video 12s mới đạt chức năng + sampled R0, min available 2.725 GiB | Lượt fail 1.850/1.651 GiB vẫn giữ; admission 300s bị từ chối, không có render mới |
| POC-06 cloud | Không chạy theo scope local | Không cản khởi công local; cloud tiếp tục tắt |
| POC-07 suggestions | Chưa chạy | FR-105/206 vẫn ở Core, phải kiểm chứng trước release |
| Drive | Chưa sync/download/restore thực | FR-407/ST-03 còn mở; local copy chưa là cloud backup |

Chi tiết và raw pointers: [POC_STATUS](POC_STATUS.md), [ASR](MEDIUM_ASR_COMPARISON.md),
[alignment](ALIGNMENT_POC_RESULTS.md), [stress](RENDER_STRESS_SUITE_RESULTS.md),
[fidelity](PREVIEW_RENDER_FIDELITY_RESULTS.md), [lifecycle](JOB_LIFECYCLE_RESULTS.md),
[storage](STORAGE_RECOVERY_POC_RESULTS.md), [RAM](RENDER_RESOURCE_ADMISSION_RESULTS.md),
[junctions](WINDOWS_PATH_SAFETY_RESULTS.md).

## Điều kiện vào xây dựng, khác với điều kiện release

PRD đặt G2 trước G3/G4; bằng chứng hiện tại chưa đủ đánh dấu G2 Passed. Đề nghị
Product Owner chấp thuận **chuyển sang phát triển có điều kiện**, giữ các phần G2
còn thiếu thành release blockers trong kế hoạch. Không tự sửa PRD hoặc giảm Core.

| Trước công việc | Điều kiện |
|---|---|
| Viết application code | PO duyệt ADR/contracts và conditional entry; chốt source root, local permissions, media policy |
| S0 → feature work | Frontend/API/renderer/SQLite/native picker smoke trên Windows; lock dependency versions/licenses, contract parity đạt |
| Tích hợp AI vào luồng thật | Job local, review/error states; model license/revision được ghi; không giả lập transcript hoặc confidence |
| Nghiệm thu Core | Toàn bộ Core FR/AC, E2E thật và các gate chưa đạt có evidence; không lấy harness thay verification |

## Các việc làm song song, không kéo dài PoC vô hạn

- Lyrics: benchmark thêm bài độc lập có quyền dùng, timing gold, correction time;
  giữ tiếng Anh ưu tiên thấp theo steering nhưng không xóa cam kết hỗ trợ.
- Rendering: VFR regression, nghe A/B AAC, long-run admission/repetitions và UI
  contention khi có editor. Không lặp cả matrix chỉ để có thêm số liệu.
- Storage: schema/migration, kill/fault giữa nhiều tài nguyên, capability/TOCTOU,
  portable/Drive restore. Package format và quyền folder cần chốt ở ADR trước code.
- Suggestions: corpus 6 track có quyền theo POC_PLAN; không gọi mock là gợi ý thật.

## Quyết định khi bằng chứng tiếp tục không đạt

Không tự bỏ rap/remix/English, word fallback, một export preset hay Drive. Nếu
không đủ bằng chứng cho release, giữ trạng thái blocked/experimental tương ứng,
báo phương án và xin quyết định sản phẩm. Manual lyrics bảo đảm một workflow có
ích nhưng không thay thế FR-201. NFR latency/quality còn là mục tiêu sàng lọc;
ngưỡng release cần PO chốt từ measurement, không tự nâng yêu cầu phần cứng.
