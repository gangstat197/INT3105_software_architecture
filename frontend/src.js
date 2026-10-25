import './style.css';

const $ = (selector) => document.querySelector(selector);
let token = sessionStorage.getItem('token');
let username = sessionStorage.getItem('username') || '';
let decks = [];
let selectedId = null;
let reviewsLoaded = false;
let quizzes = [];
let selectedQuiz = null;
let currentAttempt = null;
const drafts = new Map();
let currentView = 'overview';
let statusTimer;

const views = {
  overview: ['YOUR LEARNING JOURNEY', 'Một chút tiến bộ mỗi ngày.'],
  library: ['COLLECT WORDS, KEEP IDEAS', 'Bộ từ của bạn.'],
  reviews: ['MAKE IT STICK', 'Đến lúc nhớ lại rồi.'],
  quizzes: ['CHALLENGE YOURSELF', 'Một thử thách nho nhỏ.'],
};

function showView(view) {
  if (!views[view]) view = 'overview';
  currentView = view;
  document.querySelectorAll('[data-screen]').forEach((screen) => {
    screen.hidden = screen.dataset.screen !== view;
  });
  document.querySelectorAll('[data-view]').forEach((node) => {
    if (node.dataset.view === view) node.setAttribute('aria-current', 'page');
    else node.removeAttribute('aria-current');
  });
  $('.sidebar-decks').classList.toggle('show-decks', view === 'library');
  $('#view-kicker').textContent = views[view][0];
  $('#view-title').textContent = views[view][1];
}

async function navigate(view) {
  showView(view);
  if (view === 'reviews' && !reviewsLoaded) await loadReviews();
}

function emptyState(title, message, symbol = '✳') {
  const node = element('div', undefined, 'empty-state');
  node.append(element('span', symbol), element('h3', title), element('p', message));
  return node;
}

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function status(message, error = false, busy = false) {
  clearTimeout(statusTimer);
  $('#status-message').textContent = message;
  $('#status').dataset.error = String(error);
  $('#status').dataset.busy = String(busy);
  $('#status').hidden = false;
  if (!error && !busy) statusTimer = setTimeout(() => { $('#status').hidden = true; }, 4500);
}

function session() {
  $('#auth').hidden = Boolean(token);
  $('#app').hidden = !token;
  $('#session').hidden = !token;
  $('#username').textContent = username;
}

function logout() {
  token = null;
  username = '';
  decks = [];
  selectedId = null;
  reviewsLoaded = false;
  showView('overview');
  sessionStorage.removeItem('token');
  sessionStorage.removeItem('username');
  $('#cards').replaceChildren();
  $('#reviews').replaceChildren();
  quizzes = [];
  selectedQuiz = null;
  currentAttempt = null;
  drafts.clear();
  for (const id of ['decks', 'quizzes', 'quiz-detail', 'attempt', 'user-statistics', 'deck-statistics']) {
    $(`#${id}`).replaceChildren();
  }
  $('#deck-content').hidden = true;
  $('#quiz-detail').hidden = true;
  $('#response').textContent = 'Chưa có request.';
  session();
}

