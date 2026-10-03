const Store = {
  get topic() {
    return sessionStorage.getItem('topic') || '';
  },
  set topic(v) {
    sessionStorage.setItem('topic', v);
  },
  get kind() {
    return sessionStorage.getItem('kind') || '';
  },
  set kind(v) {
    sessionStorage.setItem('kind', v);
  },
  get result() {
    try {
      return JSON.parse(sessionStorage.getItem('result') || '{}');
    } catch {
      return {};
    }
  },
  set result(v) {
    sessionStorage.setItem('result', JSON.stringify(v));
  },
  get chatMessages() {
    try {
      return JSON.parse(sessionStorage.getItem('chatMessages') || '[]');
    } catch {
      return [];
    }
  },
  set chatMessages(v) {
    sessionStorage.setItem('chatMessages', JSON.stringify(v));
  },
  clearChat() {
    sessionStorage.removeItem('chatMessages');
  },
};
