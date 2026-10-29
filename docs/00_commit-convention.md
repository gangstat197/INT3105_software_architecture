# Quy ước commit

```text
<type>(<scope>): <summary>
```

- `type`: `feat` (chức năng), `fix` (sửa lỗi), `docs` (tài liệu), `refactor` (đổi cấu trúc), `test` (kiểm thử), `chore` (bảo trì), `build` (Docker/build), `ci` (pipeline), `perf` (hiệu năng), `revert` (hoàn tác).
- `scope` tùy chọn: `auth`, `decks`, `cards`, `reviews`, `quizzes`, `db`…
- `summary` ngắn, tiếng Anh, bắt đầu bằng chữ thường, không chấm cuối; ưu tiên tối đa 72 ký tự.

```text
feat(cards): add dictionary lookup
fix(reviews): reject duplicate submissions
docs: simplify setup guide
```

Mỗi commit chứa một thay đổi logic. Trước khi commit: đọc diff, chạy `git diff --check` và kiểm tra liên quan; không đưa secret, `.env` hay file sinh ra vào commit.

Breaking change: thêm `!` sau type/scope và footer `BREAKING CHANGE:` giải thích cách nâng cấp.

PR ghi ngắn thay đổi và cách kiểm tra. Cập nhật tài liệu trong cùng PR khi đổi API, thiết kế hoặc cách chạy.