async function api(method, path, body) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const response = await fetch(`/api${path}`, {
    method, headers, body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = response.status === 204 ? null
    : response.headers.get('content-type')?.includes('application/json')
      ? await response.json() : await response.text();
  if (response.status === 401) logout();
  const display = data?.access_token ? { ...data, access_token: '(ẩn)' } : data;
  $('#response').textContent = `${method} /api${path} → ${response.status}\n${JSON.stringify(display, null, 2)}`;
  if (!response.ok) {
    const detail = data?.detail ?? data;
    throw new Error(`${response.status}: ${typeof detail === 'string' ? detail : JSON.stringify(detail)}`);
  }
  return data;
}

async function run(action) {
  $('#controls').disabled = true;
  $('#app').setAttribute('aria-busy', 'true');
  status('Đang xử lý…', false, true);
  try {
    const message = await action();
    if (message) status(message);
    else { clearTimeout(statusTimer); $('#status').hidden = true; }
  } catch (error) {
    status(error.message, true);
  } finally {
    $('#controls').disabled = false;
    $('#app').setAttribute('aria-busy', 'false');
  }
}

function button(text, action, className = 'secondary') {
  const node = element('button', text, className);
  node.type = 'button';
  node.addEventListener('click', () => run(action));
  return node;
}

function renderDecks() {
  $('#deck-count').textContent = decks.length;
  $('#decks').replaceChildren(...decks.map((deck) => {
    const node = button(deck.name, async () => { showView('library'); await selectDeck(deck.deck_id); });
    node.setAttribute('aria-current', String(deck.deck_id === selectedId));
    return node;
  }));
  if (!decks.length) $('#decks').append(element('p', 'Bộ từ đầu tiên đang chờ bạn.', 'muted'));
}

async function loadDecks(preferredId = selectedId) {
  decks = await api('GET', '/decks');
  selectedId = decks.some((deck) => deck.deck_id === preferredId) ? preferredId : (decks[0]?.deck_id ?? null);
  await selectDeck(selectedId);
}

async function selectDeck(id) {
  selectedId = id;
  renderDecks();
  const deck = decks.find((item) => item.deck_id === id);
  $('#deck-content').hidden = !deck;
  $('#deck-title').textContent = deck ? deck.name : 'Bắt đầu với một bộ từ mới.';
  $('#deck-description').textContent = deck?.description || 'Gom những từ bạn muốn mang theo.';
  renderQuizDecks();
  if (!deck) { $('#cards').replaceChildren(); $('#deck-statistics').replaceChildren(); $('#card-count').textContent = '0 từ'; return; }
  $('#edit-deck').elements.name.value = deck.name;
  $('#edit-deck').elements.description.value = deck.description || '';
  await loadCards();
  await loadDeckStatistics();
}

function wordDetails(card) {
  const box = element('div');
  for (const meaning of card.word.meanings) {
    box.append(element('p', [meaning.part_of_speech, meaning.ipa].filter(Boolean).join(' · '), 'muted'));
    if (meaning.audio) {
      const audio = element('audio');
      audio.controls = true;
      audio.preload = 'none';
      audio.src = meaning.audio;
      box.append(audio);
    }
    for (const definition of meaning.definitions) {
      box.append(element('p', definition.definition));
      if (definition.example) box.append(element('p', definition.example, 'muted'));
      if (definition.synonyms.length) box.append(element('p', `Synonyms: ${definition.synonyms.map((item) => item.word).join(', ')}`, 'muted'));
      if (definition.antonyms.length) box.append(element('p', `Antonyms: ${definition.antonyms.map((item) => item.word).join(', ')}`, 'muted'));
    }
  }
  return box;
}

function cardHeader(card) {
  const box = element('article', undefined, 'card');
  const meta = element('div', undefined, 'word-meta');
  meta.append(element('span', `Box ${card.progress_level} / 5`, 'pill'),
    element('span', `${card.review_correct_count}/${card.review_total_count} lần nhớ đúng`, 'muted'));
  box.append(meta, element('h3', card.word.word));
  box.append(element('p', card.next_reviewed_date
    ? `Ôn tiếp: ${date(card.next_reviewed_date)}` : 'Một từ mới trên hành trình của bạn.', 'muted'));
  return box;
}

async function loadCards() {
  if (selectedId === null) return;
  const cards = await api('GET', `/decks/${selectedId}/cards`);
  $('#cards').replaceChildren();
  $('#card-count').textContent = `${cards.length} từ`;
  if (!cards.length) $('#cards').append(emptyState('Bộ từ mới, nhiều điều đang chờ.', 'Thêm từ đầu tiên ở phía trên. Nghĩa và phát âm sẽ được tìm giúp bạn.', '＋'));
  for (const card of cards) {
    const box = cardHeader(card);
    box.append(element('p', card.word.meanings?.[0]?.definitions?.[0]?.definition || 'Mở chi tiết để khám phá từ này.', 'word-preview'));
    const details = element('details');
    details.append(element('summary', 'Nghĩa & phát âm'), wordDetails(card));
    box.append(details);
    const form = element('form', undefined, 'stack');
    const label = element('label', 'Ghi chú');
    const notes = element('textarea');
    notes.value = card.notes || '';
    notes.rows = 2;
    label.append(notes);
    const moveLabel = element('label', 'Deck');
    const target = element('select');
    for (const deck of decks) {
      const option = element('option', deck.name);
      option.value = deck.deck_id;
      option.selected = deck.deck_id === card.deck_id;
      target.append(option);
    }
    moveLabel.append(target);
    const actions = element('div', undefined, 'row');
    const save = element('button', 'Lưu card', 'secondary');
    save.type = 'submit';
    actions.append(save, button('Xóa card', async () => {
      if (!confirm(`Xóa card "${card.word.word}"?`)) return 'Đã hủy';
      await api('DELETE', `/cards/${card.card_id}`);
      await refreshCardsAndReviews();
      return 'Đã xóa card';
    }, 'danger'));
    form.append(label, moveLabel, actions);
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      run(async () => {
        await api('PATCH', `/cards/${card.card_id}`, { notes: notes.value || null, deck_id: Number(target.value) });
        await refreshCardsAndReviews();
        return 'Đã lưu card';
      });
    });
    const edit = element('details');
    edit.append(element('summary', 'Chỉnh sửa ghi chú · Chuyển bộ từ'), form);
    box.append(edit);
    $('#cards').append(box);
  }
}

