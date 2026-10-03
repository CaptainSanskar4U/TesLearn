const API_BASE = localStorage.getItem('teslearn_api') || 'http://127.0.0.1:8000';

function wsUrl(mode) {
  const base = API_BASE.replace(/^https:/, 'wss:').replace(/^http:/, 'ws:');
  let url = `${base}/api/client/ws?mode=${encodeURIComponent(mode)}`;
  if (mode === 'viva' && typeof Store !== 'undefined' && Store.topic) {
    url += `&topic=${encodeURIComponent(Store.topic)}`;
  }
  return url;
}
