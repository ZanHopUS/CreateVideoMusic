# Tiến độ triển khai UI R1–R6

Baseline `dev` 7230382, Master v2.1 Approved for implementation. Chưa commit/push.

| Phase | Trạng thái | Evidence / blocker |
|---|---|---|
| R0 gate | Regression từng phần đạt | E2E takeover hai tab: test body passed; Playwright teardown trên Windows không thoát, phải Ctrl+C; backend lease/GC/recovery subset 9 passed |
| R1.A | Partially implemented | Token/chrome radius0, focus; chưa đủ primitive/state specimens/contrast/NVDA |
| R1.B | Partially implemented | Dashboard template thật, nav 4 mục, recent API+UI; geometry hai viewport passed, new-tab browser body passed; restart/port-change browser chưa chạy |
| R2 | Partially implemented | Một useStudio controller giữ khi đổi workspace, versioned recent/prefs file; application-level jobs list poll 3s, UI theo dõi render; lyrics draft được giữ theo project trong phiên và có guard khi chuyển project; browser test body passed |
| R3 | Partially implemented | Editor 3 cột, dock resize pointer/keyboard, no-page-scroll CSS; browser geometry/first-fold/fullscreen hai viewport passed, pointer/keyboard resize browser test body passed; compact evidence còn thiếu |
| R4.A/B | Existing capability rehosted; advanced chưa triển khai | ProjectTools/Lyrics/Inspector/Timeline thật; 5 tabs/advanced D-02 chưa code; cần contract + legacy/renderer tests; TPL-03 và library E2E test bodies passed |
| R5.A | Partially implemented | Storage workspace bốn tab với status/backups/MP4/API thật; transfer action giữ DrivePanel, Export dialog baseline, Projects Grid/List, Settings 6 sections với policy/cleanup/AI/Drive; Recovery read-only workspace đã có; restore trực tiếp/full transfer progress/cancel/history và full Export còn thiếu |
| R5.B | Blocked/Not Run | Cloud progress/cancel/history cần backend delta + tài khoản/consent; filename/recovery/delete safety/metadata chưa đủ |
| R6 | Partially tested | Vitest 36 passed, local API integration 12 passed, safety subset 9 passed, typecheck/build/format passed; Playwright test bodies: geometry2, Settings/Recovery1, Drive2, lease1, TPL-03 1, library1, lyrics draft1, recent/prefs new-tab1, timeline resize1. Runner teardown trên Windows treo, Ctrl+C sau khi test body hoàn tất. Full acceptance matrix chưa đạt |

**Open:** R1.A primitives/contrast/NVDA; R2 app job registry/persistence draft ngoài phiên; R3 compact/resize drag proof; R4 advanced D-02; R5 true transfer lifecycle, Export filename/result contract, PM restore/delete guard; R6 dev browser/full matrix/real cloud. Cloud thực cần tài khoản/folder và consent được cấp. Không gọi R1–R6 Passed khi ma trận còn mở.
