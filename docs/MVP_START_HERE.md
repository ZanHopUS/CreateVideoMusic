# MVP Implementation Readiness

Tiến độ hiện tại 24/11/2026: xem [kết quả S2–S6](planning/S2_S6_RESULTS.md).
Các thông tin ngày 23/11 dưới đây là checkpoint lịch sử, không thay báo cáo mới.

Ngày: **23/11/2026**. Trạng thái: **đã được Product Owner duyệt khởi công** qua
“duyệt theo đề xuất”, gồm ADR/contracts và conditional entry S0 → S1.
Ứng dụng đã có foundation và luồng TPL-01 nội bộ; baseline A–G giữ nguyên.
Xem [implementation status](planning/MVP_IMPLEMENTATION_STATUS.md) và
[hướng dẫn chạy](../README.md). Không xem bản nội bộ là nghiệm thu Core.

## Hồ sơ cần đọc

1. [PoC exit review](technical-discovery/POC_EXIT_REVIEW.md): bằng chứng, giới hạn,
   điều kiện chuyển sang xây dựng và những mục chưa đạt.
2. [ADR-0001](decisions/ADR-0001-LOCAL_MVP_ARCHITECTURE.md): stack, process boundary,
   local permissions, lưu trữ, AI và render; **Accepted**.
3. [MVP contracts](architecture/MVP_CONTRACTS.md): timeline/timebase, save/dirty,
   template, job, API và portable package; **Accepted design**, triển khai theo milestone.
4. [Implementation plan](planning/MVP_IMPLEMENTATION_PLAN.md): thứ tự triển khai,
   acceptance/test và mapping đầy đủ 38 FR.

Nguồn yêu cầu thực tế vẫn ở root: [PRD](../PRD_v1.0.md), [SRS](../SRS_v1.0.md),
[RTM](../RTM_v1.0.md), [Open Questions](../OPEN_QUESTIONS.md). Không di chuyển file
hoặc coi những ghi chú “Not run” lịch sử trong discovery là trạng thái hiện tại.

## Quyết định đã được phê duyệt

**Chấp thuận ADR-0001 + MVP_CONTRACTS và bắt đầu S0 → S1 theo implementation plan**:

- Next.js/TypeScript/Tailwind; FastAPI local điều phối SQLite/Python AI và Node
  Remotion/FFmpeg. Một heavy job tại một thời điểm, editor vẫn dùng được.
- Timeline canonical ticks 48 kHz; managed assets; manual save/recovery tách biệt;
  ZIP portable versioned; folder capability và session chỉ trên loopback.
- Cho phép xây MVP có điều kiện khi chất lượng AI chưa nghiệm thu: tích hợp ASR
  thật, review và fallback; không tuyên bố manual-only hoàn thành Core.

Phê duyệt này không nghiệm thu G2/G4/G5, không duyệt cloud uploads, phát hành,
commit/push hoặc thay đổi A–G. Phiên bản dependency cụ thể được pin sau smoke S0;
nếu smoke buộc đổi process boundary/storage/time contract, báo cáo để sửa ADR.

Ngày/chủ sở hữu đã ghi trong ADR. S0 bootstrap/checks và S1 TPL-01 đã bắt đầu;
import → draft → edit → save/reopen → MP4 thật có evidence nội bộ. Các gate còn mở
phải đóng trước release Core; không cần duyệt lại cùng kiến trúc khi tiếp tục task
trong phạm vi đã chấp thuận.

Git: checkpoint đã push `de401aa`; resource/path follow-ups và bộ hồ sơ này còn
chưa commit/push trên `dev`. Commit riêng cho hồ sơ đề xuất:
`docs(mvp): define architecture contracts and implementation gates`.
