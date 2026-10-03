async function fetchList(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`${path} failed (${res.status})`);
  return res.json();
}

const TYPE_META = {
  video: { label: 'Video', icon: 'video.png', sub: 'Watch & understand' },
  podcast: { label: 'Podcast', icon: 'podcast.png', sub: 'Listen on the go' },
  mindmap: { label: 'Mindmap', icon: 'mindmap.png', sub: 'Visualize concepts' },
  notes: { label: 'Notes', icon: 'notes.png', sub: 'Study-ready notes' },
  lab: { label: 'Virtual Lab', icon: 'lab.png', sub: 'Interactive lab' },
  comic: { label: 'Comic Book', icon: 'comic.png', sub: 'Visual story' },
};

function toResult(type, row) {
  const title = row.title || row.topic;
  switch (type) {
    case 'video':
      return { type: 'video', title, embed_url: row.embed_url };
    case 'podcast':
      return { type: 'podcast', title, audio_url: row.audio_url };
    case 'mindmap':
      return { type: 'mindmap', title, html_url: row.html_url };
    case 'notes':
      return { type: 'notes', title, markdown: row.notes_markdown };
    case 'lab':
      return { type: 'lab', title, html_url: row.html_url };
    case 'comic':
      return {
        type: 'comic',
        title,
        image_urls: row.image_urls || [],
        panels: row.panels || [],
      };
    default:
      return null;
  }
}

async function loadHistory() {
  const [videos, podcasts, mindmaps, notes, labs, comics] = await Promise.all([
    fetchList('/api/video').catch(() => []),
    fetchList('/api/podcast').catch(() => []),
    fetchList('/api/mindmap').catch(() => []),
    fetchList('/api/notes').catch(() => []),
    fetchList('/api/lab').catch(() => []),
    fetchList('/api/comic').catch(() => []),
  ]);

  const items = [];
  videos.forEach((r) => items.push({ type: 'video', topic: r.topic, id: r.id, created_at: r.created_at, result: toResult('video', r) }));
  podcasts.forEach((r) => items.push({ type: 'podcast', topic: r.topic, id: r.id, created_at: r.created_at, result: toResult('podcast', r) }));
  mindmaps.forEach((r) => items.push({ type: 'mindmap', topic: r.topic, id: r.id, created_at: r.created_at, result: toResult('mindmap', r) }));
  notes.forEach((r) => items.push({ type: 'notes', topic: r.topic, id: r.id, created_at: r.created_at, result: toResult('notes', r) }));
  labs.forEach((r) => items.push({ type: 'lab', topic: r.topic, id: r.id, created_at: r.created_at, result: toResult('lab', r) }));
  comics.forEach((r) => items.push({
    type: 'comic',
    topic: r.topic,
    id: r.id,
    created_at: r.created_at,
    result: toResult('comic', r),
  }));

  items.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
  return items;
}
