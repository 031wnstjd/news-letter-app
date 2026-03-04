const previewBtn = document.getElementById('previewBtn');
const statusText = document.getElementById('statusText');
const previewMeta = document.getElementById('previewMeta');
const hotList = document.getElementById('hotList');
const moreList = document.getElementById('moreList');
const progressList = document.getElementById('progressList');

const manualForm = document.getElementById('manualForm');
const summaryLines = document.getElementById('summaryLines');
let previewStream = null;
const PREVIEW_LIMIT = 4;

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

    if (line.startsWith('> ')) {
      closeList();
      chunks.push(`<blockquote>${formatInlineMarkdown(line.slice(2))}</blockquote>`);
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
  if (previewStream) {
    previewStream.close();
    previewStream = null;
  }
  statusText.textContent = '프리뷰 생성 시작...';
  previewMeta.textContent = '진행률: 0%';
  progressList.innerHTML = '';
  hotList.innerHTML = '';
  moreList.innerHTML = '';
  previewBtn.disabled = true;
  const stream = new EventSource(`/v1/newsletter/preview/stream?limit=${PREVIEW_LIMIT}`);
  previewStream = stream;
  let gotDone = false;
  let errorCount = 0;

  function finalize() {
    if (previewStream) {
      previewStream.close();
      previewStream = null;
    }
    previewBtn.disabled = false;
  }

  stream.addEventListener('progress', (event) => {
    try {
      const data = JSON.parse(event.data || '{}');
      const percent = Number.isFinite(data.percent) ? data.percent : 0;
      const progressText = data.total ? `(${data.current || 0}/${data.total})` : '';
      statusText.textContent = data.message || '처리 중...';
      previewMeta.textContent = `진행률: ${percent}% ${progressText}`.trim();
      if (data.stage === 'item_done' && data.title) {
        const li = document.createElement('li');
        li.textContent = `${data.current}/${data.total} 완료 - ${data.title}`;
        progressList.prepend(li);
        while (progressList.children.length > 6) {
          progressList.removeChild(progressList.lastChild);
        }
      }
    } catch (_err) {
      statusText.textContent = '진행 상태를 업데이트하는 중입니다...';
    }
  });

  stream.addEventListener('done', (event) => {
    gotDone = true;
    try {
      const data = JSON.parse(event.data || '{}');
      const aiState = data.ai_used ? '예' : '아니오';
      const aiReason = !data.ai_used && data.ai_error ? ` | AI 실패 원인: ${data.ai_error}` : '';
      previewMeta.textContent = `${data.subject} | ${data.badge} | AI 요약 사용: ${aiState}${aiReason}`;
      renderCards(hotList, data.hot || []);
      renderCards(moreList, data.bottom || []);
      statusText.textContent = '완료';
    } catch (err) {
      statusText.textContent = `오류: ${err.message}`;
    } finally {
      finalize();
    }
  });

  stream.addEventListener('failed', (event) => {
    try {
      const data = JSON.parse(event.data || '{}');
      statusText.textContent = `오류: ${data.detail || data.message || '프리뷰 생성 실패'}`;
    } catch (_err) {
      statusText.textContent = '오류: 프리뷰 생성에 실패했습니다.';
    }
    finalize();
  });

  stream.onerror = () => {
    if (gotDone) {
      return;
    }
    errorCount += 1;
    if (errorCount < 3) {
      statusText.textContent = `연결 재시도 중... (${errorCount}/2)`;
      return;
    }
    statusText.textContent = '오류: 실시간 연결이 불안정합니다. 다시 시도하세요.';
    finalize();
  };
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
