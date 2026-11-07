(() => {
  const models = JSON.parse(document.getElementById('model-catalog').textContent);
  const selected = new Set(['sdxl-lightning', 'flux-pro']);
  const maxModels = 4;
  const prompt = document.getElementById('prompt-input');
  const form = document.getElementById('generation-form');
  const generateButton = document.getElementById('generate-button');
  const comparison = document.getElementById('comparison');
  const resultGrid = document.getElementById('result-grid');
  const historyList = document.getElementById('history-list');
  let pollTimer = null;

  function renderModelCards() {
    const grid = document.getElementById('model-grid');
    grid.replaceChildren(...models.map(model => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = `model-card${selected.has(model.key) ? ' selected' : ''}`;
      button.setAttribute('aria-pressed', selected.has(model.key));
      button.dataset.key = model.key;
      button.innerHTML = `<span class="model-check" aria-hidden="true">✓</span><span class="model-category">${escapeHtml(model.category)}</span><strong>${escapeHtml(model.name)}</strong><span class="model-description">${escapeHtml(model.description)}</span>`;
      button.addEventListener('click', () => {
        if (selected.has(model.key)) selected.delete(model.key);
        else if (selected.size < maxModels) selected.add(model.key);
        else showToast('Compare up to four models at a time.');
        renderModelCards();
      });
      return button;
    }));
  }

  function renderResults(data) {
    comparison.hidden = false;
    document.getElementById('overall-status').textContent = data.status;
    document.getElementById('overall-status').className = `status-pill ${data.status}`;
    document.getElementById('run-prompt').textContent = data.prompt;
    resultGrid.replaceChildren(...data.models.map(model => {
      const card = document.createElement('article');
      card.className = 'result-card';
      const heading = document.createElement('div');
      heading.className = 'result-card-heading';
      const title = document.createElement('h3');
      title.textContent = model.name;
      const status = document.createElement('span');
      status.className = `status-pill ${model.status}`;
      status.textContent = model.status;
      heading.append(title, status);
      card.append(heading);
      if (model.images.length) {
        const images = document.createElement('div');
        images.className = 'images';
        model.images.forEach((url, index) => {
          const image = document.createElement('img');
          image.src = url;
          image.alt = `${model.name} generated image ${index + 1}`;
          image.loading = 'lazy';
          image.addEventListener('click', () => openImage(url, image.alt));
          images.append(image);
        });
        card.append(images);
      } else {
        const placeholder = document.createElement('div');
        placeholder.className = `image-placeholder ${model.status}`;
        placeholder.textContent = model.status === 'failed' || model.status === 'canceled' ? (model.error || 'This model did not return an image.') : 'Generating image…';
        card.append(placeholder);
      }
      return card;
    }));
  }

  async function submitGeneration(event) {
    event.preventDefault();
    const text = prompt.value.trim();
    if (text.length < 5) return showToast('Add a prompt with at least 5 characters.');
    if (selected.size < 1) return showToast('Select at least one model.');
    generateButton.disabled = true;
    generateButton.innerHTML = 'Starting models…';
    try {
      const response = await fetch('/api/generations/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ prompt: text, models: [...selected] }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
      renderResults(data);
      comparison.scrollIntoView({ behavior: 'smooth', block: 'start' });
      await pollGeneration(data.id);
      await loadHistory();
    } catch (error) {
      showToast(error.message || 'Could not start generation.');
    } finally {
      generateButton.disabled = false;
      generateButton.innerHTML = 'Generate comparison <span aria-hidden="true">↗</span>';
    }
  }

  async function pollGeneration(id) {
    clearTimeout(pollTimer);
    const deadline = Date.now() + 6 * 60 * 1000;
    while (Date.now() < deadline) {
      const response = await fetch(`/api/generations/${encodeURIComponent(id)}/`, { cache: 'no-store' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not refresh generation status.');
      renderResults(data);
      if (data.status === 'succeeded' || data.status === 'failed') return;
      await new Promise(resolve => { pollTimer = setTimeout(resolve, 2000); });
    }
    showToast('Generation is taking longer than expected. This page can continue checking from history.');
  }

  async function loadHistory() {
    try {
      const response = await fetch('/api/history/', { cache: 'no-store' });
      const data = await response.json();
      if (!response.ok) throw new Error('History could not be loaded.');
      historyList.replaceChildren();
      if (!data.items.length) {
        const empty = document.createElement('p');
        empty.className = 'hint';
        empty.textContent = 'Your generated comparisons will appear here.';
        historyList.append(empty);
        return;
      }
      data.items.forEach(item => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'history-item';
        const copy = document.createElement('span');
        copy.textContent = item.prompt;
        const status = document.createElement('span');
        status.className = `status-pill ${item.status}`;
        status.textContent = item.status;
        button.append(copy, status);
        button.addEventListener('click', async () => {
          const response = await fetch(`/api/generations/${encodeURIComponent(item.id)}/`);
          const result = await response.json();
          if (response.ok) { renderResults(result); comparison.scrollIntoView({ behavior: 'smooth' }); }
        });
        historyList.append(button);
      });
    } catch {
      historyList.innerHTML = '<p class="hint">History is temporarily unavailable.</p>';
    }
  }

  function openImage(url, alt) {
    const overlay = document.createElement('div');
    overlay.className = 'lightbox';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', alt);
    const image = document.createElement('img');
    image.src = url;
    image.alt = alt;
    overlay.append(image);
    overlay.addEventListener('click', () => overlay.remove());
    document.body.append(overlay);
  }

  function getCookie(name) {
    const row = document.cookie.split('; ').find(item => item.startsWith(`${name}=`));
    return row ? decodeURIComponent(row.split('=').slice(1).join('=')) : '';
  }
  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  }
  function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.append(toast);
    setTimeout(() => toast.remove(), 4000);
  }

  prompt.addEventListener('input', () => { document.getElementById('prompt-count').textContent = `${prompt.value.length.toLocaleString()} / 2,000`; });
  form.addEventListener('submit', submitGeneration);
  document.getElementById('refresh-history').addEventListener('click', loadHistory);
  renderModelCards();
  loadHistory();
})();
