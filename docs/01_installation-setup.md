# Cài đặt và chạy

Cần Docker đang chạy và Docker Compose. Chạy tại thư mục gốc:

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec api python -m backend.app.db.init_db
```

Mở [Swagger UI](http://localhost:8000/docs) để thử API. Python và PostgreSQL chạy trong container, không cần cài riêng.

Trong `.env`, đổi `JWT_SECRET`; điền `RESEND_API_KEY` và `EMAIL_FROM` hợp lệ nếu dùng chức năng gửi email.

| Việc | Lệnh |
| --- | --- |
| Xem log API | `docker compose logs -f api` |
| Chạy lại | `docker compose up -d` |
| Build lại khi đổi dependency/Dockerfile | `docker compose up --build -d` |
| Dừng, giữ dữ liệu | `docker compose down` |

Code backend tự reload. `init_db` chỉ tạo bảng còn thiếu; đổi cấu trúc bảng đã tồn tại cần migration. `docker compose down -v` xóa dữ liệu PostgreSQL local.

Frontend thử API: xem [README](../README.md#frontend-đơn-giản-test-api).
