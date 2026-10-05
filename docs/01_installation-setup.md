# Cài đặt và chạy project

Guide này chỉ chứa các bước chạy môi trường dev. Tech stack, cấu trúc thư mục, requirements, ERD và API draft nằm ở [Architecture Convention](02_architecture-convention.md).

## 1. Chuẩn bị

Cài [Docker Desktop](https://docs.docker.com/desktop/) hoặc Docker Engine kèm Compose. Mở Docker Desktop và chờ Docker Engine chạy, rồi kiểm tra:

```bash
docker info
docker compose version
```

Python và PostgreSQL chạy trong container; không cần cài riêng trên máy để chạy project.

## 2. Chạy lần đầu

Trong thư mục gốc repo:

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec api python -m backend.app.db.init_db
docker compose ps
```

Trên Windows PowerShell, dùng `Copy-Item .env.example .env` thay lệnh `cp`. File `.env` chứa cấu hình local và đã được Git bỏ qua. Lần đầu Docker cần tải image và cài package nên có thể mất vài phút.

## 3. Kiểm tra service

- FastAPI: mở `http://localhost:8000/docs` để thử các endpoint auth và deck.
- PostgreSQL: `docker compose exec db pg_isready -U flashcards -d flashcards`; kết quả mong đợi là `accepting connections`.
- Vào SQL shell: `docker compose exec db psql -U flashcards -d flashcards`.
- Xem log API: `docker compose logs -f api`.

Compose cấp `DATABASE_URL` cho API với hostname `db` trong mạng nội bộ.

Lệnh `python -m backend.app.db.init_db` tạo các bảng còn thiếu và giữ dữ liệu hiện có. Chạy lệnh này trước khi thử API trên database mới. Lệnh không cập nhật cấu trúc của bảng đã tồn tại; thay đổi schema cần migration.

## 4. Lệnh dùng khi phát triển

| Việc | Lệnh |
| --- | --- |
| Chạy lại service | `docker compose up -d` |
| Xem trạng thái | `docker compose ps` |
| Xem log tất cả service | `docker compose logs -f` |
| Build lại sau khi sửa `requirements.txt` hoặc `Dockerfile` | `docker compose up --build -d` |
| Dừng container, giữ dữ liệu PostgreSQL | `docker compose down` |

Code trong `backend/` được mount vào container và API tự reload khi sửa file. Không dùng `docker compose down -v` trừ khi muốn xóa dữ liệu local trong volume PostgreSQL.

Mỗi khi update database: 
```
docker compose exec api python -m backend.app.db.init_db
```

Nếu gặp `failed to connect to the docker API ... docker.sock`, mở Docker Desktop, chờ Engine chạy rồi kiểm tra lại `docker info`. Nếu cổng `8000` hoặc `5432` đã được dùng, đổi phần bên trái của mapping cổng trong `compose.yaml`.
