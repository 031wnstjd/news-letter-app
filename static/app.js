const previewBtn = document.getElementById('previewBtn');
const statusText = document.getElementById('statusText');
const previewMeta = document.getElementById('previewMeta');
const hotList = document.getElementById('hotList');
const moreList = document.getElementById('moreList');

const manualForm = document.getElementById('manualForm');
const summaryLines = document.getElementById('summaryLines');

function renderCards(container, items) {
  container.innerHTML = '';
  items.forEach((item) => {
    const card = document.createElement('article');
    card.className = 'card';
    card.innerHTML = `
      <a href="${item.url}" target="_blank" rel="noopener noreferrer">${item.title}</a>
      <div><small>출처: ${item.source_domain || '알 수 없음'}</small></div>
      <p>${item.tldr || ''}</p>
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