async function loadReviews() {
  const cards = await api('GET', '/reviews/due');
  reviewsLoaded = true;
  $('#reviews').replaceChildren();
  if (!cards.length) $('#reviews').append(emptyState('Bạn đã ôn xong rồi! ✦', 'Chưa có thẻ nào đến hạn. Thêm từ mới hoặc quay lại sau nhé.', '✓'));
  for (const card of cards) {
    const box = cardHeader(card);
    const answer = wordDetails(card);
    if (card.notes) answer.append(element('p', `Ghi chú: ${card.notes}`));
    answer.hidden = true;
    const actions = element('div', undefined, 'row review-actions');
    actions.hidden = true;
    for (const [text, isCorrect] of [['Nhớ rồi ✓', true], ['Chưa nhớ ↺', false]]) {
      actions.append(button(text, async () => {
        await api('POST', `/reviews/${card.card_id}`, { is_correct: isCorrect, expected_review_version: card.review_version });
        await refreshCardsAndReviews();
        return `Đã ghi nhận: ${text.toLowerCase()}`;
      }));
    }
    const reveal = element('button', 'Lật thẻ · Xem nghĩa ↻', 'secondary review-reveal');
    reveal.type = 'button';
    reveal.addEventListener('click', () => { answer.hidden = false; actions.hidden = false; reveal.hidden = true; });
    box.append(reveal, answer, actions);
    $('#reviews').append(box);
  }
}

async function refreshCardsAndReviews() {
  await loadCards();
  if (reviewsLoaded) await loadReviews();
  await loadStatistics();
}

const quizTypes = { multiple_choice: 'Trắc nghiệm', fill_blank: 'Điền từ' };
const percent = (value) => value == null ? 'Chưa có dữ liệu' : `${(value * 100).toFixed(1)}%`;
const date = (value) => value ? new Date(value).toLocaleString('vi-VN') : 'Chưa hoàn thành';

function metrics(target, entries) {
  target.replaceChildren(...entries.map(([label, value]) => {
    const item = element('div', undefined, 'metric');
    const number = element('strong', String(value));
    if (String(value).length > 10) number.className = 'no-data';
    item.append(number, element('span', label));
    return item;
  }));
}

async function loadUserStatistics() {
  const data = await api('GET', '/statistics');
  metrics($('#user-statistics'), [
    ['Deck', data.total_decks], ['Card', data.total_cards],
    ['Tiến độ ôn tập', percent(data.overall_progress)],
    ['Độ chính xác ôn tập', percent(data.overall_review_accuracy)],
    ['Lượt quiz đã hoàn thành', data.total_quizzes_completed],
  ]);
}

