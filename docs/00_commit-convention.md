# Commit Protocol & Convention

## 1. Mục tiêu

### 1.1. Phạm vi

Áp dụng cho mọi commit trong repo. Dùng [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) để lịch sử thay đổi dễ đọc, tìm kiếm và tổng hợp.

### 1.2. Nguyên tắc

Một commit nên chứa một thay đổi logic có thể review. Commit code và tài liệu liên quan cùng nhau khi chúng phụ thuộc nhau. Không commit secret, `.env`, file sinh ra khi chạy local hoặc code chưa hoạt động chỉ để lưu tạm.

## 2. Cấu trúc commit message

### 2.1. Cú pháp

```text
<type>(<scope>): <summary>

[body]

[footer]
```

`scope` có thể bỏ qua nếu thay đổi ảnh hưởng toàn project. `body` và `footer` là tùy chọn, trừ khi có breaking change.

### 2.2. Dòng tiêu đề

1. Viết bằng tiếng Anh để giữ format nhất quán với tên code và tooling.
2. Dùng động từ ở dạng mệnh lệnh hoặc mô tả hành động ngắn: `add`, `fix`, `update`, `remove`.
3. Viết chữ thường ở đầu `summary`, không thêm dấu chấm cuối.
4. Cố gắng giữ dòng tiêu đề tối đa 72 ký tự.

## 3. Các `type` được dùng

| Type | Khi sử dụng |
| --- | --- |
| `feat` | Thêm chức năng cho người dùng hoặc API |
| `fix` | Sửa hành vi sai |
| `docs` | Chỉ thay đổi tài liệu |
| `refactor` | Đổi cấu trúc code nhưng không đổi hành vi |
| `test` | Thêm hoặc sửa test |
| `chore` | Việc bảo trì, dependency, cấu hình thông thường |
| `build` | Dockerfile, Compose, build hoặc packaging |
| `ci` | Pipeline CI/CD |
| `perf` | Cải thiện hiệu năng có đo lường |
| `revert` | Hoàn tác commit trước |

Chọn type theo tác động chính của commit. Ví dụ: thêm API kèm test vẫn là `feat`, sửa bug kèm test vẫn là `fix`.

## 4. Các `scope` khuyến nghị

### 4.1. Scope theo feature

`auth`, `decks`, `cards`, `dictionary`, `reviews`, `quizzes`, `statistics`.

### 4.2. Scope hạ tầng

`db`, `docker`, `api`, `deps`, `docs`, `ci`.

Không cần tạo scope mới nếu scope hiện có mô tả được thay đổi. Scope không phải tên người làm hoặc mã issue.

## 5. Body, footer và breaking change

### 5.1. Body

Dùng body khi tiêu đề chưa giải thích đủ: nêu lý do đổi và quyết định đáng chú ý. Để một dòng trống giữa tiêu đề và body.

### 5.2. Breaking change

Nếu API/schema thay đổi khiến client hoặc dữ liệu cũ không còn tương thích, thêm `!` sau type/scope và ghi `BREAKING CHANGE:` trong footer. Nêu rõ người dùng cần làm gì để nâng cấp.

```text
feat(auth)!: require bearer tokens on deck endpoints

BREAKING CHANGE: clients must send Authorization: Bearer <token>.
```

### 5.3. Issue reference

Nếu team dùng issue tracker, đặt mã issue ở footer, ví dụ `Refs: #42`. Không ép gắn issue cho mọi commit.

## 6. Quy trình trước khi commit

### 6.1. Kiểm tra thay đổi

1. Chạy `git status` và `git diff --check`.
2. Đọc `git diff --staged` để chắc chắn chỉ stage các file cần thiết.
3. Chạy test hoặc kiểm tra liên quan đến phần đã sửa.
4. Nếu thay đổi database model, cập nhật [Architecture Convention](02_architecture-convention.md) khi thiết kế thay đổi; cập nhật [Installation & Setup Guide](01_installation-setup.md) khi cách chạy thay đổi.

### 6.2. Tạo commit

Stage file cụ thể bằng `git add <path>` và commit với message theo Mục 2. Tránh `git add .` nếu chưa kiểm tra toàn bộ file mới.

## 7. Ví dụ

### 7.1. Chức năng

```text
feat(auth): add user registration with hashed passwords
feat(cards): populate word details from dictionary API
feat(reviews): prioritize overdue cards in study sessions
```

### 7.2. Sửa lỗi và database

```text
fix(cards): reject moves to decks owned by another user
fix(reviews): prevent duplicate submissions from updating progress
feat(db): add quiz card result table
```

### 7.3. Tài liệu và hạ tầng

```text
docs(docs): add team setup guide and commit convention
build(docker): add api and postgres services
ci: run tests on pull requests
```

## 8. Pull request

### 8.1. Nội dung PR

Mô tả ngắn thay đổi, lý do, cách kiểm tra và tác động tới schema/API.

### 8.2. Review

Giữ PR đủ nhỏ để reviewer đọc được. Sửa nhận xét bằng commit mới trong lúc review; team có thể squash khi merge nếu muốn lịch sử nhánh chính gọn hơn, nhưng message cuối cùng vẫn theo convention này.
