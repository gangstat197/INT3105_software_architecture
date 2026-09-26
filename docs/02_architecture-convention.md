# Architecture Convention

Quy ước này mô tả nghiệp vụ, trách nhiệm từng layer, database và API của backend. Lệnh cài đặt/chạy nằm ở [01_installation-setup.md](01_installation-setup.md). Khi triển khai thay đổi contract, cập nhật tài liệu trong cùng PR.

Stack: Python/FastAPI, SQLAlchemy, PostgreSQL 17, Alembic và Docker Compose. Phiên bản package nằm trong `requirements.txt`.

## 1. Requirements và nghiệp vụ

### 1.1. Authentication và quyền sở hữu

- Guest đăng ký bằng `username`, `email`, `password`; username/email unique, password chỉ lưu dạng hash. User đăng nhập bằng username/password và nhận JWT.
- API về deck, card, review, quiz và statistics yêu cầu JWT hợp lệ; thiếu/sai token trả `401 Unauthorized`. Đăng ký, đăng nhập và bắt đầu khôi phục mật khẩu là public.
- User chỉ thao tác với deck của mình. Card đi qua `card.deck_id → deck.user_id`; quiz/attempt đi qua `quiz.deck_id → deck.user_id`. Theo requirement, truy cập resource của user khác trả `403 Forbidden`.
- Quên mật khẩu gửi link chứa reset token qua email. Token có thời hạn, dùng một lần; database chỉ lưu hash của token. Phản hồi yêu cầu reset không tiết lộ email có tồn tại hay không. **Dịch vụ gửi email sẽ chọn khi triển khai auth**, chưa ràng buộc vào provider cụ thể.

### 1.2. Deck, card và dictionary

- User tạo, xem, sửa, xóa deck; xóa deck thì xóa card, quiz, câu hỏi và attempt của **deck đó**. Word và dữ liệu dictionary dùng chung được giữ lại.
- Card có word và notes tùy chọn; chỉ được chuyển sang deck khác của cùng user.
- Khi word chưa có trong database, backend gọi dictionary API. Nếu không tìm thấy, trả `Word Not Found` và không tạo card. Nếu có, lưu meaning, definition, example, IPA, audio, synonym, antonym theo dữ liệu API.
- Một word có thể được dùng bởi nhiều card và vẫn giữ lại khi không còn card. Chuẩn hóa từ và đặt unique trên `(language, normalized_word)` để tránh lưu trùng.
- Một word có nhiều meaning; các definition trong cùng meaning dùng IPA/audio của meaning đó. Synonym và antonym gắn với definition.

### 1.3. Review theo Leitner