async function loadDeckStatistics() {
  if (selectedId === null) return;
  const data = await api('GET', `/decks/${selectedId}/statistics`);
  metrics($('#deck-statistics'), [
    ['Card trong deck', data.total_cards], ['Tiến độ ôn tập', percent(data.progress)],
    ['Độ chính xác ôn tập', percent(data.review_accuracy)],
  ]);
}

async function loadStatistics() {
  await loadUserStatistics();
  await loadDeckStatistics();
}

async function loadWorkspace() {
  await loadDecks();
  await loadUserStatistics();
  await loadQuizzes();
}

function renderQuizDecks() {
  const select = $('#quiz-deck');
  select.replaceChildren(...decks.map((deck) => {
    const option = element('option', deck.name);
    option.value = deck.deck_id;
    option.selected = deck.deck_id === selectedId;
    return option;
  }));
  $('#create-quiz-button').disabled = decks.length === 0;
  if (!decks.length) {
    const option = element('option', 'Tạo deck và thêm card trước');
    option.value = '';
    select.append(option);
  }
}

function quizLabel(quiz) {
  const deck = decks.find((item) => item.deck_id === quiz.deck_id);
  return `Quiz #${quiz.quiz_id} · ${quizTypes[quiz.quiz_type]} · ${deck?.name || `Deck #${quiz.deck_id}`}`;
}

function renderQuizzes() {
  $('#quizzes').replaceChildren(...quizzes.map((quiz) => {
    const node = button(quizLabel(quiz), () => selectQuiz(quiz.quiz_id));
    node.setAttribute('aria-current', String(quiz.quiz_id === selectedQuiz?.quiz_id));
    return node;
  }));
  if (!quizzes.length) $('#quizzes').append(emptyState('Một thử thách mới?', 'Tạo quiz từ bộ từ của bạn để bắt đầu.', '✳'));
}

async function loadQuizzes(preferredId = selectedQuiz?.quiz_id) {
  const type = $('#quiz-filter').value;
  quizzes = await api('GET', `/quizzes${type ? `?quiz_type=${encodeURIComponent(type)}` : ''}`);
  if (preferredId && quizzes.some((quiz) => quiz.quiz_id === preferredId)) {
    // Refresh metadata/history without discarding an open answer form.
    await loadQuizDetail(preferredId);
  } else {
    selectedQuiz = null;
    currentAttempt = null;
    $('#quiz-detail').hidden = true;
    $('#quiz-detail').replaceChildren();
    $('#attempt').replaceChildren();
  }
  renderQuizzes();
}

async function selectQuiz(id) {
  if (selectedQuiz?.quiz_id !== id) {
    currentAttempt = null;
    $('#attempt').replaceChildren();
  }
  await loadQuizDetail(id);
  renderQuizzes();
}

function questionContent(question) {
  const content = element('div');
  content.append(element('p', question.prompt_snapshot));
  if (question.options_snapshot) {
    const list = element('ul');
    for (const option of question.options_snapshot) list.append(element('li', `${option.id}. ${option.text}`));
    content.append(list);
  }
  return content;
}

