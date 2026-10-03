(() => {
  const params = new URLSearchParams(location.search);
  const mode = params.get('mode') || Store.result?.liveMode || 'viva';
  const isViva = mode === 'viva';
  const topic = Store.topic;
  if (!topic) location.href = 'index.html';

  document.getElementById('title').textContent = topic;
  document.getElementById('kicker').textContent =
    mode === 'screen' ? 'Screen Reader' : 'Live Viva';

  document.getElementById('vivaPanel')?.classList.toggle('hidden', !isViva);
  document.getElementById('screenPanel')?.classList.toggle('hidden', isViva);

  const api = isViva ? '/api/viva' : '/api/screen';
  let started = false;

  async function post(path, body) {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || data.error || `Request failed (${res.status})`);
    }
  }

  (async () => {
    try {
      if (isViva) await post(`${api}/start`, { topic });
      else await post(`${api}/start?mode=screen`);
      started = true;
    } catch (e) {
      console.error('Live session start failed:', e);
    }
  })();

  window.addEventListener('beforeunload', () => {
    if (!started) return;
    fetch(`${API_BASE}${api}/stop`, { method: 'POST', keepalive: true }).catch(() => {});
  });
})();
