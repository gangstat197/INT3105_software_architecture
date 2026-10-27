# Kiểm thử tải trên Kaggle CPU

FastAPI 1 worker, PostgreSQL và Locust chạy cùng máy. Đọc deck, card và thẻ đến hạn; dùng chung 100 tài khoản, nghỉ 1–3 giây/request, timeout 10 giây. Nhóm kiểm thử với 2 settings: tăng 50 users/giây và 100 users/giây. 

| Lượt chạy | Request | Tỷ lệ lỗi | RPS tổng | p95 |
| --- | ---: | ---: | ---: | ---: |
| [100 users, tăng 50 users/giây](../notebooks/load_report_100.html) | 3.146 | **0%** | 45,14 | 340 ms |
| [650 users, tăng 50 users/giây](../notebooks/load_report_1000.html) | 2.372 | **71,16%** | 33,99 | 10.000 ms |
|100–900 users, tăng 100 users/giây | 22.710 | **100% cho toàn bộ** | — | 10.000 ms |

**Kết quả:** lượt cũ 100 users tăng 50 users/giây chạy tốt. Lượt mới tăng 100 users/giây nghẽn từ 100 users. Hai lượt khác thiết lập, chưa xác nhận tốc độ tăng tải là nguyên nhân duy nhất.

**Lỗi:** hết 15 connection trong pool; worker chờ connection, request giữ connection chờ worker để chạy tiếp. Server báo `QueuePool connection timed out`, client timeout sau 10 giây.

[Notebook](../notebooks/kaggle_cpu_load_test.ipynb): upload lên Kaggle, chọn CPU, bật Internet rồi Run All.