async function loadQuizDetail(id) {
  const quiz = await api('GET', `/quizzes/${id}`);
  const attempts = await api('GET', `/quizzes/${id}/attempts`);
  const stats = await api('GET', `/quizzes/${id}/statistics`);
  selectedQuiz = quiz;
  const box = $('#quiz-detail');
  box.hidden = false;
  box.replaceChildren(element('h3', quizLabel(quiz)),
    element('p', `${quiz.quiz_questions.length} câu hỏi. Điểm là số câu trả lời đúng.`, 'muted'));
  const overview = element('div', undefined, 'metrics');
  metrics(overview, [
    ['Lượt đã hoàn thành', stats.total_attempts],
    ['Điểm trung bình', stats.average_score == null ? 'Chưa có' : stats.average_score.toFixed(1)],
    ['Điểm cao nhất', stats.best_score ?? 'Chưa có'],
  ]);
  box.append(overview);
  const preview = element('details');
  preview.append(element('summary', 'Xem đề bài'));
  for (const [index, question] of quiz.quiz_questions.entries()) {
    const item = element('div', undefined, 'card');
    item.append(element('strong', `Câu ${index + 1}`), questionContent(question));
    preview.append(item);
  }
  box.append(preview, button('Bắt đầu lượt làm mới', async () => {
    if (currentAttempt && !currentAttempt.completed_at) {
      if (!confirm('Bắt đầu lượt mới? Bạn có thể tiếp tục lượt cũ trong lịch sử.')) return 'Đã hủy';
    }
    const attempt = await api('POST', `/quizzes/${id}/attempts`);
    renderAttempt(attempt);
    await loadQuizDetail(id);
    return 'Đã bắt đầu lượt làm bài';
  }, ''));
  box.append(element('h3', 'Lịch sử làm bài'));
  if (!attempts.length) box.append(element('p', 'Chưa có lượt làm bài.', 'muted'));
  for (const attempt of attempts) {
    const row = element('div', undefined, 'history-row');
    const completed = Boolean(attempt.completed_at);
    row.append(element('span', `Lượt #${attempt.attempt_id} · ${date(attempt.started_at)} · ${completed ? `${attempt.score}/${quiz.quiz_questions.length} câu đúng` : 'Đang làm'}`),
      button(completed ? 'Xem kết quả' : 'Tiếp tục', async () => {
        const data = await api('GET', `/quizzes/${id}/attempts/${attempt.attempt_id}`);
        renderAttempt(data);
      }));
    box.append(row);
  }
}

function answerText(question, answer) {
  if (answer == null || answer === '') return '(Bỏ trống)';
  const option = question.options_snapshot?.find((item) => item.id === answer);
  return option ? `${option.id}. ${option.text}` : answer;
}

function renderAttempt(attempt) {
  currentAttempt = attempt;
  const box = $('#attempt');
  box.replaceChildren(element('span', attempt.completed_at ? 'NICE WORK · KẾT QUẢ CỦA BẠN' : 'TAKE YOUR TIME · TỪNG CÂU MỘT', 'eyebrow'),
    element('h3', `Lượt làm #${attempt.attempt_id}`));
  if (attempt.completed_at) {
    box.append(element('p', `Kết quả: ${attempt.score}/${attempt.total_questions} câu đúng`, 'score'),
      element('p', `Nộp lúc ${date(attempt.completed_at)}`, 'muted'));
    const wrong = attempt.wrong_questions || [];
    box.append(element('h3', wrong.length ? `Câu sai (${wrong.length})` : 'Bạn đã trả lời đúng tất cả câu hỏi!'));
    for (const question of wrong) {
      const item = element('article', undefined, 'card wrong-answer');
      item.append(questionContent(question),
        element('p', `Bạn trả lời: ${answerText(question, question.user_answer)}`),
        element('p', `Đáp án đúng: ${answerText(question, question.correct_answer)}`, 'correct-answer'));
      box.append(item);
    }
    box.scrollIntoView?.({ block: 'start' });
    return;
  }
  const key = `${attempt.quiz_id}:${attempt.attempt_id}`;
  if (!drafts.has(key)) drafts.set(key, {});
  const draft = drafts.get(key);
  const form = element('form', undefined, 'stack');
  const progressBox = element('div', undefined, 'quiz-progress');
  const progress = element('progress');
  progress.max = attempt.total_questions;
  const progressLabel = element('span');
  progressBox.append(progress, progressLabel);
  const updateProgress = () => {
    const data = new FormData(form);
    const answered = (attempt.questions || []).filter((question) => String(data.get(`answer_${question.card_id}`) || '').trim()).length;
    progress.value = answered;
    progressLabel.textContent = `${answered} / ${attempt.total_questions} câu`;
    progress.setAttribute('aria-label', `Đã trả lời ${answered} trên ${attempt.total_questions} câu`);
  };
  form.append(progressBox);
  for (const [index, question] of (attempt.questions || []).entries()) {
    const field = element('fieldset', undefined, 'card quiz-question');
    field.append(element('legend', `Câu ${index + 1}`), element('p', question.prompt_snapshot));
    const name = `answer_${question.card_id}`;
    if (question.options_snapshot) {
      for (const option of question.options_snapshot) {
        const label = element('label', undefined, 'quiz-option');
        const input = element('input');
        input.type = 'radio';
        input.name = name;
        input.value = option.id;
        input.required = true;
        input.checked = draft[name] === option.id;
        label.append(input, element('span', `${option.id}. ${option.text}`));
        field.append(label);
      }
    } else {
      const label = element('label', 'Từ cần điền');
      const input = element('input');
      input.name = name;
      input.required = true;
      input.autocomplete = 'off';
      input.value = draft[name] || '';
      label.append(input);
      field.append(label);
    }
    form.append(field);
  }
  form.addEventListener('input', () => {
    Object.assign(draft, Object.fromEntries(new FormData(form)));
    updateProgress();
  });
  updateProgress();
  const submit = element('button', 'Nộp bài');
  submit.type = 'submit';
  form.append(element('p', 'Trả lời tất cả câu trước khi nộp. Đáp án chưa nộp chỉ được giữ trong phiên trang hiện tại.', 'muted'), submit);
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const answers = attempt.questions.map((question) => ({
      card_id: question.card_id, user_answer: String(data.get(`answer_${question.card_id}`) || '').trim(),
    }));
    run(async () => {
      const path = `/quizzes/${attempt.quiz_id}/attempts/${attempt.attempt_id}`;
      let result;
      try {
        result = await api('POST', `${path}/submit`, { answers });
      } catch (error) {
        // Another tab may already have submitted this attempt.
        if (!error.message.startsWith('409:')) throw error;
        result = await api('GET', path);
      }
      drafts.delete(key);
      renderAttempt(result);
      await loadQuizDetail(attempt.quiz_id);
      await loadUserStatistics();
      return 'Đã chấm bài';
    });
  });
  box.append(form);
  box.scrollIntoView?.({ block: 'start' });
}

