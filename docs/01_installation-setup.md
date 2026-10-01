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
docker compose ps
```

Trên Windows PowerShell, dùng `Copy-Item .env.example .env` thay lệnh `cp`. File `.env` chứa cấu hình local và đã được Git bỏ qua. Lần đầu Docker cần tải image và cài package nên có thể mất vài phút.

## 3. Kiểm tra service

- FastAPI: mở `http://localhost:8000/docs`, thử hai endpoint trong nhóm **Health** bằng **Try it out → Execute**.
- PostgreSQL: `docker compose exec db pg_isready -U flashcards -d flashcards`; kết quả mong đợi là `accepting connections`.
- Vào SQL shell: `docker compose exec db psql -U flashcards -d flashcards`.
- Xem log API: `docker compose logs -f api`.

Compose cấp `DATABASE_URL` cho API với hostname `db` trong mạng nội bộ.

Hai endpoint kiểm tra không cần đăng nhập và không ghi dữ liệu:

| Endpoint | Kết quả mong đợi |
| --- | --- |
| `GET /api/health/models` | `status: "ok"`, `model_count: 13` và danh sách model kèm quan hệ đã được SQLAlchemy resolve; ví dụ `Card` có `deck: "Deck"`, `word: "Word"`. |
| `GET /api/health/db` | `{"status":"ok","database":"connected"}` khi session thực hiện được `SELECT 1`; trả `503` nếu database không kết nối được. |

Có thể mở trực tiếp hai URL trên trình duyệt hoặc chạy:

```bash
curl http://localhost:8000/api/health/models
curl http://localhost:8000/api/health/db
```

Endpoint models chỉ kiểm tra cấu hình ORM, không truy vấn database. Endpoint db chỉ kiểm tra kết nối; cả hai không tạo bảng và không xác nhận schema đã được migrate.

## 4. Lệnh dùng khi phát triển

| Việc | Lệnh |
| --- | --- |
| Chạy lại service | `docker compose up -d` |
| Xem trạng thái | `docker compose ps` |
| Xem log tất cả service | `docker compose logs -f` |
| Build lại sau khi sửa `requirements.txt` hoặc `Dockerfile` | `docker compose up --build -d` |
| Dừng container, giữ dữ liệu PostgreSQL | `docker compose down` |

Code trong `backend/` được mount vào container và API tự reload khi sửa file. Không dùng `docker compose down -v` trừ khi muốn xóa dữ liệu local trong volume PostgreSQL.

Nếu gặp `failed to connect to the docker API ... docker.sock`, mở Docker Desktop, chờ Engine chạy rồi kiểm tra lại `docker info`. Nếu cổng `8000` hoặc `5432` đã được dùng, đổi phần bên trái của mapping cổng trong `compose.yaml`.
