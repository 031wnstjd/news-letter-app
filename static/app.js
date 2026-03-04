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

function buildMarkdownFallback(item) {
  const lines = Array.isArray(item.lines) ? item.lines.filter((line) => String(line || '').trim()) : [];
  if (lines.length) {
    return ['### 핵심 정리', ...lines.map((line) => `- ${line}`)].join('\n');
  }
  const tldr = String(item.tldr || '').trim();
  if (tldr) {
    return `### 핵심 정리\n- ${tldr}`;
  }
  return '### 핵심 정리\n- 카드 본문을 생성 중입니다.';
}

function renderCards(container, items) {
  container.innerHTML = '';
  if (!Array.isArray(items) || items.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'empty-cards';
    empty.textContent = '표시할 카드가 아직 없습니다.';
    container.appendChild(empty);
    return;
  }
  items.forEach((item) => {
    const card = document.createElement('article');
    card.className = 'card';
    const articleUrl = safeUrl(item.url);
    const markdownSource = String(item.markdown || '').trim() ? item.markdown : buildMarkdownFallback(item);
    const markdownHtml = renderMarkdownToHtml(markdownSource);

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

function renderPreviewPayload(data) {
  let summaryMode = 'AI 요약 적용';
  if (!data.ai_used && data.ai_error) {
    summaryMode = `AI 요약 실패(${data.ai_error})`;
  } else if (!data.ai_used) {
    summaryMode = 'AI 요약 실패';
  }
  previewMeta.textContent = `${data.subject || '프리뷰'} | ${data.badge || ''} | ${summaryMode}`;
  renderCards(hotList, data.hot || []);
  renderCards(moreList, data.bottom || []);
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
  let fallbackTriggered = false;
  let lastEventAt = Date.now();
  const renderedByIndex = new Map();
  const idleTimer = window.setInterval(() => {
    if (gotDone) return;
    const idleSeconds = (Date.now() - lastEventAt) / 1000;
    if (idleSeconds >= 12) {
      statusText.textContent = `응답 대기 중... (${Math.floor(idleSeconds)}초)`;
    }
  }, 2000);

  function finalize() {
    window.clearInterval(idleTimer);
    if (previewStream) {
      previewStream.close();
      previewStream = null;
    }
    previewBtn.disabled = false;
  }

  async function fetchSnapshotFallback(reason) {
    if (fallbackTriggered || gotDone) return;
    fallbackTriggered = true;
    statusText.textContent = `실시간 연결 복구 중... (${reason})`;
    try {
      const res = await fetch(`/v1/newsletter/preview?limit=${PREVIEW_LIMIT}`);
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || '프리뷰 조회 실패');
      }
      renderPreviewPayload(data);
      statusText.textContent = '완료';
      gotDone = true;
    } catch (err) {
      statusText.textContent = `오류: ${err.message || '프리뷰 생성 실패'}`;
    } finally {
      finalize();
    }
  }

  stream.addEventListener('progress', (event) => {
    try {
      const data = JSON.parse(event.data || '{}');
      lastEventAt = Date.now();
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
      if (data.stage === 'item_done' && data.item) {
        const index = Number.isFinite(data.index) ? data.index : renderedByIndex.size;
        renderedByIndex.set(index, data.item);
        const ordered = Array.from(renderedByIndex.entries())
          .sort((a, b) => a[0] - b[0])
          .map((entry) => entry[1]);
        renderCards(hotList, ordered.slice(0, 2));
        renderCards(moreList, ordered.slice(2));
      }
    } catch (_err) {
      statusText.textContent = '진행 상태를 업데이트하는 중입니다...';
    }
  });

  stream.addEventListener('done', (event) => {
    gotDone = true;
    try {
      const data = JSON.parse(event.data || '{}');
      renderPreviewPayload(data);
      statusText.textContent = '완료';
    } catch (err) {
      fetchSnapshotFallback(err.message || 'done_parse_error');
      return;
    }
    finalize();
  });

  stream.addEventListener('failed', (event) => {
    try {
      const data = JSON.parse(event.data || '{}');
      fetchSnapshotFallback(data.detail || data.message || 'stream_failed');
      return;
    } catch (_err) {
      fetchSnapshotFallback('stream_failed');
      return;
    }
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
    fetchSnapshotFallback('stream_error');
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