$('#create-quiz').addEventListener('submit', (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.currentTarget));
  run(async () => {
    const feedback = $('#quiz-feedback');
    feedback.hidden = true;
    let quiz;
    try {
      quiz = await api('POST', `/decks/${Number(data.deck_id)}/quizzes`, { quiz_type: data.quiz_type });
    } catch (error) {
      const message = error.message.includes('No cards in this deck are usable')
        ? data.quiz_type === 'multiple_choice'
          ? 'Chưa đủ dữ liệu tạo trắc nghiệm. Cần thẻ có câu ví dụ và đủ 3 từ gây nhiễu. Thử kiểu điền từ hoặc bổ sung từ mới nhé.'
          : 'Bộ từ này chưa có thẻ với câu ví dụ chứa từ đang học. Thử bộ từ khác hoặc thêm từ có câu ví dụ nhé.'
        : error.message;
      feedback.textContent = message;
      feedback.dataset.error = 'true';
      feedback.hidden = false;
      throw new Error(message);
    }
    $('#quiz-filter').value = '';
    currentAttempt = null;
    $('#attempt').replaceChildren();
    await loadQuizzes(quiz.quiz_id);
    feedback.textContent = `Quiz đã sẵn sàng! ${quiz.quiz_questions.length} câu đang chờ bạn ở phía dưới.`;
    feedback.dataset.error = 'false';
    feedback.hidden = false;
    return 'Quiz đã sẵn sàng. Bắt đầu một lượt làm mới nhé!';
  });
});
$('#create-quiz').addEventListener('change', () => { $('#quiz-feedback').hidden = true; });
$('#quiz-filter').addEventListener('change', () => run(() => loadQuizzes()));
$('#refresh-quizzes').addEventListener('click', () => run(() => loadQuizzes()));
$('#refresh-statistics').addEventListener('click', () => run(() => loadStatistics()));

for (const [id, path] of [['forgot-password', '/auth/forgot-password'], ['reset-password', '/auth/reset-password']]) {
  $(`#${id}`).addEventListener('submit', (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form));
    run(async () => {
      const response = await api('POST', path, data);
      form.reset();
      return id === 'reset-password' ? 'Đã đặt lại mật khẩu. Đăng nhập bằng mật khẩu mới.' : response.message;
    });
  });
}

