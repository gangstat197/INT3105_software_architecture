# Cài đặt môi trường phát triển

Backend và PostgreSQL đều chạy bằng Docker Compose. Máy chỉ cần cài [Docker Desktop](https://docs.docker.com/desktop/) (hoặc Docker Engine kèm Compose). `requirements.txt` được cài trong image backend khi build.

## 1. Tech stack và tài liệu

| Công nghệ | Dùng để làm gì | Tài liệu |
| --- | --- | --- |
| Python 3.12, FastAPI, Uvicorn | Viết và chạy HTTP API | [FastAPI tutorial](https://fastapi.tiangolo.com/tutorial/), đặc biệt `APIRouter` và dependencies |
| Pydantic | Kiểm tra request, định nghĩa response schema và cấu hình | [Pydantic models](https://pydantic.dev/docs/validation/latest/concepts/models/) |
| PostgreSQL 17 | Lưu users, decks, cards, quiz và exercise | [PostgreSQL tutorial](https://www.postgresql.org/docs/17/tutorial.html): bảng, khóa ngoại, query, transaction |
| SQLAlchemy 2 + psycopg | Ánh xạ Python models và truy vấn PostgreSQL | [SQLAlchemy ORM tutorial](https://docs.sqlalchemy.org/en/20/tutorial/) |
| Docker Compose | Chạy API và PostgreSQL cùng một cấu hình | [Compose quickstart](https://docs.docker.com/compose/gettingstarted/) |

Khi bắt đầu làm **database models**, đọc [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) để tạo và chạy migrations. Khi làm **đăng nhập**, đọc [FastAPI security guide](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) cho password hashing và JWT. `httpx` dùng cho dictionary API; `pytest` dùng để kiểm thử. Phiên bản package cụ thể nằm trong `requirements.txt`.

## 2. Cấu trúc project

```text
backend/
  app/
    main.py             # khởi tạo FastAPI
    routers/            # HTTP endpoints
    schemas/            # Pydantic request/response
    services/           # nghiệp vụ
    repositories/       # truy vấn PostgreSQL
    models/             # SQLAlchemy ORM models
    db/                 # kết nối database
    core/               # cấu hình và bảo mật
docs/
requirements.txt
Dockerfile              # image FastAPI
compose.yaml            # service api và PostgreSQL
.env.example
.gitignore
```

Luồng xử lý khi có chức năng: **router → service → repository → database**. Router nhận request và trả response; service xử lý nghiệp vụ; repository chứa truy vấn; model ánh xạ bảng; schema kiểm tra dữ liệu vào/ra. Ví dụ tính năng deck sau này có thể có `routers/decks.py`, `services/decks.py`, `repositories/decks.py`, `models/deck.py` và `schemas/deck.py`. Chỉ tạo các file đó khi bắt đầu làm tính năng.

FastAPI [hướng dẫn tách app bằng `APIRouter`](https://fastapi.tiangolo.com/tutorial/bigger-applications/); service/repository là quy ước kiến trúc của team, không phải cấu trúc bắt buộc của framework. Các thư mục hiện chỉ có `__init__.py`; `backend/app/main.py` chỉ có `app = FastAPI()`, chưa có endpoint hay kết nối database.

## 3. Chạy project

Mở Docker Desktop và chờ Docker Engine chạy, rồi thực hiện trong thư mục gốc repo:

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

Trên Windows PowerShell, thay lệnh copy bằng `Copy-Item .env.example .env`. Lần chạy đầu Docker tải PostgreSQL và cài Python packages nên có thể mất vài phút.

- FastAPI: mở `http://localhost:8000/docs`. Swagger UI hiện trống vì chưa có endpoint.
- PostgreSQL: chạy `docker compose exec db pg_isready -U flashcards -d flashcards`; kết quả mong đợi là `accepting connections`.
- SQL shell: `docker compose exec db psql -U flashcards -d flashcards`.
- Xem log API: `docker compose logs -f api`.
- Dừng: `docker compose down`. Lệnh này giữ lại dữ liệu PostgreSQL trong volume.

Docker Compose chờ database healthy rồi mới chạy API. Trong container, API dùng hostname `db` để kết nối PostgreSQL; `DATABASE_URL` được tạo từ các biến `POSTGRES_*` trong `.env`. App hiện chưa dùng database vì chưa có model hoặc logic kết nối.

`requirements.txt` đã có Alembic để quản lý thay đổi schema sau này. Migration đầu tiên sẽ được tạo khi có database models; hiện chưa có migration nào để chạy.

## 4. Khi phát triển

Sửa file trong `backend/` thì API tự reload. Khi sửa `requirements.txt` hoặc `Dockerfile`, chạy lại `docker compose up --build -d` để cập nhật image. Khi thêm router đầu tiên, import và gọi `app.include_router(...)` trong `backend/app/main.py`.

Không commit `.env`, `.venv` hoặc cache. Nếu cổng `8000` hay `5432` đã được dùng trên máy, đổi phần **bên trái** của mapping cổng tương ứng trong `compose.yaml`. Quy tắc commit nằm ở [commit convention](commit-convention.md).
