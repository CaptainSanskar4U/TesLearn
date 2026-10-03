const UI = {
  LOGO: 'logo.png',

  initTheme() {
    const saved = localStorage.getItem('teslearn_theme');
    const dark = saved === 'dark';
    document.documentElement.classList.toggle('dark', dark);
  },

  toggleTheme() {
    const next = !document.documentElement.classList.contains('dark');
    document.documentElement.classList.toggle('dark', next);
    localStorage.setItem('teslearn_theme', next ? 'dark' : 'light');
  },

  mountNav({ backHref = null, title = 'TesLearn', showLogo = true, showBrand = true, showHistory = true } = {}) {
    const el = document.getElementById('nav');
    if (!el) return;
    const logo = showLogo
      ? `<img src="${this.LOGO}" alt="" class="brand-logo" width="36" height="36" />`
      : '';
    const brand = showBrand
      ? `<a href="index.html" class="brand">${logo}<span>${title}</span></a>`
      : '';
    const historyLink = showHistory
      ? `<a href="history.html" class="icon-btn" aria-label="History" title="History">⌛</a>`
      : '';
    el.innerHTML = `
      <nav class="glass-nav">
        <div style="display:flex;align-items:center;gap:0.75rem">
          ${backHref ? `<a href="${backHref}" class="icon-btn" aria-label="Back">←</a>` : ''}
          ${brand}
        </div>
        <div class="nav-actions">
          ${historyLink}
          <button type="button" class="icon-btn" id="themeToggle" aria-label="Toggle theme">◐</button>
        </div>
      </nav>`;
    document.getElementById('themeToggle')?.addEventListener('click', () => UI.toggleTheme());
  },

  toast(msg) {
    let t = document.getElementById('toast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'toast';
      t.style.cssText = 'position:fixed;bottom:1.5rem;left:50%;transform:translateX(-50%);padding:0.75rem 1.25rem;background:var(--card);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow-lg);font-size:0.875rem;z-index:50;opacity:0;transition:opacity .2s';
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.style.opacity = '1';
    setTimeout(() => { t.style.opacity = '0'; }, 2800);
  },
};

UI.initTheme();

if (!document.querySelector('link[rel="icon"]')) {
  const icon = document.createElement('link');
  icon.rel = 'icon';
  icon.type = 'image/png';
  icon.href = UI.LOGO;
  document.head.appendChild(icon);
}
