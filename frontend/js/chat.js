async function sendChatMessage(topic, messages) {
  const res = await apiPost('/api/chat', { topic, messages }, 90000);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || data.reason || `Chat API ${res.status}`);
  }
  return data.reply;
}
