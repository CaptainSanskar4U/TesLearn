/** Simulated ETA countdown while resources generate. */
const ETA_MAX = 60;

const ETA = {
  video: 90,
  podcast: 120,
  mindmap: 45,
  notes: 60,
  lab: 90,
  comic: 60,
  viva: 8,
  screenReader: 8,
  chat: 5,
};

function formatEta(seconds) {
  if (seconds <= 0) return 'Almost ready…';
  if (seconds < 60) return `About ${seconds}s remaining`;
  const mins = Math.ceil(seconds / 60);
  return mins === 1 ? 'About 1 min remaining' : `About ${mins} min remaining`;
}

function startSimulatedEta(kind) {
  const etaEl = document.getElementById('eta');
  const fillEl = document.getElementById('etaFill');
  if (!etaEl) return () => {};

  const total = Math.min(ETA[kind] ?? ETA_MAX, ETA_MAX);
  let elapsed = 0;

  etaEl.classList.remove('hidden');
  etaEl.textContent = formatEta(total);
  if (fillEl) fillEl.style.width = '0%';

  const timer = setInterval(() => {
    elapsed += 1;
    const remaining = Math.max(0, total - elapsed);
    etaEl.textContent = formatEta(remaining);
    if (fillEl) {
      const pct = Math.min(92, (elapsed / total) * 100);
      fillEl.style.width = `${pct}%`;
    }
  }, 1000);

  return () => {
    clearInterval(timer);
    if (fillEl) fillEl.style.width = '100%';
    etaEl.textContent = 'Finishing up…';
  };
}