**Review** là luồng ôn do hệ thống đề xuất; **quiz** là bài tự kiểm tra. Quiz không làm đổi lịch review. `card.progress_level` chính là [box trong Leitner system](https://subjectguides.york.ac.uk/study-revision/leitner-system?audience=staff); không thêm cột box hoặc `next_review_interval`. Quy ước khởi đầu: 5 box với khoảng chờ tương ứng **1, 3, 7, 14, 30 ngày**, đặt trong cấu hình nghiệp vụ.

1. Card mới ở box 1; `last_reviewed_at` và `next_review_date` là `NULL`.
2. Đề xuất tối đa 20 card đang hoạt động: card quá hạn trước, theo ngày đến hạn cũ nhất; sau đó card chưa từng review. Response kèm `review_version` của mỗi card. Việc đề xuất không đổi tiến độ.
3. User xem đáp án rồi tự đánh dấu đúng/sai. Đúng tăng một box (tối đa box 5); sai về box 1. Cập nhật `last_reviewed_at = now` và `next_review_date = now + interval(box mới)`.
4. Không lưu lịch sử từng lần review. Card giữ `review_total_count`, `review_correct_count` và `review_version` (bắt đầu từ 0). Request gửi `expected_review_version`; backend cập nhật có điều kiện ngay tại database khi version còn khớp **và card còn đến hạn**, rồi tăng version cùng box, ngày review, bộ đếm trong một transaction. Request cũ/gửi lặp không được tính lần hai.

### 1.4. Quiz và statistics

- Một deck có thể tạo nhiều quiz. Mỗi quiz có `quiz_type = multiple_choice` hoặc `fill_blank`; không có bảng exercise.
- Khi tạo quiz, **backend tự chọn** tối đa 20 card hợp lệ từ deck; client không gửi `card_ids`. Nếu không tạo được ít nhất một câu hỏi hợp lệ cho `quiz_type` đã chọn, trả lỗi và không lưu quiz rỗng. Backend lưu bộ câu hỏi cố định. Không sửa bộ card, prompt, options hoặc đáp án sau khi tạo. Mọi attempt làm lại đúng bộ câu hỏi ấy.
- Cả fill và multiple choice chỉ dùng card có example chứa từ đích. Chọn example ngẫu nhiên **một lần khi tạo quiz**, thay từ đích bằng blank. Fill yêu cầu user tự điền từ; so sánh không phân biệt hoa/thường.
- Multiple choice dùng cùng câu có blank, với 4 options: từ đúng và 3 từ ngẫu nhiên khác từ bảng `word` cùng ngôn ngữ. Không dùng chính từ đúng, từ trùng sau chuẩn hóa hoặc bất kỳ synonym nào của từ đúng (gộp synonym từ mọi definition/meaning). Nếu không đủ 3 từ nhiễu, card đó không hợp lệ cho quiz multiple choice. Trộn options một lần khi tạo quiz rồi lưu cùng đáp án chuẩn; không trộn lại theo attempt.
- Khi bắt đầu làm, tạo attempt với `started_at` và `score`/`completed_at` bằng `NULL`. Khi nộp đủ đáp án, ghi kết quả từng card, score bằng **số câu đúng** và `completed_at` trong một transaction. Attempt bỏ dở vẫn có thể mở lại; nếu bắt đầu lần mới thì attempt cũ vẫn chưa hoàn thành. Làm sai hoặc làm lại quiz không ảnh hưởng Leitner.
- Statistics chỉ tính attempt đã hoàn thành (`completed_at IS NOT NULL`). Tiến độ deck = số card đang hoạt động ở box ≥ 2 / tổng card đang hoạt động; deck rỗng trả tiến độ `0`. Review accuracy = tổng lượt review đúng / tổng lượt review; khi chưa có review, accuracy là `null`.

## 2. Project structure

| Vị trí | Trách nhiệm | Lý do tách |
| --- | --- | --- |
| `backend/app/main.py` | Tạo FastAPI app, gắn router | Giữ điểm khởi động ngắn |
| `backend/app/routers/` | HTTP path, nhận request, gọi service, trả response | HTTP không chứa nghiệp vụ/SQL |
| `backend/app/schemas/` | Pydantic schema cho request/response và snapshot | Không lộ ORM model qua API |
| `backend/app/services/` | Ownership, dictionary, Leitner, tạo/chấm quiz và transaction | Một nơi áp dụng quy tắc nghiệp vụ |
| `backend/app/repositories/` | Truy vấn/ghi dữ liệu qua SQLAlchemy | Query không rải trong router/service |
| `backend/app/models/` | ORM model và quan hệ database | Phân biệt schema DB với HTTP |
| `backend/app/db/` | Engine, session, metadata; schema thay đổi qua Alembic | Quản lý kết nối nhất quán |
| `backend/app/core/` | Config, JWT và password hashing | Không lặp mã bảo mật |

Luồng: `router → service → repository → PostgreSQL`. Router không truy vấn SQL; repository không tạo HTTP response. Chỉ tạo file khi triển khai feature tương ứng. Package nằm trong `requirements.txt`.

## 3. Database design

### 3.1. ERD

Sơ đồ dùng [Mermaid ER diagram](https://mermaid.js.org/syntax/entityRelationshipDiagram). `QUIZ_QUESTION.card_id` ghi ID card nguồn lúc tạo quiz; **không phải FK sống tới CARD**. Cách này cho phép quiz cố định dù card được chuyển hoặc xóa riêng (Mục 3.3).

```mermaid
erDiagram
    USER ||--o{ DECK : owns
    USER ||--o{ PASSWORD_RESET_TOKEN : requests
    DECK ||--o{ CARD : contains
    DECK ||--o{ QUIZ : contains
    WORD ||--o{ CARD : used_by
    WORD ||--o{ WORD_MEANING : has
    WORD_MEANING ||--o{ WORD_DEFINITION : has
    WORD_DEFINITION ||--o{ WORD_SYNONYM : has
    WORD_DEFINITION ||--o{ WORD_ANTONYM : has
    QUIZ ||--|{ QUIZ_QUESTION : fixes
    QUIZ ||--o{ ATTEMPT : has
    ATTEMPT ||--o{ QUIZ_CARD : records
    QUIZ_QUESTION ||--o{ QUIZ_CARD : answered_in

    USER {
        int user_id PK
        string username UK
        string email UK
        string password_hash
    }
    PASSWORD_RESET_TOKEN {
        int reset_token_id PK
        int user_id FK
        string token_hash UK
        datetime expires_at
        datetime used_at
    }
    DECK {
        int deck_id PK
        int user_id FK
        string name
        string description
    }
    CARD {
        int card_id PK
        int deck_id FK
        int word_id FK
        string notes
        int progress_level
        datetime last_reviewed_at
        datetime next_review_date
        int review_total_count
        int review_correct_count
        int review_version
    }
    WORD {
        int word_id PK
        string word
        string normalized_word
        string language
    }
    WORD_MEANING {
        int word_meaning_id PK
        int word_id FK
        string part_of_speech
        string IPA
        string audio
    }
    WORD_DEFINITION {
        int word_definition_id PK
        int word_meaning_id FK
        string definition
        string example
    }
    WORD_SYNONYM {
        int synonym_id PK
        int word_definition_id FK
        string word
    }
    WORD_ANTONYM {
        int antonym_id PK
        int word_definition_id FK
        string word
    }
    QUIZ {
        int quiz_id PK
        int deck_id FK
        string quiz_type
    }
    QUIZ_QUESTION {
        int quiz_id PK, FK
        int card_id PK
        string prompt_snapshot
        string answer_snapshot
        jsonb options_snapshot
    }
    ATTEMPT {
        int attempt_id PK
        int quiz_id FK
        int score
        datetime started_at
        datetime completed_at
    }
    QUIZ_CARD {
        int quiz_id PK, FK
        int attempt_id PK, FK
        int card_id PK, FK
        string user_answer
        boolean is_correct
    }
```

### 3.2. Khóa, quan hệ và xóa

- `quiz_question` có khóa chính `(quiz_id, card_id)`. Lúc tạo quiz, service chỉ chọn card đang thuộc deck của quiz; tạo quiz và toàn bộ câu hỏi trong một transaction.
- `attempt` thuộc một quiz, có khóa `attempt_id` và `UNIQUE(attempt_id, quiz_id)` làm đích cho FK ghép.
- `attempt.completed_at IS NULL` nghĩa là chưa nộp; lúc này `score IS NULL` và chưa có `quiz_card`. Khi đã hoàn thành, `score` có giá trị (kể cả `0`). Một attempt bỏ dở không bị tính vào statistics và có thể đọc lại câu hỏi để tiếp tục. Backend không lưu đáp án từng phần trước khi submit; nếu cần giữ phần đã nhập, frontend lưu cục bộ.
- `quiz_card` có khóa chính **ba cột** `(quiz_id, attempt_id, card_id)`. FK ghép `(attempt_id, quiz_id) → attempt(attempt_id, quiz_id)` bảo đảm attempt thuộc quiz; FK ghép `(quiz_id, card_id) → quiz_question(quiz_id, card_id)` bảo đảm card nằm trong bộ câu hỏi. Ba FK riêng hoặc chỉ khóa chính ba cột đều không đủ. [PostgreSQL hỗ trợ khóa và FK ghép](https://www.postgresql.org/docs/17/ddl-constraints.html).
- Xóa quiz xóa câu hỏi, attempt và kết quả; xóa deck xóa quiz và card của deck. Xóa/chuyển riêng card không làm đổi quiz cũ; word được giữ để tái sử dụng.

### 3.3. Snapshot

Snapshot được tạo **một lần cùng quiz**, không tạo lại theo attempt. `quiz_question` lưu câu example đã thay từ đích bằng blank, đáp án chuẩn và options theo thứ tự cố định. Với multiple choice, `options_snapshot` là JSONB array gồm 4 option ID/text đã trộn, ví dụ `[{"id":"A","text":"apple"},{"id":"B","text":"orange"},...]`; `answer_snapshot` là ID option đúng. Với fill, `options_snapshot = NULL` và `answer_snapshot` là từ cần điền. Schema Pydantic chung kiểm tra cấu trúc khi tạo/đọc; không dùng chuỗi tự phân cách. Không gửi đáp án chuẩn trước khi nộp bài.

Mỗi attempt đọc **snapshot** để hiển thị/chấm; `quiz_card` chỉ lưu đáp án user và đúng/sai. `quiz_question.card_id` là ID nguồn lịch sử, **không có FK trực tiếp tới `card`**: khi card còn tồn tại vẫn tra được, khi card bị xóa quiz vẫn hoạt động nhờ snapshot. Nếu muốn thay bộ câu hỏi, tạo quiz mới.

## 4. API list

Các path dưới đây là contract dự kiến. Multiple choice và fill dùng cùng nhóm `/api/quizzes`. Mọi path ngoài auth public đều kiểm tra owner như Mục 1.1.

| Nhóm | Method | Path | Mục đích |
| --- | --- | --- | --- |
| Auth | POST | `/api/auth/register` | Đăng ký |
| Auth | POST | `/api/auth/login` | Nhận JWT |
| Auth | POST | `/api/auth/forgot-password` | Yêu cầu gửi reset link qua email |
| Auth | POST | `/api/auth/reset-password` | Đặt mật khẩu mới bằng reset token |
| Deck | POST | `/api/decks` | Tạo deck |
| Deck | GET | `/api/decks` | Danh sách deck |
| Deck | GET | `/api/decks/{deck_id}` | Chi tiết deck |
| Deck | PATCH | `/api/decks/{deck_id}` | Sửa deck |
| Deck | DELETE | `/api/decks/{deck_id}` | Xóa deck, card, quiz và attempt của deck |
| Deck | GET | `/api/decks/{deck_id}/cards` | Card trong deck |
| Card | POST | `/api/decks/{deck_id}/cards` | Tạo card |
| Card | PATCH | `/api/cards/{card_id}` | Sửa notes hoặc chuyển deck |
| Card | DELETE | `/api/cards/{card_id}` | Xóa card; quiz cũ giữ snapshot |
| Review | GET | `/api/reviews/due` | Tối đa 20 card đến hạn/chưa review, kèm `review_version` |
| Review | POST | `/api/reviews/{card_id}` | Body: `is_correct`, `expected_review_version`; cập nhật Leitner một lần |
| Quiz | POST | `/api/decks/{deck_id}/quizzes` | Backend tự chọn card và tạo bộ câu hỏi cố định; body có `quiz_type`, không có `card_ids` |
| Quiz | GET | `/api/quizzes` | Danh sách quiz của user; lọc theo `quiz_type` |
| Quiz | GET | `/api/quizzes/{quiz_id}` | Chi tiết quiz/câu hỏi, chưa lộ đáp án |
| Quiz | GET | `/api/quizzes/{quiz_id}/attempts` | Danh sách attempt của quiz và trạng thái hoàn thành |
| Quiz | POST | `/api/quizzes/{quiz_id}/attempts` | Tạo attempt chưa hoàn thành, trả `attempt_id` và câu hỏi |
| Quiz | POST | `/api/quizzes/{quiz_id}/attempts/{attempt_id}/submit` | Nộp toàn bộ đáp án; ghi kết quả, score và `completed_at` cùng transaction |
| Quiz | GET | `/api/quizzes/{quiz_id}/attempts/{attempt_id}` | Chưa nộp: câu hỏi để tiếp tục, không lộ đáp án; đã nộp: score, câu sai và đáp án |
| Statistics | GET | `/api/decks/{deck_id}/statistics` | Tiến độ và review accuracy của deck |
| Statistics | GET | `/api/quizzes/{quiz_id}/statistics` | Kết quả các attempt của quiz |
| Statistics | GET | `/api/statistics` | Tổng quan của user |

Frontend kiểm tra số câu và lựa chọn trước khi gửi để hỗ trợ user; backend vẫn kiểm tra attempt thuộc quiz, bộ `card_id` gửi lên khớp đúng bộ câu hỏi (không thiếu, thừa hoặc trùng), và đáp án multiple choice thuộc options của câu đó. Request sai không được ghi kết quả một phần. Submit khóa/kiểm tra attempt trong transaction và chỉ chấp nhận khi `completed_at IS NULL`; request sau khi hoàn thành trả `409 Conflict` và không ghi lại score. Review với version cũ hoặc card chưa đến hạn cũng trả `409 Conflict`, không tăng box hay bộ đếm. Các path xem card sai và `/complete` trong đề xuất ban đầu được gộp vào GET attempt vì câu sai phụ thuộc vào **attempt**, không chỉ quiz.
