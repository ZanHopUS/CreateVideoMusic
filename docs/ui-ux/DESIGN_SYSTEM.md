# Design System v1.0 — Hòa Âm

**Ngày:** 24/11/2026 (Asia/Saigon) · **Baseline code:** `dev`, `d12015a`.

**Trạng thái tài liệu:** v1.0 — **Approved theo phạm vi DS-P01…DS-P07 ngày 24/11/2026**; DS-P05 chỉ duyệt thử nghiệm hai viewport, DS-P08 đã có UI-03 Approved for Design theo ST-01…ST-07. Các chi tiết ngoài quyết định vẫn Proposed/Pending Approval; không coi mọi chi tiết layout/API ngoài quyết định là Approved.

## 0. Thẩm quyền, nguồn và cách đọc

| Trạng thái              | Nội dung                                                                                                                                                                                                                                       | Nguồn quyết định                                                                                                    |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Approved**            | Phương án 2 — Minimal Professional; desktop-first, tiếng Việt; không bo góc (`border-radius: 0`), không neon glow, không gradient trang trí dư thừa, không shadow mạnh; panel phẳng/viền mảnh, màu ít bão hòa, lavender xám, spacing nhất quán | Task Design System do PO cung cấp và xác nhận tiếp tục                                                              |
| **Approved**            | R0 Editor Lease/read-only được PO nghiệm thu ngày 24/11/2026 qua trả lời “xác nhận” sau câu hỏi xác nhận nghiệm thu R0                                                                                                                         | [Bản ghi nghiệm thu R0](UI_R0_LEASE_FIX_RESULTS.md#po-acceptance-r0)                                                |
| **Approved**            | Cấu trúc Editor, no-page-scroll, Preview/Timeline thường trực ở chế độ thường, resize và bảo toàn nghiệp vụ                                                                                                                                    | [UI-02 nguyên văn](UI_02_VIDEO_EDITOR.md), Approved for Design                                                      |
| **Approved**            | Hướng D-01…D-05; Dashboard template-first/dark-purple                                                                                                                                                                                          | [Sổ quyết định](UI_GAP_ANALYSIS.md#5-sổ-quyết-định-d-01d-06--cập-nhật-po-24112026); UI-01 vẫn Proposed về wireframe |
| **Approved**            | Palette hiện tại; Segoe UI cho giao diện v1; body14px/label13px/caption12px; component/tương tác với keyboard và lỗi rõ; template trước recent; triển khai R1 theo từng phần, không gộp Advanced Editor                                        | PO xác nhận DS-P01…DS-P07, xem §11                                                                                  |
| **Approved for trial**  | DS-P05: thử nghiệm ở1366×768 và1920×1080; chưa đồng nghĩa các breakpoint/Compact Mode nhỏ hơn đã nghiệm thu                                                                                                                                    | Quyết định PO ngày24/11/2026                                                                                        |
| **Proposed**            | Heading scale/line-height/weights và kích thước chưa được chốt cụ thể; compact/breakpoints, persistence/metadata contract và chi tiết ngoài các quyết định                                                                                     | Chỉ triển khai theo phase/contract được duyệt, không tự nâng quyền từ ảnh                                           |
| **Approved for Design** | UI-03: ST-01…ST-07 — workspace riêng/bốn tab, progress/error/cancel thật, hai lịch sử, auto-off/consent, cloud test thật và giữ Editor state                                                                                                   | PO xác nhận “duyệt theo đề xuất”, [bản ghi UI-03](UI_03_STORAGE_MANAGER.md#storage-decisions)                       |
| **Pending Approval**    | Contract UI-03 progress/error/cancel, persistence/history chi tiết chưa chốt; D-06 vẫn Recommended                                                                                                                                             | Chưa duyệt API/schema mới hoặc cloud acceptance                                                                     |

Đã đối chiếu [AGENTS](../../AGENTS.md), PRD/SRS/RTM/OPEN_QUESTIONS **tại root** (đường dẫn docs/requirements trong AGENTS không tồn tại), [ADR-0001](../decisions/ADR-0001-LOCAL_MVP_ARCHITECTURE.md), [ADR-0002](../decisions/ADR-0002-DIRECT_GOOGLE_DRIVE.md), [MVP contracts](../architecture/MVP_CONTRACTS.md), [UI-01](UI_01_DASHBOARD.md), [UI-02](UI_02_VIDEO_EDITOR.md), [Gap Analysis](UI_GAP_ANALYSIS.md), [Plan](UI_REDESIGN_PLAN.md), CSS/config và sáu frontend components. Chi tiết hiện trạng: [UI Design Audit](UI_DESIGN_AUDIT.md).

Ảnh PO cung cấp “Ảnh ChatGPT 13_13_56 24 thg 11, 2026.png” là **tham chiếu hình ảnh**, không phải screenshot ứng dụng. Dùng panel phẳng, nhịp phân cấp và lavender trong ảnh; Noto Serif VN/Inter là font candidate. Không sao chép toàn bộ mã màu/kích thước trong ảnh thành Approved. Hero ảnh lớn, góc bo, gradient trang trí, nút chức năng/hiệu ứng chưa hỗ trợ, gói Creative/quota 1TB và các số liệu giả không trở thành phạm vi sản phẩm. File ảnh ở máy PO, chưa đưa vào repo hoặc dùng làm asset production. Tại baseline chưa có đặc tả `UI-03`; theo DS-P08 đã soạn [UI-03 Storage Manager](UI_03_STORAGE_MANAGER.md) nay Approved for Design theo xác nhận PO “duyệt theo đề xuất” cho ST-01…ST-07; quyền duyệt đến từ PO, không từ ảnh.

## A. Design Principles

| Nguyên tắc    | Quy tắc vận dụng                                                                                                                            |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Professional  | Nội dung project, Preview và Timeline là ưu tiên. Hiển thị đúng quyền, revision và trạng thái job; nút có nhãn theo hành động.              |
| Minimal       | Một accent lavender xám. Phân vùng bằng surface/viền; bỏ mảng trang trí không phục vụ tác vụ. Shell không có glow, blur kính hoặc gradient. |
| Consistent    | Một bộ semantic tokens và primitive cho form/status/action; không tự đặt màu/cỡ chữ từng panel.                                             |
| Functional    | Select/seek đọc được trong read-only; mutation vẫn qua controller/lease. Không dựng control như đã hoạt động nếu capability chưa có.        |
| Accessible    | Focus phân biệt với selected; nhãn/đơn vị/lỗi bằng chữ; thao tác có phương án keyboard và không chỉ kéo-thả.                                |
| Desktop-first | Thiết kế tại 1366×768 và 1920×1080 trước; compact có chủ đích. Chưa hứa mobile Editor hoàn chỉnh.                                           |

Nguyên tắc là hướng **Approved** từ task; cách thể hiện cụ thể là **Proposed**. Design System chỉ style chrome ứng dụng; không đổi fonts, màu, radius hay animation bên trong composition/video user đang tạo. Video và ảnh có gradient/bo góc do nội dung project không vi phạm quy tắc shell.

## B. Color System — Approved DS-P01

### B1. Token architecture

Ba tầng: primitive HEX → semantic role → component alias. Ví dụ `neutral.950 → color.background → editor.background`; `lavender.400 → color.accent → button.primary.background`. Một primitive có thể được tham chiếu nhiều nơi; token tên theo chức năng, không theo giá trị. Trong code tương lai chỉ dùng semantic/component aliases; không thay `--accent` toàn app mà chưa kiểm ảnh hưởng scene/UA controls. Không thêm theme library cho việc ánh xạ này.

| Semantic token (tên tài liệu) | Giá trị               | Vai trò / giới hạn                                                       |
| ----------------------------- | --------------------- | ------------------------------------------------------------------------ |
| `color.background`            | `#101217`             | Nền app/Preview surround; không dùng như canvas user                     |
| `color.surface`               | `#191D26`             | Panel, card, control nền cơ bản                                          |
| `color.surface-elevated`      | `#252A36`             | Menu/dialog/hover surface; elevation không cần shadow                    |
| `color.border`                | `#343A49`             | Divider trang trí/nhóm nội dung; không đủ cho boundary control cần thiết |
| `color.border-control`        | `#737D93`             | Viền input, checkbox, interactive outline cần nhìn thấy                  |
| `color.text-primary`          | `#ECEEF3`             | Nội dung/nhãn/action chính                                               |
| `color.text-secondary`        | `#A1A7B5`             | Metadata, trợ giúp                                                       |
| `color.text-muted`            | `#959CAD`             | Mức nhấn thấp, vẫn đọc được; không giảm opacity tiếp                     |
| `color.accent`                | `#A8A0CB`             | Primary action, selected marker, focus                                   |
| `color.accent-hover`          | `#B8B0DB`             | Hover primary; chỉ thay màu, không glow/scale                            |
| `color.accent-active`         | `#C5BDE8`             | Pressed primary; trở về hover/rest sau release                           |
| `color.on-accent`             | `#101217`             | Chữ/icon trên primary fill, luôn màu tối                                 |
| `color.selection-surface`     | `#343044`             | Selected tab/clip/card; đi kèm marker và semantic state                  |
| `color.success`               | `#A1C5AE`             | Đã xác nhận thành công                                                   |
| `color.warning`               | `#D8BD85`             | Chưa lưu/waiting/tác vụ cần chú ý                                        |
| `color.error`                 | `#E0A3AC`             | Lỗi/invalid/destructive outline và nhãn                                  |
| `color.info`                  | `#A5BDD6`             | Thông tin/quyền cần kiểm tra                                             |
| `color.disabled-fg`           | `#7D8494`             | Inactive icon/label, kèm lý do đọc bằng text-secondary                   |
| `color.disabled-bg`           | `#202530`             | Control bất hoạt, không opacity cả container                             |
| `color.scrim`                 | `rgba(16,18,23,0.80)` | Che nội dung sau modal; overlay không là bề mặt đọc chữ                  |

Giữ bảy màu khởi điểm của PO làm các vai trò tương ứng; bổ sung muted/semantic/control border. `border-control` sáng hơn divider để thấy control trên elevated. Semantic colors dịu, không dùng màu warning/success cho track nhạc chỉ để trang trí. Track loại clip có icon + nhãn; màu loại có thể dùng accent/info/success/warning như mã phân loại **kèm legend**, không ngụ ý trạng thái job.

### B2. Contrast worksheet — tính toán, chưa phải UI test

Ngày tính 24/11/2026. sRGB opaque, không opacity/blending: chuyển mỗi kênh `s/255`; nếu ≤0.04045 thì chia 12.92, còn lại `((c+0.055)/1.055)^2.4`; luminance `0.2126R+0.7152G+0.0722B`; ratio `(Lmax+0.05)/(Lmin+0.05)`. Số làm tròn 2 chữ số, so ngưỡng bằng số chưa làm tròn. Dữ liệu là cặp màu đã tính, không tuyên bố WCAG toàn ứng dụng.

| Foreground     | Background | Surface | Elevated | Ý nghĩa                                |
| -------------- | ---------: | ------: | -------: | -------------------------------------- |
| Primary text   |    16.14:1 | 14.53:1 |  12.36:1 | Đủ text thông thường                   |
| Secondary text |     7.77:1 |  7.00:1 |   5.95:1 | Đủ metadata/label                      |
| Muted text     |     6.81:1 |  6.13:1 |   5.22:1 | Đủ caption 12px, không dim thêm        |
| Accent         |     7.63:1 |  6.87:1 |   5.85:1 | Đủ chữ/link/focus trên ba nền          |
| Success        |     9.91:1 |  8.93:1 |   7.60:1 | Icon + nhãn                            |
| Warning        |    10.29:1 |  9.27:1 |   7.89:1 | Icon + nhãn                            |
| Error          |     8.92:1 |  8.03:1 |   6.84:1 | Text lỗi/viền invalid                  |
| Info           |     9.68:1 |  8.71:1 |   7.42:1 | Icon + nhãn                            |
| Control border |     4.54:1 |  4.08:1 |   3.47:1 | Đủ boundary 3:1                        |
| Divider border |     1.65:1 |  1.48:1 |   1.26:1 | Không đạt 3:1; chỉ phân nhóm trang trí |

`on-accent` trên accent/hover/active: **7.63 / 9.16 / 10.54:1**. Selected surface + primary/secondary/accent: **10.95 / 5.27 / 5.18:1**. Không dùng primary text sáng trên accent fill. Tooltip/dialog đọc trên elevated; destructive dùng nền surface, chữ/viền error, không dùng chữ trắng trên error. Focus trên primary fill dùng hai nét: 2px tối ngăn cách + 2px lavender ngoài để không hòa vào nút; kiểm adjacent colors thực tế khi triển khai.

Mục tiêu text ≥4.5:1; large text ≥3:1 (18pt regular hoặc 14pt bold); thông tin control và focus cần ≥3:1. Trạng thái inactive thuộc ngoại lệ contrast nhưng lý do vẫn cần đọc được. Màu không là tín hiệu duy nhất. Các ngưỡng này theo [WCAG 2.2 — contrast](https://www.w3.org/TR/WCAG22/#contrast-minimum) và [non-text contrast](https://www.w3.org/TR/WCAG22/#non-text-contrast).

Không tính ratio của scrim như control color. Ảnh/thumbnail/Preview có nền bất kỳ: đặt nhãn trên nền opaque đã kiểm, không giả định màu chữ luôn đủ tương phản trên video.

## C. Typography — Approved một phần theo DS-P02/03

| Token                  | Font / weight                          | Size / line height | Sử dụng                                                                                                            |
| ---------------------- | -------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------ |
| `font.ui`              | `"Segoe UI", Arial, sans-serif`        | Theo scale         | Lựa chọn khởi điểm: hệ điều hành Windows đã có, không tải mạng; label/body/heading chức năng                       |
| `font.brand-candidate` | Noto Serif (Vietnamese subset), 600    | 28/36              | Candidate cho wordmark/heading Dashboard theo ảnh; tên “Noto Serif VN” trong ảnh chưa xác minh là font asset riêng |
| `font.ui-candidate`    | Inter (Vietnamese glyphs), 400/500/600 | Theo scale         | Candidate thay Segoe UI nếu PO chọn; cần bundle local và kiểm license/glyph/metrics, chưa thêm dependency          |
| `font.numeric`         | `Consolas, "Courier New", monospace`   | 12/16 hoặc 14/20   | Timecode, timestamp, hàng dữ liệu số; `tabular-nums`, không áp cho mọi label                                       |
| `type.h1`              | UI 600                                 | 28/36              | Tiêu đề Dashboard/workspace; không 60px hero                                                                       |
| `type.h2`              | UI 600                                 | 20/28              | Section/dialog lớn                                                                                                 |
| `type.h3`              | UI 600                                 | 16/24              | Nhóm panel                                                                                                         |
| `type.body`            | UI 400                                 | 14/20              | Nội dung chính                                                                                                     |
| `type.label`           | UI 500                                 | 13/20              | Form/toolbar/tab                                                                                                   |
| `type.caption`         | UI 400                                 | 12/16              | Metadata/phụ trợ; không dưới 12px trong chrome                                                                     |
| `type.timecode`        | Numeric 400                            | 12/16              | `HH:MM:SS:FF`, FPS từ project; phân biệt với giây/ticks                                                            |

PO đã chọn **Segoe UI cho giao diện v1**, body14px/label13px/caption12px. Inter chỉ cân nhắc sau; Noto Serif không được tự thêm làm font tiêu đề. Heading scale, line-height và các chi tiết typography khác ở bảng là đề xuất chưa được quyết định riêng. Không dùng ảnh để ngầm đổi font đã chốt. Khi bundle font: self-host, chỉ preload weight đầu màn hình cần dùng; không Google Font request. Không giấu label để chờ font, không làm toolbar đổi chiều cao. Fallback phải có đủ glyph, đo metrics khi triển khai. Không đổi font composition/MP4; đó là lựa chọn content có pipeline riêng.

Dùng rem cho text và kích thước control cơ bản, không khóa zoom trình duyệt. Font weight 400/500/600; 700 chỉ cảnh báo/heading cần nhấn. Letter spacing 0 cho body/label, heading tối đa -0.01em, không tracking rộng cho dấu Việt nhỏ. Stress string: “Hòa Âm — Đường về quê hương, Nguyễn Thị Mỹ; Ắ Ằ Ẳ Ẵ Ặ Ế Ề Ể Ễ Ệ Ỹ Ỵ; 00:01:24:12; 1.250,5”. Không clip dấu khi line-height/reserve-space thay đổi.

Tên file: `min-width:0` trên grid/flex child; card tối đa hai dòng tên, `overflow-wrap:anywhere`, không làm cột rộng ra; giữ extension ở metadata riêng. Hàng hẹp dùng một dòng ellipsis và lối xem tên đầy đủ bằng focus/tooltip hoặc popover có thể copy. Accessible name vẫn là tên đầy đủ, không chỉ `title`. Label form tối đa hai dòng, không ellipsis che đơn vị/lỗi; khi hẹp chuyển label lên trên input. Không đổi/dạng chuẩn hóa chuỗi Unicode gốc để làm đẹp.

## D. Spacing, sizing, radius và density

**Approved:** base spacing 4px; tất cả authored corners bằng 0. Không dùng pill cho badge/toggle/slider thumb. Native OS dialog/scrollbar có giao diện hệ thống riêng, không bị giả lập chỉ để ép góc vuông.

| Token Proposed                 | Giá trị                                          | Dùng                                                            |
| ------------------------------ | ------------------------------------------------ | --------------------------------------------------------------- |
| `space.0/1/2/3/4/6/8/10/12`    | 0/4/8/12/16/24/32/40/48px                        | Nhịp gap/padding; stroke và text size không buộc là bội 4       |
| `radius.none`                  | **0, Approved**                                  | Button/input/card/menu/modal/clip/handle                        |
| `border.width` / `focus.width` | 1px / 2px                                        | Divider/outline; focus có offset 2px                            |
| `shadow.none`                  | none                                             | Panel/card; dialog dùng scrim + border-control, chưa cần shadow |
| `panel.padding`                | 16px standard, 12px compact                      | Left/Inspector, section gap 24px                                |
| `control.height`               | 36px standard, 32px dense, 40px prominent        | Input/button/select; dense không giảm font                      |
| `control.inline-padding`       | 12px (8px dense)                                 | Không đổi theo độ dài nhãn                                      |
| `icon.size` / `icon.stroke`    | 16px, 20px prominent / 1.5–2px                   | Cùng bộ icon SVG, chưa chọn library                             |
| `icon-button.target`           | 32×32px; 40×40 prominent                         | Glyph 16/20 căn giữa; không tạo control nhỏ 16px                |
| `toolbar.height`               | 40px                                             | Một hàng; overflow menu có nhãn cho lệnh phụ                    |
| `panel-header.height`          | 40px                                             | Title/tab không chiếm Preview                                   |
| `editor-header.height`         | 56px                                             | Tên project, save/lease, actions                                |
| `status-strip.height`          | 32px                                             | Tóm tắt một dòng; nội dung đầy đủ qua details/popover           |
| `track.height`                 | 48px standard, 40px dense                        | Header/clip cùng cao; không bóp chật controls                   |
| `target.minimum`               | 24×24px floor; ưu tiên 32px desktop / 44px touch | Trừ ngoại lệ có đánh giá riêng, không viện dense để bỏ target   |

Density là presentation, không thay viewport time, ticks, project data, history hay dirty. Dense dùng 32px control/12px padding, không 10px text. Không áp density toàn app bằng `transform:scale`. Hit area cần không overlap; icon nhỏ có thể nằm trong target lớn. Clip có duration hiển thị hẹp hơn 24px phải có cách chọn/chỉnh bằng danh sách/numeric, không kéo rộng clip làm sai thời gian.

## E. Component System — Approved design theo DS-P04

### E0. Contract chung

PO duyệt component và tương tác, bắt buộc keyboard và trạng thái lỗi rõ. Đây là duyệt thiết kế, không phải kết quả kiểm triển khai. Những kích thước/layout phụ thuộc DS-P05 vẫn phải thử nghiệm. Tất cả component bên dưới theo tám mục: vai trò, cấu trúc, variants, kích thước, states, keyboard/accessibility, nên dùng, không nên dùng. Tên API là ý tưởng, chưa tạo TS files hoặc public contract. Mỗi control có default/hover/pressed/focus-visible/disabled và loading khi phù hợp; selected khác focus; error không thay nhãn. Header/status giữ footprint, thông báo dài có vùng đọc đầy đủ, không chỉ ellipsis mất lỗi.

Primitive nhận presentation + value/callback, không tự fetch session/claim/takeover, không sở hữu bản project thứ hai. `readOnly`, `disabled`, `busy`, `invalid`, `reasonId` phải tách; không dùng boolean `loading` làm writable. Không có hành động nghiệp vụ trong Tooltip/Toast. Native elements là mặc định nếu đạt interaction; custom ARIA cần keyboard test. Icon SVG decorative `aria-hidden`; icon-only button có accessible name độc lập tooltip. Ưu tiên SVG nhỏ tự quản từ nguồn có license rõ; chưa thêm UI/icon library.

### E1. Button

- **Vai trò:** Kích hoạt một hành động, phân cấp theo mức quan trọng.
- **Cấu trúc:** Native button type=button mặc định; icon tùy chọn + nhãn + busy indicator giữ chỗ.
- **Variants:** Primary: accent/on-accent; Secondary: elevated/primary; Outline: surface/border-control; Ghost: transparent/primary; Destructive: surface/error text+border, hover vẫn giữ ratio.
- **Kích thước:** Cao 36, dense 32, prominent 40px; padding ngang 12px, gap 8px; radius 0.
- **Interaction states:** Rest/hover/pressed/focus/disabled/busy; busy giữ nhãn như “Đang lưu…” và width đủ, chặn submit trùng; failure trả về actionable error.
- **Keyboard/accessibility:** Enter/Space; focus-visible; type=submit chỉ trong form; native disabled không focus được nên lý do hiển thị cạnh nhóm. aria-busy không tự chặn handler.
- **Quy tắc sử dụng:** Một primary cho mỗi nhóm tác vụ; “Lưu project”, “Xuất video”, destructive ghi rõ đối tượng.
- **Không nên dùng:** Không dùng link để ghi dữ liệu, không dùng primary cho mọi nút, không thay backend confirmation bằng trạng thái pressed.

### E2. Icon Button

- **Vai trò:** Thao tác ngắn lặp lại như Undo, Redo, mute, đóng.
- **Cấu trúc:** Button + SVG + accessible name + tooltip; pressed state nếu đúng là toggle.
- **Variants:** Ghost, Outline; toggle aria-pressed cho chế độ bật/tắt; destructive khi xóa.
- **Kích thước:** Target 32×32, prominent 40×40; icon 16/20px.
- **Interaction states:** Hover/pressed/focus/disabled; selected có marker, không nhầm icon đổi màu là focus.
- **Keyboard/accessibility:** Enter/Space; aria-label “Hoàn tác”, “Tắt tiếng”; tooltip cả hover và focus; reason visible khi disabled.
- **Quy tắc sử dụng:** Dùng cho icon quen thuộc, kèm nhãn ở context ít quen.
- **Không nên dùng:** Không nút ký tự Unicode không nhãn; không chỉ tooltip cho thông tin bắt buộc; không bỏ target để tiết kiệm diện tích.

### E3. Input

- **Vai trò:** Nhập text, số, tìm kiếm hoặc tên project.
- **Cấu trúc:** Field label + input + helper/error + đơn vị; label htmlFor, helper/error IDs.
- **Variants:** Text, Search, Numeric, readOnly; secret input chỉ khi nghiệp vụ thật cần, không hiển thị OAuth secret.
- **Kích thước:** Cao 36/32px; padding 8/12px; numeric width tối thiểu 80px, mở rộng theo đơn vị.
- **Interaction states:** Empty/filled/hover/focus/invalid/disabled/read-only; giữ raw draft chưa hợp lệ để sửa, không im lặng clamp thành giá trị khác.
- **Keyboard/accessibility:** Tab/focus, chọn/copy; Enter commit khi luồng cho phép, Escape hủy draft về giá trị hiện tại; không chiếm Ctrl+Z nếu đang nhập. aria-invalid và describedby.
- **Quy tắc sử dụng:** Kiểm min/max/step và đơn vị từ domain; giữ semantics commit hiện có khi chưa có task đổi.
- **Không nên dùng:** Không placeholder thay label; không mỗi lần gõ tự đổi revision/ghi hợp lệ giả; không disable input chỉ vì có tooltip.

### E4. Textarea

- **Vai trò:** Nhập caption, lyrics thô hoặc ghi chú nhiều dòng.
- **Cấu trúc:** Label + textarea + số dòng/validation + helper/error.
- **Variants:** Caption, Lyrics import, readOnly result; luôn phân biệt AI draft chưa duyệt.
- **Kích thước:** Min-height 96px; padding 12px; tăng chiều cao trong panel scroll, không đẩy Preview/Timeline.
- **Interaction states:** Focused/dirty/invalid/loading nguồn/disabled/read-only; giữ text nếu lỗi parser/job.
- **Keyboard/accessibility:** Tab đi tiếp, Enter xuống dòng; Ctrl+Enter chỉ khi shortcut được hiển thị và duyệt; selection/copy vẫn dùng được.
- **Quy tắc sử dụng:** Cho nội dung cần đọc nhiều dòng; resize dọc có bounds của panel.
- **Không nên dùng:** Không đặt textarea auto-grow vô hạn trong editor shell; không tự áp dụng lyrics hoặc cắt text dài.

### E5. Select

- **Vai trò:** Chọn một giá trị trong tập hữu hạn.
- **Cấu trúc:** Visible label + native select + mô tả đơn vị/capability.
- **Variants:** Preset, font, loại media/model; optgroup khi có nhóm; custom combobox chỉ sau khi chứng minh native không đủ.
- **Kích thước:** 36/32px, min-width 96px, width 100% panel field.
- **Interaction states:** Rest/focus/disabled/invalid/loading; lựa chọn unsupported có lý do, không giả hoạt động.
- **Keyboard/accessibility:** Native keyboard và accessible name; khi custom phải bổ sung combobox/listbox pattern riêng, không chỉ gán role.
- **Quy tắc sử dụng:** Options từ PRESETS/domain/API hiện hành; label tiếng Việt dễ hiểu.
- **Không nên dùng:** Không dùng select để thực thi destructive action ngay; không bịa model/font/preset có trong ảnh.

### E6. Checkbox

- **Vai trò:** Bật một lựa chọn độc lập hoặc xác nhận consent.
- **Cấu trúc:** Input checkbox hình vuông + label bấm được + helper/error.
- **Variants:** Unchecked/checked/mixed cho chọn tập con; mixed không dùng cho consent.
- **Kích thước:** Ô 16×16px, vùng click label cao ≥32px; khoảng trống 8px.
- **Interaction states:** Checked có checkmark; focus rõ; disabled reason; consent mặc định chưa chọn nếu chưa có hợp lệ.
- **Keyboard/accessibility:** Space toggle; native indeterminate cho chọn một phần; label/description liên kết.
- **Quy tắc sử dụng:** Quyền media, chọn items; lưu consent theo flow backend, không chỉ lưu màu check.
- **Không nên dùng:** Không tự check consent từ sự hiện diện của file; không dùng mixed để che trạng thái không rõ.

### E7. Toggle

- **Vai trò:** Đổi setting nhị phân có hiệu lực ngay.
- **Cấu trúc:** Switch label + track/thumb vuông + trạng thái chữ Bật/Tắt + reason.
- **Variants:** Off/On/Pending; optional disabled. Tự sao lưu chỉ phản ánh server đã xác nhận.
- **Kích thước:** Track 36×20px, thumb 16px vuông; vùng tương tác ≥44×32px với label.
- **Interaction states:** Pending chặn toggle trùng, failure trả về trạng thái server và báo lỗi, không báo On trước xác nhận.
- **Keyboard/accessibility:** Role switch/aria-checked hoặc native checkbox styled có semantics phù hợp; Space; focus không mất khi response về.
- **Quy tắc sử dụng:** Setting như Tự sao lưu, sau consent hợp lệ; default off theo contract.
- **Không nên dùng:** Không thay checkbox consent, không dùng cho Start job/nhận quyền, không bật autosync ngầm.

### E8. Slider

- **Vai trò:** Điều chỉnh đại lượng liên tục trong khoảng có ý nghĩa.
- **Cấu trúc:** Label + range + numeric input + đơn vị + reset khi có default.
- **Variants:** Volume, zoom giao diện, brightness; seek dùng cùng primitive nhưng timecode semantics riêng.
- **Kích thước:** Track thị giác 4px, thumb vuông 12px trong vùng thao tác ≥24px; row 36px.
- **Interaction states:** Hover/drag/focus/disabled/invalid; live preview khi kéo, commit history một transaction khi kết thúc.
- **Keyboard/accessibility:** Arrow một step; Home/End min/max; numeric cho giá trị chính xác; aria-valuetext có đơn vị. Không capture phím khi không focus.
- **Quy tắc sử dụng:** Giá trị hữu hạn có min/max/step domain; numeric là phương án thay thao tác kéo.
- **Không nên dùng:** Không slider duy nhất cho timestamp chính xác; không tự thêm property speed/rotation khi chưa supported.

### E9. Tabs

- **Vai trò:** Đổi nội dung cùng một vùng, không phải điều hướng project.
- **Cấu trúc:** Tablist + tab + tabpanel IDs nối controls/labelledby; indicator 2px + label.
- **Variants:** Horizontal, vertical; Media/Văn bản/Lyrics/Hiệu ứng/Templates; Lyrics ba mode riêng.
- **Kích thước:** Cao 40px; label 13/20; có horizontal scroll nội bộ nếu nhãn dài, không cắt tab mất lối vào.
- **Interaction states:** Active/hover/focus/disabled/loading; active marker khác focus outline; tab switch không discard draft.
- **Keyboard/accessibility:** Roving tabindex; Arrow theo trục, Home/End; Enter/Space activate. Manual activation nếu nội dung chậm; Tab rời tablist sang panel.
- **Quy tắc sử dụng:** Một cấp tool tabs và một cấp Lyrics modes có nhãn; giữ controller/draft ngoài tab content.
- **Không nên dùng:** Không menu giả tab, không remount authority/session, không thêm tab AI trùng Lyrics Recognition theo ảnh.

### E10. Tooltip

- **Vai trò:** Giải thích ngắn cho icon hoặc tên bị rút gọn.
- **Cấu trúc:** Anchor + tooltip text; liên kết describedby; nền elevated opaque/viền control.
- **Variants:** Text only; full-name tooltip không thay dialog xem/copy khi cần.
- **Kích thước:** Max-width 280px, padding 8px; không chứa nút/link; typography 12/16.
- **Interaction states:** Hover/focus show sau 400ms, Escape dismiss; không tự biến mất khi con trỏ vào tooltip.
- **Keyboard/accessibility:** Không lấy focus; đóng bằng Escape; label của icon đã tồn tại độc lập tooltip.
- **Quy tắc sử dụng:** Thông tin bổ trợ, không che target/focus; đặt lại vị trí khi gần viewport edge.
- **Không nên dùng:** Không dùng cho lỗi bắt buộc, consent, form hay lý do disabled chỉ truy cập được bằng hover.

### E11. Popover

- **Vai trò:** Hiển thị tùy chọn hoặc nội dung phụ không cần modal.
- **Cấu trúc:** Trigger + anchored surface + heading nếu dài + controls + close khi cần; portal dưới app theme scope.
- **Variants:** Action menu (menu pattern), thông tin chi tiết, filter form (dialog non-modal/group); không áp role menu cho mọi form.
- **Kích thước:** Width 240–360px, padding 12px, max-height theo viewport trừ 32px; scroll nội bộ.
- **Interaction states:** Open/closed/loading/error, trigger aria-expanded; không làm document tăng kích thước.
- **Keyboard/accessibility:** Escape đóng/return focus; form dùng Tab bình thường, action menu dùng Arrow; click ngoài đóng khi không gây mất draft chưa xác nhận.
- **Quy tắc sử dụng:** Ít controls/ngắn, show tên đầy đủ hoặc chi tiết lỗi, giữ origin focus.
- **Không nên dùng:** Không nested popover nhiều tầng cho lyrics dài; không chứa luồng takeover/restore có cảnh báo quan trọng.

### E12. Dialog / Modal

- **Vai trò:** Tác vụ tập trung như Export hoặc xác nhận restore/xóa; Storage Manager dùng workspace riêng theo ST-01 đã duyệt, không đặt toàn bộ manager trong dialog.
- **Cấu trúc:** Title + optional description + body scroll + footer actions + close; background inert khi modal.
- **Variants:** Confirm (480px), form thường (640px); Export dùng dialog lớn hai cột theo [UI-04](UI_04_EXPORT_WORKSPACE.md), kích thước cụ thể chờ thử nghiệm; không dùng biến thể Storage960px cho toàn bộ manager. Workspace Storage theo UI-03/ST-01 Approved for Design.
- **Kích thước:** Width min(preset, viewport−32px), max-height viewport−32px; header/footer cố định, body min-height 0/overflow.
- **Interaction states:** Open/pending/invalid/error/result; pending không đồng nghĩa đóng bị cấm; lỗi ở trong dialog và giữ input.
- **Keyboard/accessibility:** Focus vào title hoặc control phù hợp, Tab trap, Shift+Tab, Escape/close, trả focus. Destructive focus action an toàn; heading labelledby.
- **Quy tắc sử dụng:** Đóng UI không hủy job; cần action Hủy tác vụ riêng có xác nhận trạng thái backend.
- **Không nên dùng:** Không portal ra khỏi tokens mà mất theme; không modal tự bật khi heartbeat lỗi; không close đồng nghĩa upload canceled.

### E13. Toast / Notification

- **Vai trò:** Xác nhận ngắn không chặn thao tác; lỗi cần xử lý nằm persistent inline/banner.
- **Cấu trúc:** Icon + message + optional action + close; một vùng announcements được quản lý.
- **Variants:** Success/info/warning/error; persistent banner là biến thể cho conflict/offline/failed save.
- **Kích thước:** Width 320–400px, padding 12px, gap 8; tối đa 3 toast, phần còn lại có lịch sử/inline.
- **Interaction states:** Appear/dismiss/pause-on-hover-focus; success tham khảo 6s, có action hoặc error không tự tắt.
- **Keyboard/accessibility:** role=status cho thông tin, alert chỉ lỗi mới cần chú ý ngay; action keyboard reachable, không lấy focus tự động; reduced motion.
- **Quy tắc sử dụng:** “Đã lưu project” sau xác nhận hash, kèm trạng thái lưu bền vững ở header.
- **Không nên dùng:** Không toast-only cho 409/save fail/missing media; không báo mọi poll/từng frame làm screen reader nói liên tục.

### E14. Progress Bar

- **Vai trò:** Phản ánh tiến độ job/thao tác do backend cung cấp.
- **Cấu trúc:** Nhãn job + phase + progress indicator + message + cancel nếu hỗ trợ.
- **Variants:** Determinate khi có numerator/denominator đáng tin; indeterminate khi chỉ biết phase; blocked/waiting riêng.
- **Kích thước:** Bar 4px, status row ≥32px; chi tiết trong workspace task; không làm toolbar cao lên.
- **Interaction states:** Queued/waiting/running/cancelling/cancelled/failed/interrupted/succeeded; không 100% khi mới queued.
- **Keyboard/accessibility:** Native progress có label; unknown bỏ value; custom role progressbar với value phù hợp. Throttle announcements theo phase/mốc; nút hủy riêng.
- **Quy tắc sử dụng:** Thông báo phase thật; “Đang chờ đủ tài nguyên” không fake timer phần trăm.
- **Không nên dùng:** Không bịa % upload/download khi backend chưa cấp (D-03); không đổi job thành succeeded khi chỉ request accepted.

### E15. Media Card

- **Vai trò:** Duyệt/chọn/xem trước/thêm media vào project.
- **Cấu trúc:** Thumbnail hoặc icon fallback + tên + kind/mime/duration khi biết + actions riêng; audio audition/video preview.
- **Variants:** Grid/list; image/video/audio; missing/error/loading; readonly vẫn cho xem.
- **Kích thước:** Grid min-width 120px trong tool panel, thumb aspect 4:3; list thumb 48×36; row actions 32px.
- **Interaction states:** Hover/selected/focused/importing/thumbnail-error/disabled-add; retry thumbnail không tự xóa asset.
- **Keyboard/accessibility:** Article/list item; nút chọn/Thêm/Nghe riêng có tên file; không nested buttons; Enter chọn, thêm bằng action; kéo có numeric/list alternative.
- **Quy tắc sử dụng:** Metadata unknown ghi “Chưa có thông tin”, ảnh không duration ghi “—”; tag/search theo dữ liệu thật. Tên đầy đủ accessible.
- **Không nên dùng:** Không chế waveform/duration từ filename; không tạo one-click add khi intent đang audition; không mutate media gốc.

### E16. Project Card

- **Vai trò:** Mở project local/recent và truy cập quản lý theo context.
- **Cấu trúc:** Tên + thumbnail thật hoặc placeholder nhận diện template + recent metadata khi có + Open + menu.
- **Variants:** Recent/project list/empty/error; không coi rowid tạo project là thời gian mở.
- **Kích thước:** Min-width 200px Dashboard, thumbnail 16:9, body padding 12px; tên tối đa hai dòng.
- **Interaction states:** Hover/focus/opening/missing/unavailable; current marker; disabled reason không chỉ màu.
- **Keyboard/accessibility:** Tên/Thẻ mở là button hoặc link theo routing thực; menu sibling, không nested interactive; keyboard tới Open và menu.
- **Quy tắc sử dụng:** D-01 history xuyên phiên sau contract được duyệt; card mở qua dirty/navigation guard hiện có.
- **Không nên dùng:** Không hiển thị timestamp/clip-count/cover giả như dữ liệu thật; không lấy Creative plan/quota trong ảnh làm chức năng.

### E17. Contextual Inspector Field

- **Vai trò:** Chỉnh property đúng selected clip/project và quyền hiện tại.
- **Cấu trúc:** Field group label + control/numeric+slider + unit + reset + helper/error; property/source identifier nội bộ.
- **Variants:** No selection project; image/video/audio/text/lyrics/Music Card theo capability; read-only value có thể copy.
- **Kích thước:** Một cột 280–320px; field gap 12px; label trên, numeric+unit hàng ngang; reset target 32px.
- **Interaction states:** Dirty local/focus/valid/invalid/disabled-reason/read-only; reset chỉ property supported, không reset cả project.
- **Keyboard/accessibility:** Tab có thứ tự; slider/numeric semantics; property name tiếng Việt và đơn vị; giữ focus khi preview rerender; reason describedby.
- **Quy tắc sử dụng:** Một gesture commit một history command; validate trim/source/ticks và mutation qua controller đã nghiệm thu R0.
- **Không nên dùng:** Không cập nhật từ stale selection callback; không thêm rotation/layout progress advanced chỉ vì ảnh minh họa; không đặt Export form trong Inspector.

### E18. Timeline Track Header

- **Vai trò:** Nhận diện, chọn và điều khiển track theo capability.
- **Cấu trúc:** Icon + tên/loại + current indicator + reorder actions; visibility/lock chỉ nếu được triển khai/phê duyệt.
- **Variants:** Background/music/text/lyrics; selected/empty; không hardcode số tracks.
- **Kích thước:** Width 144px, row 48px (dense 40), toolbar targets32; sticky theo scroll ngang.
- **Interaction states:** Hover/current/focus/read-only; read-only chặn reorder, giữ selection.
- **Keyboard/accessibility:** Tên track accessible; reorder buttons có tên và hướng, báo vị trí mới bằng status; drag chỉ bổ trợ.
- **Quy tắc sử dụng:** Header đồng bộ row position/scroll với tracks; nhiều controls đưa menu có nhãn.
- **Không nên dùng:** Không đặt icon eye/lock hoạt động giả; không chỉ kéo reorder; không đổi track kind ngoài contract.

### E19. Timeline Clip

- **Vai trò:** Biểu diễn interval và chọn/move/trim theo phạm vi supported.
- **Cấu trúc:** Clip rectangle vuông + type icon + nhãn + optional real thumbnail/waveform + selection marker; playhead riêng.
- **Variants:** Image/video/audio/text/lyrics; current/selected/missing; màu loại khác status semantics có legend.
- **Kích thước:** Cao theo track trừ 8px; width/left tính ticks/zoom, không đặt min-width làm sai thời gian; trim target 24px nếu có handles được duyệt.
- **Interaction states:** Hover/selected/focus/drag/trim/invalid/read-only; selected line 2px, focus outline ngoài khác nét; ghost drag không đổi source đến commit.
- **Keyboard/accessibility:** Button/select semantics, accessible name loại+tên/thời gian; Enter/Space chọn; numeric Inspector thay move/trim; Escape hủy gesture; tránh hàng nghìn tab stops bằng navigation có thiết kế riêng.
- **Quy tắc sử dụng:** Tôn trọng timebase48k, frame rounding/domain; giữ source lyrics mapping, single undo transaction; numeric trim đã có.
- **Không nên dùng:** Không pattern gradient giả waveform; không hiển thị split/snap/duplicate/visibility như đã supported; không đổi project khi chỉ focus/seek.

### E20. Resizable Separator

- **Vai trò:** Đổi chiều cao Timeline trong bounds, không làm thay content.
- **Cấu trúc:** Separator focusable + visual 1px divider + hit zone 24px + label/value + numeric height/reset trong menu bố cục.
- **Variants:** Horizontal giữa workspace/Timeline; không collapse Timeline vì Preview/Timeline phải còn ở normal.
- **Kích thước:** Hit band cao24px, width workspace; min Timeline180px, max theo công thức §F; radius0.
- **Interaction states:** Hover/focus/drag/at-min/at-max; cursor row-resize; clamp khi đổi viewport; pointercancel/lostcapture/unmount dọn listener.
- **Keyboard/accessibility:** role=separator, aria-orientation=horizontal, controls Timeline, name “Chiều cao Timeline”, min/max/now và valuetext px. Up tăng Timeline8px, Down giảm8px; Shift bước32; Home min, End max. Enter mở numeric height; nút Reset riêng, không collapse.
- **Quy tắc sử dụng:** Pointer capture, cập nhật layout qua requestAnimationFrame; numeric input và Reset là phương án không cần drag. Save preference sau commit gesture, không sau mỗi pixel.
- **Không nên dùng:** Không dùng divider không focus làm duy nhất cách resize; không đưa panel height vào project/dirty/hash; không sao chép Enter-collapse từ splitter generic vì trái UI-02.

## F. Layout System — Proposed details, Approved structure

### F1. Dashboard

UI-01 vẫn **Proposed**, chưa chốt wireframe. Sidebar dự kiến 208px; content padding24, gap16, max-width1200px; header56. Tiêu đề h1 28/36, intro ngắn và ba template TPL-01/02/03 đặt **trước** recent projects. Ở 1366×768, dự toán template row240px gồm artwork+label/actions; header56 + intro120 + gap24 + row240 + padding48 =488px, còn chỗ bắt đầu recent. Đây là phép phân bổ, không phải browser evidence.

Ảnh minh họa đặt recent ngay sau hero và quick-start dưới; đề xuất điều chỉnh thứ tự để ba template có mặt ở vùng nhìn đầu theo UI-01. Thumbnail chứa nội dung thật; placeholder ghi rõ. Navigation có Dashboard/Dự án/Lưu trữ/Cài đặt theo luồng được duyệt; không tự thêm gói thuê bao, trang AI riêng hoặc link chết. Dashboard có thể page scroll; scroll lock Editor không được lan sang đây. Recent history xuyên phiên là D-01, cần metadata contract riêng; R1.A tokens không tự tạo timestamp mới.

### F2. Editor normal — ba cột, Timeline dock

Cấu trúc Approved từ UI-02; các con số và pseudocode dưới đây là Proposed, **chỉ là tài liệu**:

```text
EditorShell: block-size 100dvh; overflow hidden
rows: Header 56px | Workspace minmax(0,1fr) | Separator 24px | Timeline T | Status 32px
Workspace columns: Left 288px | Center minmax(0,1fr) | Inspector 288px
Left/Inspector: Header 40px | Content minmax(0,1fr) with overflow auto
Center: Preview minmax(0,1fr) | Transport 40px
Timeline: Toolbar 40px | Ruler 24px | Tracks minmax(0,1fr)
```

`min-height:0`/`min-width:0` toàn chuỗi grid/flex; body/html không cuộn khi Editor mount, khôi phục khi rời Editor; không đặt height cố định 470px cho Preview. Preview fit **contain**, giữ aspect 9:16/16:9/1:1, không sửa preset để vừa panel. Preview rectangle có dimension dương, transport và Timeline luôn trong viewport normal. Canvas scene và playhead lấy từ controller/composition hiện hữu. Left/Inspector cuộn riêng; Timeline cuộn ngang trên vùng time, dọc trên tracks. Track headers/ruler giữ đồng bộ, scrollbar không ép chiều rộng toàn app.

Left panel giữ năm tool tabs UI-02; Lyrics có Nhận dạng / Chỉnh sửa & Căn thời gian / Kiểu trình bày. Lyrics draft/model/job state không sống trong component dễ bị unmount khi chuyển tab. Inspector không selection → project; selection → đúng loại object. Export dùng dialog hai cột theo UI-04, Drive dùng Storage workspace riêng. Header chứa project/back/undo/redo/save status/lease/actions; status có link “Chi tiết” nếu dài, không chiếm thêm hàng đẩy Preview.

### F3. Timeline resize và bounds

Gọi `A = viewportHeight − 56 − 32 − 24` là tổng chiều cao Workspace+Timeline. Proposed: workspace minimum240px (đã gồm transport40), Timeline minimum180px. `Tmax = min(floor(0.55×A), A−240)`. `Tdefault = clamp(280,180,Tmax)`. Nếu `Tmax < 180`, không áp clamp sai/tràn: chuyển compact/insufficient-space state và giữ lối vào chuyển mode.

Tại 1366×768: A656, default T280, Workspace376; cột Center790px nếu Left/Right288. Tại 1920×1080: A968, Workspace688 khi T280. Timeline ở default có tracks216px sau toolbar/ruler. Separator24px đã được tính, không overlay hit area lên nút transport. Ruler/zoom không đổi content khi panel resize.

Pointerdown capture; đo dy từ điểm bắt đầu, kéo lên tăng T; update rAF và clamp; Escape/pointercancel phục hồi chiều cao đầu gesture. Keyboard/numeric/reset ở E20. Lưu T như UI preference có version ngoài project sau gesture; clamp lại theo viewport khi hydrate. D-04 persistence xuyên port/launcher restart cần contract riêng; không dùng localStorage cùng-origin làm lời hứa đủ xuyên phiên, không ghi vào project.view chỉ để né quyết định. Session fallback có thể dùng cho prototype sau khi được phép nhưng phải ghi rõ chưa đạt D-04.

### F4. Compact và fullscreen Preview — D-05

**Approved hướng, Pending Approval chi tiết.** Candidate normal ≥1280×720 CSS px. Compact candidate 960–1279px hoặc thiếu chiều cao: Left thành rail48px có nhãn accessible/tooltip, Center linh hoạt, Inspector240px vẫn hiện, tool mở panel tạm có close rõ. Timeline Tdefault220px/min180. Tool overlay chỉ mở do user, đóng trả focus; không tự che Preview vô thời hạn. Ba vùng Preview/Inspector/Timeline vẫn phải hiện ở trạng thái compact nghỉ. Không coi thông số candidate là viewport supported đã nghiệm thu.

Dưới960px hoặc chiều cao không đủ cho min rows: đề xuất thông báo thiếu không gian và cho chọn tool/Inspector drawer có nút mở rõ ràng, Preview/Timeline vẫn giữ; đây là nhánh compact cần PO review riêng về tiêu chí hiển thị đồng thời. Không âm thầm cắt action; không tuyên bố mobile Editor hoặc pass UI-ED-02 tại nhánh chưa kiểm này. UI thông báo/settings/dialog phải reflow; Timeline/canvas là vùng dữ liệu 2D cần kiểm pan riêng, không lấy ngoại lệ reflow cho toàn form.

Fullscreen Preview là mode riêng user chủ động, có Escape và nút Thoát; tạm ẩn chrome theo D-05, không coi đó là vi phạm “luôn hiển thị ở chế độ thường”. Giữ playhead/selection/panel sizes khi thoát, nhưng quyền lấy trạng thái hiện hành, không restore writable cũ. Không tự play/unmute/claim khi vào fullscreen; focus trả về trigger hoặc control tương đương. Kiểm OS/browser fullscreenchange cả khi user thoát bằng hệ thống.

### F5. Workspaces còn lại

| Vùng               | Bố cục đề xuất                                                                                                                | Bất biến                                                                                                                                          |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Storage Manager    | Workspace riêng theo ST-01 đã duyệt; bốn tab Tổng quan/Bản sao lưu/MP4 khôi phục/Cấu hình, vùng danh sách/details cuộn nội bộ | OAuth/consent/auto-off, manifest/checksum/no-overwrite theo ADR-0002; đóng không hủy transfer; D-03 progress/error/cancel thật cần contract riêng |
| Export             | Dialog lớn hai cột theo UI-04; trái real Preview/validation, phải config supported, header/footer cố định/body scroll                   | Queue khác success; render snapshot xác định; option chỉ từ supported presets, không thêm FPS trong mockup                                        |
| Project Management | Dashboard list/table, actions Open/Rename/Delete/Recovery/Package theo capability                                             | Dirty guard, restore explicit, manual vs portable phân biệt; không overwrite local đang edit                                                      |
| Settings           | Section list và form một cột, footer Lưu/Đặt lại khi semantics yêu cầu                                                        | Tùy chọn UI ngoài project, không lease/session secrets; native folder picker vẫn backend grant, không nhập arbitrary path để cấp quyền            |

Chưa có routing/workspace implementation cho bảng này. R1 chỉ thiết kế primitive và Dashboard sau gate; R3/R4/R5 mới chuyển các vùng theo plan.

## G. States & Feedback

Quyền, dirty và job là ba trục độc lập. Ví dụ có thể vừa “Chỉ đọc” + “Chưa lưu thủ công” + job running; không gộp thành một status xanh. UI hiển thị tiếng Việt, không đổi code status backend hay persist enum mới. Một vùng status tổng hợp và lỗi gần control; không phát screen-reader announcement ở mỗi heartbeat/frame.

| Trạng thái             | Hiển thị / hành động                                                                         | Semantics & giới hạn                                                                                                   |
| ---------------------- | -------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Loading                | Placeholder giữ box, “Đang tải thư viện…”                                                    | aria-busy vùng; không giả waveform/output; không giấu toàn shell                                                       |
| Empty                  | “Chưa có media. Nhập file để bắt đầu.” + action hợp lệ                                       | Không render danh sách mẫu như dữ liệu thật                                                                            |
| Hover                  | Viền/control sáng hơn, không đổi kích thước                                                  | Không là cách duy nhất biết chức năng                                                                                  |
| Selected               | Marker/viền + tên/selected state                                                             | Tách focus, loại clip bằng icon/chữ                                                                                    |
| Focus                  | Outline2px, offset2px, đủ contrast                                                           | Không outline:none nếu không có thay thế; không bị panel overflow cắt                                                  |
| Disabled               | Nút bất hoạt + “Cần chọn clip để tiếp tục.”                                                  | Native disabled không Tab; reason ở ngoài target luôn đọc được; aria-disabled tự chặn handlers nếu cần focus discovery |
| Read-only              | “Chỉ đọc — project đang được sửa ở tab khác.” + Nhận quyền                                   | Giữ copy/seek/select; pending quyền không editable; capability từng action, không disable toàn app                     |
| Unsaved                | “Chưa lưu thủ công”                                                                          | Working autosync không clear; không giấu vì job succeeded                                                              |
| Saving                 | “Đang lưu bản đã chọn…”                                                                      | Chặn save trùng nhưng không khóa edits khác khi policy hiện hữu cho phép                                               |
| Saved                  | “Đã lưu bản được chọn.”                                                                      | Nếu B đã save nhưng C dirty, vẫn hiện Chưa lưu thủ công; không set sạch bằng job success                               |
| Conflict               | “Project đã thay đổi. Bản nháp đang giữ trong tab này.” + action reload/takeover có xác nhận | Không auto PATCH với revision mới; không toast-only                                                                    |
| Error                  | Lỗi cụ thể + hướng thử lại; field invalid có đơn vị/range                                    | aria-invalid/description, focus tới lỗi đầu khi submit; không chuyển message server thành success                      |
| Job                    | Phase thật, phần trăm nếu có + Hủy tác vụ nếu hỗ trợ                                         | “Đang chờ tài nguyên” khác “Đang xuất”; cancelRequested khác cancelled; giữ job khi đóng dialog                        |
| Offline / disconnected | “Mất kết nối dịch vụ local” hoặc “Google Drive chưa kết nối”                                 | Hai tình huống khác nhau; Drive lỗi không khóa local edit, API/lease uncertain chặn ghi                                |
| Missing media          | Tên asset + “Chọn lại file gốc” theo flow relink                                             | Không xóa clip/source tự động, vẫn cho đọc thông tin                                                                   |
| Recoverable / fatal    | Retry tại nguồn hoặc hướng tải lại Studio; fatal giữ vùng báo lỗi truy cập được              | Không loop auto reload mất draft; không log token/path riêng tư                                                        |

Pending takeover label “Đang kiểm tra quyền…”, nút busy; hoàn tất chỉ sau controller xác minh. R0 đã nghiệm thu không cho phép DS sửa epoch/heartbeat/TTL. Đánh giá lại regression khi đổi DOM, không viết authority vào primitive status.

## H. Motion & Interaction

Proposed: micro color/opacity100–150ms ease-out; dialog/popover tối đa150ms, không scale/bounce; tooltip delay400ms; không animation chuyển panel khi kéo Timeline. `prefers-reduced-motion: reduce` bỏ transition/decorative loading animation, vẫn có text tiến trình. Không thêm motion library.

Preview/clip content animation là nghiệp vụ composition riêng; reduced motion của shell không sửa output video user. Có Pause Preview rõ ràng, không autoplay để minh họa effect. Hover/pressed chỉ đổi color/border; không translate/zoom làm target dịch. Playhead/drag đi sát dữ liệu, không easing hoặc tween để che lag. Khi body font/thumbnail tải, reserve box; không fade toàn chrome hoặc giấu text/function đợi font.

Không bố trí status text làm co giãn Header; lỗi dài đọc trong banner/details có scroll riêng hoặc dialog khi user chọn. Không chỉ truncation rồi bỏ message. Scroll panel không đưa selection/seek đến vị trí mới ngoài ý muốn.

## I. Accessibility

Mục tiêu là **WCAG 2.2 AA khi triển khai**, chưa là chứng nhận conformance. Tài liệu này kiểm số màu và định nghĩa hành vi; chưa chạy screen reader/zoom/browser trên thiết kế mới.

- Tab order theo DOM hợp lý: back/project/header → Left tools → Preview controls → Inspector → resize → Timeline; có skip links/region labels để không Tab qua hàng trăm clip. Không positive tabindex. Keyboard shortcuts chỉ xử lý khi không nhập text hoặc mở modal; không override Ctrl+Z native trong text field.
- Native labels/fieldset/legend khi có nhóm; ảnh decorative alt rỗng, thumbnail có tên nếu truyền nội dung. Focus luôn thấy, không bị sticky header hoặc toast che; invalid reason đọc bằng describedby. Không sử dụng màu/âm thanh đơn lẻ.
- Action target floor24×24 CSS px, ưu tiên32; drag có numeric/buttons alternative; kiểm tiêu chí ngoại lệ thực tế trước kết luận. Theo [WCAG target size](https://www.w3.org/TR/WCAG22/#target-size-minimum) và [dragging movements](https://www.w3.org/TR/WCAG22/#dragging-movements).
- Dialog theo [WAI-ARIA APG modal](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/), tabs theo [APG tabs](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/); labels/keys cụ thể ở E9/E12. Không tự gán roles mà bỏ hành vi.
- Slider theo [APG slider](https://www.w3.org/WAI/ARIA/apg/patterns/slider/), separator tham khảo [APG Window Splitter](https://www.w3.org/WAI/ARIA/apg/patterns/windowsplitter/). APG splitter còn lưu ý review chưa hoàn tất; đây là guidance, cần assistive-technology test. Dự án chủ động dùng Enter mở numeric thay collapse, ghi hướng dẫn ngay cạnh control; Up tăng chiều cao Timeline, Down giảm; Home/End giữ min/max, không ẩn Timeline.
- Tooltip hover/focus có thể dismiss/hover/persist khi cần; popover có actions không dùng role tooltip. Status chỉ announce thay đổi ý nghĩa; playhead update visual có timecode đọc được khi focus, không aria-live60FPS.
- Chuẩn bị NVDA trên Windows + Chromium, keyboard-only, text zoom200%, browser zoom200/400%, forced-colors, reduced-motion, Vietnamese IME và fallback glyph. Forms/settings/notifications reflow ở320CSSpx; vùng canvas/timeline2D được đánh giá riêng, không blanket exemption cho shell.
- Kiểm narrow panel/long file name, disabled reason, modal focus return, restored fullscreen focus, separator target/movement numeric. Automated axe nếu được chọn sau không thay review thủ công; chưa thêm dependency.

## 10. Bảo toàn nghiệp vụ và mapping sang giai đoạn

| Ràng buộc              | DS hỗ trợ                                                             | Không được thay                                                                                              |
| ---------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| R0 lease đã nghiệm thu | Status/disabled reason/focus feedback, không callback authority riêng | Epoch, claim-confirm-load, retry revision, heartbeat5s/TTL30s, không auto takeover                           |
| Manual Save/History    | Các trạng thái G và field gesture transaction                         | Dirty hash/manualSavedHash, B-save/C-edit, snapshot pins                                                     |
| Shared Preview/MP4     | Chrome scope và aspect contain                                        | Scene styles/fonts/output codec, timeline timebase48k                                                        |
| Lyrics                 | Tabs/modes/status đúng Draft/Reviewed/Applied                         | Parser/alignment confidence/AI review explicit, không tự apply                                               |
| Drive                  | Manager primitives và truthful progress                               | Consent/auto-off/manifest/checksum/no-overwrite; progress/cancel capability chưa triển khai phải có contract |
| D-01/D-04              | Project card và separator UI không mutate content                     | Persistence xuyên port chưa được tự chọn API/DB; chỉ proposal                                                |
| D-02/D-06              | Inspector/media hiển thị field hiện hữu, unknown fallback             | Advanced property và DTO delta phải được duyệt trước; Recommended khác Approved                              |

DS-P07 đã duyệt triển khai R1 theo từng phần: R1.A tokens + primitives + state specimens **được gắn nhãn kiểm thử**, không thay màn hình hoạt động; R1.B Dashboard integration sau wireframe/D-01/navigation contract còn lại. Không gộp Advanced Editor. R3 layout, R4 typed panels, R5 Storage/Export, R6 regression tiếp tục theo plan. Quyền triển khai theo từng phần đến từ DS-P07, không đến từ việc tạo tài liệu; không bao gồm backend Drive hoặc API/schema delta chưa duyệt.

## 11. Quyết định PO — DS-P01…DS-P08

**Ngày quyết định:** 24/11/2026 (Asia/Saigon). **Nguồn:** bảng DS-P01…DS-P08 do PO gửi trong hội thoại sau khi tài liệu v1.0 được push ở commit `4681031`. Ghi nhận đúng phạm vi dưới đây, không biến duyệt thử nghiệm thành test Passed.

| ID     | Nội dung               | Quyết định PO                                              | Trạng thái / giới hạn                                                                                                                                  |
| ------ | ---------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| DS-P01 | Bảng màu               | Duyệt palette hiện tại                                     | **Approved**: bảng B gồm semantic, viền control/focus; contrast runtime còn cần kiểm                                                                   |
| DS-P02 | Font chữ               | Segoe UI cho giao diện v1; cân nhắc Inter sau              | **Approved** Segoe UI; Inter/Noto Serif không thêm trong v1 nếu chưa có quyết định mới                                                                 |
| DS-P03 | Kích thước             | Duyệt body14px, label13px, caption12px                     | **Approved** ba cỡ chữ; không tự gọi mọi heading/control/breakpoint đã được nghiệm thu                                                                 |
| DS-P04 | Component và tương tác | Duyệt, bắt buộc keyboard và trạng thái lỗi rõ              | **Approved for design** E/G/I; mỗi phần triển khai phải có evidence keyboard/error, không che lỗi nghiệp vụ                                            |
| DS-P05 | Layout responsive      | Duyệt thử nghiệm ở1366×768 và1920×1080                     | **Approved for trial** hai viewport; Compact Mode/breakpoint nhỏ hơn, kích thước thực và nghiệm thu geometry còn phải review/test                      |
| DS-P06 | Dashboard              | Duyệt template trước, dự án gần đây sau                    | **Approved** thứ tự nội dung; UI-01 chưa thành Approved toàn bộ wireframe, recent persistence cần contract                                             |
| DS-P07 | Phạm vi R1             | Duyệt triển khai theo từng phần, không gộp Advanced Editor | **Approved phased implementation**: R1.A foundations trước, R1.B Dashboard sau dependency; không cấp quyền tự commit/push/merge hoặc API/schema mới    |
| DS-P08 | Google Drive UI-03     | Cần hoàn thiện tài liệu riêng                              | **Approved for Design**: [UI-03/ST-01…ST-07](UI_03_STORAGE_MANAGER.md#storage-decisions) được PO duyệt; transfer API contracts chi tiết vẫn cần review |

**Còn cần chốt:** UI-01 wireframe chi tiết/navigation; contract recent/preferences D-01/D-04; kích thước/breakpoint compact ngoài hai viewport thử; typography ngoài font UI và ba body sizes; delta kỹ thuật UI-03 progress/error/cancel và retention/history; ST-01…ST-07 đã duyệt, không cần xác nhận lại. D-06 không được chuyển khỏi Recommended qua bảng này.

## 12. Verification & handoff

Đã khảo sát static code, tính contrast ở B2, đối chiếu tài liệu/ảnh tham chiếu và W3C primary sources ngày24/11/2026. Không sửa ứng dụng hoặc cài fonts/libraries; không chạy UI/build/regression mới cho một thay đổi chỉ có tài liệu. Test R0 được liên kết như evidence lịch sử và PO acceptance riêng, không tính là pass Design System.

Theo quyền triển khai từng phần DS-P07, khi thực thi mỗi phần R1: kiểm contrast của computed styles và mọi state; button/field/tab/tooltip/popover/dialog/progress/separator keyboard+NVDA; dirty/lease R0 dev+production; scene CSS leakage; two desktop viewports, compact/zoom/reduced motion, Vietnamese/long names/loading/error. Trình screenshots state matrix và browser evidence trước tuyên bố UI-ED/DS pass. UI-01 Proposed và UI-02 nguyên văn vẫn giữ, không rewrite spec được duyệt.

## 13. UI-03/UI-04 — ảnh minh họa và nguồn Approved mới

PO cung cấp hai ảnh UI-03/UI-04 cùng [UI-04 Export Workspace](UI_04_EXPORT_WORKSPACE.md) nguyên văn **Approved for Design — Not Implemented**. UI-03 là workspace riêng theo ST-01…ST-07, không manager modal960px. UI-04 là modal hai cột góc vuông; Escape/Close chỉ đóng view, không cancel render. Job tracking/reopen ở application controller/Editor, không thuộc component dialog. Hai quyết định này thay các phương án Export workspace/dialog640 generic trước đó; không thay UI-02 nguyên văn hoặc thiết kế Storage đã chốt.

Ảnh chỉ minh họa: badge connected/folder sample, placeholder Preview/check xanh/custom MP4 name không là capability/evidence thật. Export Preview phải dùng composition thật; filename/preflight/metadata/error contracts còn cần review trong UI-04 phụ lụcH. Số đo1000px là Proposed, không Approved từ ảnh. Chưa sửa UI/CSS hoặc chạy tests mới trong lượt cập nhật tài liệu.
