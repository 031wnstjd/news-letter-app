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

function formatInlineMarkdown(value) {
  let formatted = escapeHtml(value);
  formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  formatted = formatted.replace(/`(.+?)`/g, '<code>$1</code>');
  return formatted;
}

function renderMarkdownToHtml(markdown) {
  const lines = String(markdown || '').split('\n');
  const chunks = [];
  let listMode = null;

  function closeList() {
    if (listMode === 'ul') chunks.push('</ul>');
    if (listMode === 'ol') chunks.push('</ol>');
    listMode = null;
  }

  lines.forEach((rawLine) => {
    const line = rawLine.trim();
    if (!line) {
      closeList();
      return;
    }

    if (line.startsWith('### ')) {
      closeList();
      chunks.push(`<h4>${formatInlineMarkdown(line.slice(4))}</h4>`);
      return;
    }

    if (line.startsWith('- ')) {
      if (listMode !== 'ul') {
        closeList();
        chunks.push('<ul>');
        listMode = 'ul';
      }
      chunks.push(`<li>${formatInlineMarkdown(line.slice(2))}</li>`);
      return;
    }

    const orderedMatch = line.match(/^(\d+)\.\s+(.+)$/);
    if (orderedMatch) {
      if (listMode !== 'ol') {
        closeList();
        chunks.push('<ol>');
        listMode = 'ol';
      }
      chunks.push(`<li>${formatInlineMarkdown(orderedMatch[2])}</li>`);
      return;
    }

    closeList();
    chunks.push(`<p>${formatInlineMarkdown(line)}</p>`);
  });

  closeList();
  return chunks.join('');
}

function renderCards(container, items) {
  container.innerHTML = '';
  items.forEach((item) => {
    const card = document.createElement('article');
    card.className = 'card';
    const articleUrl = safeUrl(item.url);
    const markdownHtml = renderMarkdownToHtml(item.markdown || '');

    card.innerHTML = `
      <a href="${escapeHtml(articleUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title)}</a>
      <div class="card-meta">
        <small>출처: ${escapeHtml(item.source_domain || '알 수 없음')}</small>
        <small>카테고리: ${escapeHtml(item.category || '기타')}</small>
      </div>
      <div class="md-view">${markdownHtml}</div>
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
