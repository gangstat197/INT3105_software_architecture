# Kiểm thử tải trên Kaggle CPU

Upload [notebook](../notebooks/kaggle_cpu_load_test.ipynb) lên Kaggle, chọn **Accelerator: None**, bật **Internet**, rồi **Run All**. PostgreSQL, FastAPI (1 worker) và Locust chạy cùng phiên Kaggle.

Kịch bản: đọc deck, card và thẻ đến hạn; mỗi user nghỉ 1–3 giây giữa các request, dùng luân phiên 100 tài khoản mẫu.

| Report | Request | Lỗi | RPS tổng | p95 |
| --- | ---: | ---: | ---: | ---: |
| [100 users](../notebooks/load_report_100.html) | 3.146 | 0% | 45,14 | 340 ms |
| [Mục tiêu 1.000 users](../notebooks/load_report_1000.html) | 2.372 | 71,16% | 33,99 | 10.000 ms |

Cả hai lượt chạy 70 giây. Lượt thứ hai chỉ ghi nhận tối đa 650 users trong biểu đồ; toàn bộ lỗi là timeout 10 giây. RPS tổng bao gồm request lỗi.

100 users hoạt động ổn trong lượt đo; tăng tải gây nhiều timeout.
