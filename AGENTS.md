# AGENTS.md — AI Music Video Studio

## 1. Project Overview

**Project:** AI Music Video Studio

Ứng dụng web tạo và chỉnh sửa video âm nhạc từ ảnh/video và bài hát, có hỗ trợ AI nhận dạng lyrics, đồng bộ lời hát, tạo video theo template, chỉnh sửa trên multi-track timeline và xuất MP4.

### Product Principles

- Editor mạnh, linh hoạt nhưng dễ sử dụng.
- Giao diện hiện đại, tối giản, hoàn toàn bằng tiếng Việt.
- Template-first, automatic generation, edit-after-generation.
- Local-first, ưu tiên miễn phí.
- AI local là mặc định; Gemini/OpenAI API chỉ là tùy chọn.
- Desktop trước, mobile sau.
- Không tự ý mở rộng phạm vi MVP.

## 2. Source of Truth

Trước khi triển khai, phải đọc tài liệu có liên quan:

- `PRD_v1.0.md`
- `SRS_v1.0.md`
- `RTM_v1.0.md`
- `OPEN_QUESTIONS.md`

Thứ tự xử lý thông tin:

1. Yêu cầu trực tiếp của người dùng và các quyết định đã được phê duyệt.
2. PRD/SRS và các Architecture Decision Records đã phê duyệt.
3. Các quy tắc trong AGENTS.md.
4. Code và cấu trúc hiện có.

Nếu tài liệu mâu thuẫn hoặc thiếu quyết định quan trọng, phải báo cáo trước khi triển khai. Không tự ý coi một Open Question là đã được phê duyệt.

## 3. Git Workflow

Repository chỉ sử dụng hai nhánh chính:

- `main`: bản ổn định, đã nghiệm thu.
- `dev`: phát triển, nghiên cứu, kiểm thử và sửa lỗi.

### Quy tắc bắt buộc

- Chỉ được sửa code và tạo commit trên `dev`.
- Không commit trực tiếp vào `main`.
- Không tự tạo feature branch nếu người dùng không yêu cầu.
- Không tự push, merge, rebase hoặc tạo tag khi chưa được cho phép.
- Chỉ thực hiện Pull Request từ `dev` sang `main` khi người dùng yêu cầu phát hành.
- Không tự ý thay đổi lịch sử Git.

Trước khi sửa file, kiểm tra:

- `git status`
- `git branch --show-current`
- `git diff`

Nếu đang ở `main`, phải chuyển sang `dev` trước khi chỉnh sửa, sau khi kiểm tra các thay đổi chưa commit. Nếu không thể chuyển nhánh an toàn, phải báo cáo.

## 4. Commit Convention

Sử dụng Conventional Commits:

`type(scope): description`

Các type:

- `feat`: chức năng mới.
- `fix`: sửa lỗi.
- `docs`: tài liệu.
- `refactor`: tái cấu trúc.
- `test`: kiểm thử.
- `perf`: tối ưu hiệu năng.
- `chore`: bảo trì.
- `build`: build/dependency.
- `ci`: CI/CD.

Ví dụ:

- `docs(requirements): finalize SRS baseline`
- `feat(editor): implement multi-track timeline`
- `feat(lyrics): add lyric timing controls`
- `fix(audio): correct playback offset`
- `test(render): validate mp4 output`

Mỗi commit phải:

1. Có một mục đích logic rõ ràng.
2. Không chứa thay đổi ngoài phạm vi.
3. Không chứa secrets hoặc dữ liệu media cá nhân.
4. Được kiểm tra diff trước khi tạo.
5. Chỉ được tạo sau khi người dùng phê duyệt.

Không tự động commit sau mỗi thay đổi nhỏ.

## 5. Development Workflow

Với mỗi task, thực hiện theo thứ tự:

### Step 1 — Understand

- Đọc yêu cầu task và Acceptance Criteria.
- Đọc tài liệu liên quan.
- Kiểm tra code hiện có.
- Xác định các module bị ảnh hưởng.

### Step 2 — Plan

Trình bày:

- Mục tiêu.
- Các thay đổi dự kiến.
- File/module liên quan.
- Dependency.
- Rủi ro.
- Phương pháp kiểm thử.

Nếu task chỉ yêu cầu phân tích hoặc lập kế hoạch, dừng ở đây.

### Step 3 — Implement

Khi được giao triển khai:

- Chỉ sửa những phần cần thiết.
- Tôn trọng kiến trúc đã phê duyệt.
- Không thêm dependency không cần thiết.
- Không thực hiện refactor lớn ngoài phạm vi.
- Không hardcode secrets.
- Không tạo mock thay cho chức năng thực mà không ghi rõ.

### Step 4 — Verify

- Chạy test liên quan.
- Chạy lint/typecheck/build khi phù hợp.
- Kiểm tra kết quả thực tế.
- Ghi nhận những test chưa thể chạy.

### Step 5 — Report

Báo cáo:

- Công việc đã hoàn thành.
- File đã thay đổi.
- Test và kết quả.
- Các vấn đề còn tồn tại.
- Trạng thái Git.
- Commit message đề xuất.

Chờ người dùng phê duyệt commit hoặc công việc tiếp theo.

## 6. Technical Principles

### Frontend

- Ưu tiên Next.js, TypeScript và Tailwind CSS theo kiến trúc được phê duyệt.
- Component có trách nhiệm rõ ràng.
- Không đặt toàn bộ logic vào một component lớn.
- Không hardcode nội dung giao diện bằng tiếng Anh.
- Hạn chế phụ thuộc không cần thiết.

### Video Editor

- Timeline là nguồn dữ liệu thống nhất.
- Preview và renderer phải sử dụng cùng cấu hình.
- Chỉnh sửa phải hỗ trợ Undo/Redo khi thuộc phạm vi yêu cầu.
- Không làm mất dữ liệu project khi chỉnh sửa hoặc render.

### AI
