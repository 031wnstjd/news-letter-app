const previewBtn = document.getElementById('previewBtn');
const statusText = document.getElementById('statusText');
const previewMeta = document.getElementById('previewMeta');
const hotList = document.getElementById('hotList');
const moreList = document.getElementById('moreList');

const manualForm = document.getElementById('manualForm');
const summaryLines = document.getElementById('summaryLines');

function escapeHtml(value) {
  return String(value || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function safeUrl(value) {
  const raw = String(value || '');
  if (raw.startsWith('http://') || raw.startsWith('https://')) {
    return raw;
  }
  return '#';
}

function renderCards(container, items) {
  container.innerHTML = '';
  items.forEach((item) => {
    const lines = Array.isArray(item.lines) ? item.lines : [];
    const headline = [lines[0], lines[1]].filter(Boolean).join(' ');
    const why = lines[2] || '';
    const apply = lines[3] || '';
    const extraPoints = lines.slice(4);

    const card = document.createElement('article');
    card.className = 'card';
    const articleUrl = safeUrl(item.url);
    const extraHtml = extraPoints.length
      ? `
        <div class="card-block">
          <strong>세부 포인트</strong>
          <ul class="card-point-list">
            ${extraPoints.map((point) => `<li>${escapeHtml(point)}</li>`).join('')}
          </ul>
        </div>
      `
      : '';

    card.innerHTML = `
      <a href="${escapeHtml(articleUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title)}</a>
      <div class="card-meta">
        <small>출처: ${escapeHtml(item.source_domain || '알 수 없음')}</small>
        <small>카테고리: ${escapeHtml(item.category || '기타')}</small>
      </div>
      <div class="card-block">
        <strong>핵심 정리</strong>
        <p>${escapeHtml(headline || item.tldr || '')}</p>
      </div>
      <div class="card-block">
        <strong>왜 중요한가</strong>
        <p>${escapeHtml(why)}</p>
      </div>
      <div class="card-block">
        <strong>실무 적용</strong>
        <p>${escapeHtml(apply)}</p>
      </div>
      ${extraHtml}
    `;
    container.appendChild(card);
  });
}

async function fetchPreview() {
  statusText.textContent = '프리뷰 생성 중...';
  previewBtn.disabled = true;
  try {
    const res = await fetch('/v1/newsletter/preview');
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || '프리뷰 생성에 실패했습니다');
    }

    previewMeta.textContent = `${data.subject} | ${data.badge} | AI 요약 사용: ${data.ai_used ? '예' : '아니오'}`;
    renderCards(hotList, data.hot || []);
    renderCards(moreList, data.bottom || []);
    statusText.textContent = '완료';
  } catch (err) {
    statusText.textContent = `오류: ${err.message}`;
  } finally {
    previewBtn.disabled = false;
  }
}

previewBtn.addEventListener('click', fetchPreview);

manualForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  summaryLines.innerHTML = '';

  const payload = {
    title: document.getElementById('title').value,
    url: document.getElementById('url').value,
    source_text: document.getElementById('sourceText').value,
  };

  const res = await fetch('/v1/summaries/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();

  if (!res.ok || !data.ok) {
    const li = document.createElement('li');
    li.textContent = data.error || '요약 실패';
    summaryLines.appendChild(li);
    return;
  }

  data.lines.forEach((line) => {
    const li = document.createElement('li');
    li.textContent = line;
    summaryLines.appendChild(li);
  });
});
