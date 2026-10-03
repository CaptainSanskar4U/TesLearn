async function apiPost(path, body, timeoutMs = 180000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    return res;
  } finally {
    clearTimeout(t);
  }
}

async function checkGuardrail(prompt) {
  const res = await apiPost('/api/guardrail/check', { prompt }, 60000);
  if (!res.ok) return { allowed: false, reason: `Guardrail failed (${res.status})` };
  const data = await res.json();
  return { allowed: !!data.allowed, reason: data.reason || 'Blocked' };
}

async function checkLiveBackend() {
  const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(8000) });
  if (!res.ok) throw new Error('Backend unavailable');
  return res.json();
}

async function loadResource(kind, topic) {
  const guard = await checkGuardrail(topic);
  if (!guard.allowed) throw new Error(guard.reason);

  switch (kind) {
    case 'video': {
      const res = await apiPost('/api/video', { topic, duration: 12 });
      if (!res.ok) throw new Error(`Video API ${res.status}`);
      const data = await res.json();
      return { type: 'video', embed_url: data.embed_url, title: topic };
    }
    case 'podcast': {
      const res = await apiPost('/api/podcast', { topic });
      if (!res.ok) throw new Error(`Podcast API ${res.status}`);
      const data = await res.json();
      return { type: 'podcast', audio_url: data.audio_url, title: topic };
    }
    case 'mindmap': {
      const res = await apiPost('/api/mindmap', { topic });
      if (!res.ok) throw new Error(`Mindmap API ${res.status}`);
      const data = await res.json();
      return { type: 'mindmap', html_url: data.html_url, title: topic };
    }
    case 'notes': {
      const res = await apiPost('/api/notes', { topic });
      if (!res.ok) throw new Error(`Notes API ${res.status}`);
      const data = await res.json();
      return { type: 'notes', markdown: data.notes_markdown, title: topic };
    }
    case 'lab': {
      const res = await apiPost('/api/lab', { topic });
      if (!res.ok) throw new Error(`Lab API ${res.status}`);
      const data = await res.json();
      return { type: 'lab', html_url: data.html_url, title: topic };
    }
    case 'comic': {
      const res = await apiPost('/api/comic', { topic }, 300000);
      if (!res.ok) throw new Error(`Comic API ${res.status}`);
      const data = await res.json();
      return {
        type: 'comic',
        image_urls: data.image_urls || [],
        panels: data.panels || [],
        title: data.title || topic,
      };
    }
    case 'viva': {
      await checkLiveBackend();
      return { type: 'viva', title: topic, liveMode: 'viva' };
    }
    case 'screenReader': {
      await checkLiveBackend();
      return { type: 'screenReader', title: topic, liveMode: 'screen' };
    }
    case 'chat':
      return { type: 'chat', title: topic };
    default:
      throw new Error(`Unknown resource: ${kind}`);
  }
}