$('#auth-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const action = event.submitter?.value || $('#auth-submit').value;
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form));
  run(async () => {
    if (action === 'register') {
      if (!data.email) throw new Error('Cần nhập email khi đăng ký.');
      await api('POST', '/auth/register', data);
    }
    const result = await api('POST', '/auth/login', { username: data.username, password: data.password });
    token = result.access_token;
    username = data.username;
    sessionStorage.setItem('token', token);
    sessionStorage.setItem('username', username);
    form.elements.password.value = '';
    session();
    await loadWorkspace();
    return 'Đã đăng nhập';
  });
});

$('#create-deck').addEventListener('submit', (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const name = form.elements.name.value;
  run(async () => {
    const deck = await api('POST', '/decks', { name });
    form.reset();
    showView('library');
    await loadDecks(deck.deck_id);
    await loadUserStatistics();
    return 'Đã tạo deck';
  });
});

$('#edit-deck').addEventListener('submit', (event) => {
  event.preventDefault();
  const fields = event.currentTarget.elements;
  const data = { name: fields.name.value, description: fields.description.value || null };
  run(async () => {
    await api('PATCH', `/decks/${selectedId}`, data);
    await loadDecks();
    return 'Đã lưu deck';
  });
});

$('#add-card').addEventListener('submit', (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form));
  data.notes = data.notes || null;
  run(async () => {
    await api('POST', `/decks/${selectedId}/cards`, data);
    form.reset();
    await refreshCardsAndReviews();
    return 'Đã thêm card';
  });
});

$('#delete-deck').addEventListener('click', () => run(async () => {
  if (!confirm('Xóa deck cùng toàn bộ card và quiz trong deck?')) return 'Đã hủy';
  await api('DELETE', `/decks/${selectedId}`);
  await loadDecks();
  if (reviewsLoaded) await loadReviews();
  await loadUserStatistics();
  await loadQuizzes();
  return 'Đã xóa deck';
}));
$('#refresh-decks').addEventListener('click', () => run(() => loadDecks()));
$('#refresh-cards').addEventListener('click', () => run(() => loadCards()));
$('#load-reviews').addEventListener('click', () => run(() => loadReviews()));
$('#logout').addEventListener('click', () => { logout(); status('Đã đăng xuất'); });

for (const node of document.querySelectorAll('[data-view], [data-go]')) {
  node.addEventListener('click', () => run(() => navigate(node.dataset.view || node.dataset.go)));
}
$('#start-studying').addEventListener('click', () => run(() => navigate('reviews')));
$('.brand').addEventListener('click', (event) => {
  event.preventDefault();
  if (token) showView('overview');
});
$('#dismiss-status').addEventListener('click', () => { clearTimeout(statusTimer); $('#status').hidden = true; });
for (const node of document.querySelectorAll('[data-auth-mode]')) {
  node.addEventListener('click', () => {
    const register = node.dataset.authMode === 'register';
    document.querySelectorAll('[data-auth-mode]').forEach((tab) => tab.setAttribute('aria-pressed', String(tab === node)));
    $('#register-email').hidden = !register;
    $('#auth-form').elements.email.required = register;
    $('#auth-form').elements.email.disabled = !register;
    $('#auth-heading').textContent = register ? 'Một khởi đầu mới.' : 'Chào bạn trở lại.';
    $('#auth-caption').textContent = register ? 'Tạo tài khoản và bắt đầu bộ từ đầu tiên của bạn.' : 'Bộ từ của bạn đang chờ một lần ôn nữa.';
    $('#auth-submit').value = register ? 'register' : 'login';
    $('#auth-submit').textContent = register ? 'Tạo góc học tập →' : 'Vào góc học tập →';
    $('#auth-form').elements.password.autocomplete = register ? 'new-password' : 'current-password';
  });
}
$('#today-label').textContent = new Date().toLocaleDateString('vi-VN', { weekday: 'long', day: 'numeric', month: 'long' });
showView('overview');

session();
if (token) run(() => loadWorkspace());
