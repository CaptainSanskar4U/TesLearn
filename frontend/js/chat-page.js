(() => {
  const topic = Store.topic;
  if (!topic) {
    location.href = 'index.html';
    return;
  }

  document.getElementById('title').textContent = topic;

  const listEl = document.getElementById('messages');
  const inputEl = document.getElementById('input');
  const sendBtn = document.getElementById('send');
  const clearBtn = document.getElementById('clear');
  let messages = Store.chatMessages;
  let busy = false;

  function welcome() {
    return `Hi! I'm your AI tutor for "${topic}". Ask me anything about this lesson — definitions, examples, exam tips, or step-by-step explanations.`;
  }

  function render() {
    listEl.innerHTML = '';
    const all = messages.length
      ? messages
      : [{ role: 'assistant', content: welcome() }];

    all.forEach((m) => {
      const div = document.createElement('div');
      div.className = `chat-bubble ${m.role}${m.typing ? ' typing' : ''}`;
      if (m.role === 'assistant' && !m.typing) {
        div.innerHTML = `<div class="markdown-body">${MD.render(m.content)}</div>`;
      } else {
        div.textContent = m.content;
      }
      listEl.appendChild(div);
    });
    listEl.scrollTop = listEl.scrollHeight;
    listEl.querySelectorAll('.markdown-body').forEach((el) => MD.typeset(el));
  }

  function persist() {
    Store.chatMessages = messages.filter((m) => !m.typing);
  }

  async function send() {
    const text = inputEl.value.trim();
    if (!text || busy) return;

    busy = true;
    sendBtn.disabled = true;
    inputEl.value = '';

    messages.push({ role: 'user', content: text });
    messages.push({ role: 'assistant', content: 'Thinking…', typing: true });
    render();

    try {
      const history = messages.filter((m) => !m.typing);
      const reply = await sendChatMessage(topic, history);
      messages = messages.filter((m) => !m.typing);
      messages.push({ role: 'assistant', content: reply });
      persist();
    } catch (e) {
      messages = messages.filter((m) => !m.typing);
      UI.toast(e.message || String(e));
    }

    busy = false;
    sendBtn.disabled = false;
    render();
    inputEl.focus();
  }

  sendBtn.addEventListener('click', send);
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });

  clearBtn?.addEventListener('click', () => {
    messages = [];
    Store.clearChat();
    render();
  });

  render();
})();
