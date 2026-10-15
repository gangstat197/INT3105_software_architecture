import './style.css';

const $ = (selector) => document.querySelector(selector);
let token = sessionStorage.getItem('token');
let username = sessionStorage.getItem('username') || '';
let decks = [];
let selectedId = null;
let reviewsLoaded = false;

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function status(message, error = false) {
  $('#status').textContent = message;
  $('#status').dataset.error = String(error);
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
  sessionStorage.removeItem('token');
  sessionStorage.removeItem('username');
  $('#cards').replaceChildren();
  $('#reviews').replaceChildren();
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
  status('Đang gửi request…');
  try {
    const message = await action();
    status(message || 'OK');
  } catch (error) {
    status(error.message, true);
  } finally {
    $('#controls').disabled = false;
  }
}

function button(text, action, className = 'secondary') {
  const node = element('button', text, className);
  node.type = 'button';
  node.addEventListener('click', () => run(action));
  return node;
}

function renderDecks() {
  $('#decks').replaceChildren(...decks.map((deck) => {
    const node = button(deck.name, async () => { await selectDeck(deck.deck_id); });
    node.setAttribute('aria-current', String(deck.deck_id === selectedId));
    return node;
  }));
  if (!decks.length) $('#decks').append(element('p', 'Chưa có deck.', 'muted'));
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
  $('#deck-title').textContent = deck ? `Deck #${deck.deck_id}` : 'Chọn hoặc tạo deck';
  if (!deck) { $('#cards').replaceChildren(); return; }
  $('#edit-deck').elements.name.value = deck.name;
  $('#edit-deck').elements.description.value = deck.description || '';
  await loadCards();
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
  box.append(element('h3', card.word.word));
  box.append(element('p', `Card #${card.card_id} · Deck #${card.deck_id} · Box ${card.progress_level} · Đúng ${card.review_correct_count}/${card.review_total_count} · v${card.review_version}`, 'muted'));
  box.append(element('p', `Lịch ôn: ${card.next_reviewed_date ? new Date(card.next_reviewed_date).toLocaleString() : 'Chưa ôn'}`, 'muted'));
  return box;
}

async function loadCards() {
  if (selectedId === null) return;
  const cards = await api('GET', `/decks/${selectedId}/cards`);
  $('#cards').replaceChildren();
  if (!cards.length) $('#cards').append(element('p', 'Deck chưa có card.', 'muted'));
  for (const card of cards) {
    const box = cardHeader(card);
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
    box.append(form);
    $('#cards').append(box);
  }
}

async function loadReviews() {
  const cards = await api('GET', '/reviews/due');
  reviewsLoaded = true;
  $('#reviews').replaceChildren();
  if (!cards.length) $('#reviews').append(element('p', 'Không có card đến hạn.', 'muted'));
  for (const card of cards) {
    const box = cardHeader(card);
    const answer = wordDetails(card);
    if (card.notes) answer.append(element('p', `Ghi chú: ${card.notes}`));
    answer.hidden = true;
    const actions = element('div', undefined, 'row');
    actions.hidden = true;
    for (const [text, isCorrect] of [['Đúng', true], ['Sai', false]]) {
      actions.append(button(text, async () => {
        await api('POST', `/reviews/${card.card_id}`, { is_correct: isCorrect, expected_review_version: card.review_version });
        await refreshCardsAndReviews();
        return `Đã ghi nhận: ${text.toLowerCase()}`;
      }));
    }
    const reveal = element('button', 'Xem đáp án', 'secondary');
    reveal.type = 'button';
    reveal.addEventListener('click', () => { answer.hidden = false; actions.hidden = false; reveal.hidden = true; });
    box.append(reveal, answer, actions);
    $('#reviews').append(box);
  }
}

async function refreshCardsAndReviews() {
  await loadCards();
  if (reviewsLoaded) await loadReviews();
}

$('#auth-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const action = event.submitter?.value || 'login';
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
    await loadDecks();
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
    await loadDecks(deck.deck_id);
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
  return 'Đã xóa deck';
}));
$('#refresh-decks').addEventListener('click', () => run(() => loadDecks()));
$('#refresh-cards').addEventListener('click', () => run(() => loadCards()));
$('#load-reviews').addEventListener('click', () => run(() => loadReviews()));
$('#logout').addEventListener('click', () => { logout(); status('Đã đăng xuất'); });
session();
if (token) run(() => loadDecks());
