/** Interactive comic book — open spread (2 pages) with page-turn. */
const ComicBook = {
  escapeHtml(text) {
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  },

  normalizePanels(result) {
    if (result.panels?.length) return result.panels;
    return (result.image_urls || []).map((url) => ({ url, caption: '', dialogue: '' }));
  },

  toSpreads(panels) {
    const spreads = [];
    for (let i = 0; i < panels.length; i += 2) {
      spreads.push({ left: panels[i], right: panels[i + 1] || null });
    }
    return spreads;
  },

  pageSideHtml(panel, side, pageNum, total) {
    if (!panel) {
      return `<div class="comic-page comic-page--${side} comic-page--blank" aria-hidden="true"></div>`;
    }
    const caption = panel.caption
      ? `<div class="comic-caption">${this.escapeHtml(panel.caption)}</div>`
      : '';
    const dialogue = panel.dialogue
      ? `<div class="comic-dialogue">${this.escapeHtml(panel.dialogue)}</div>`
      : '';
    return `
      <div class="comic-page comic-page--${side}">
        <div class="comic-page-inner">
          <img src="${panel.url}" alt="Comic page ${pageNum}" draggable="false" loading="lazy" />
          ${caption}${dialogue}
          <span class="comic-page-num">${pageNum} / ${total}</span>
        </div>
      </div>`;
  },

  spreadHtml(spread, spreadIndex, spreads, panels) {
    const leftNum = spreadIndex * 2 + 1;
    const rightNum = spreadIndex * 2 + 2;
    return `
      <div class="comic-spread" data-spread="${spreadIndex}">
        ${this.pageSideHtml(spread.left, 'left', leftNum, panels.length)}
        <div class="comic-spread-gutter" aria-hidden="true"></div>
        ${this.pageSideHtml(spread.right, 'right', rightNum, panels.length)}
      </div>`;
  },

  mount(container, result) {
    const panels = this.normalizePanels(result);
    if (!panels.length) {
      container.innerHTML = '<p class="muted" style="padding:1.5rem">No comic pages found.</p>';
      return;
    }

    const spreads = this.toSpreads(panels);
    const title = this.escapeHtml(result.title || 'Comic');
    let spreadIndex = 0;
    let busy = false;

    container.innerHTML = `
      <div class="comic-book" id="comicBook" tabindex="0">
        <div class="comic-book-shell">
          <div class="comic-book-edge" aria-hidden="true"></div>
          <div class="comic-book-viewport comic-book-viewport--spread" id="comicViewport">
            <div class="comic-book-layer comic-book-layer--base" id="comicBase"></div>
            <div class="comic-book-layer comic-book-layer--flip is-idle" id="comicFlip" aria-hidden="true"></div>
            <button type="button" class="comic-hit comic-hit--prev" id="comicHitPrev" aria-label="Previous spread"></button>
            <button type="button" class="comic-hit comic-hit--next" id="comicHitNext" aria-label="Next spread"></button>
          </div>
          <div class="comic-book-spine" aria-hidden="true"></div>
        </div>
        <p class="comic-book-title">${title}</p>
        <div class="comic-book-toolbar">
          <button type="button" class="btn btn-ghost" id="comicPrev" aria-label="Previous spread">← Prev</button>
          <span class="comic-book-indicator" id="comicIndicator"></span>
          <button type="button" class="btn btn-ghost" id="comicNext" aria-label="Next spread">Next →</button>
        </div>
      </div>`;

    const base = container.querySelector('#comicBase');
    const flip = container.querySelector('#comicFlip');
    const indicator = container.querySelector('#comicIndicator');
    const prevBtn = container.querySelector('#comicPrev');
    const nextBtn = container.querySelector('#comicNext');
    const hitPrev = container.querySelector('#comicHitPrev');
    const hitNext = container.querySelector('#comicHitNext');

    const renderSpread = (el, idx) => {
      el.innerHTML = this.spreadHtml(spreads[idx], idx, spreads, panels);
    };

    const labelFor = (idx) => {
      if (spreads.length <= 1) return `${panels.length} page${panels.length === 1 ? '' : 's'}`;
      const start = idx * 2 + 1;
      const end = Math.min((idx + 1) * 2, panels.length);
      return `Pages ${start}–${end} · ${idx + 1} / ${spreads.length}`;
    };

    const syncControls = () => {
      indicator.textContent = labelFor(spreadIndex);
      const atStart = spreadIndex === 0;
      const atEnd = spreadIndex >= spreads.length - 1;
      prevBtn.disabled = atStart || busy;
      nextBtn.disabled = atEnd || busy;
      hitPrev.disabled = atStart || busy;
      hitNext.disabled = atEnd || busy;
    };

    const hideFlip = () => {
      flip.className = 'comic-book-layer comic-book-layer--flip is-idle';
      flip.innerHTML = '';
      flip.setAttribute('aria-hidden', 'true');
    };

    const showFlip = (className, html) => {
      flip.innerHTML = html;
      flip.className = `comic-book-layer comic-book-layer--flip ${className}`;
      flip.removeAttribute('aria-hidden');
    };

    const finishFlip = (nextIndex) => {
      spreadIndex = nextIndex;
      renderSpread(base, spreadIndex);
      hideFlip();
      busy = false;
      syncControls();
    };

    const turnForward = () => {
      if (busy || spreadIndex >= spreads.length - 1) return;
      busy = true;
      syncControls();

      const nextIndex = spreadIndex + 1;
      renderSpread(base, nextIndex);
      showFlip('is-turning-forward', this.spreadHtml(spreads[spreadIndex], spreadIndex, spreads, panels));

      const onEnd = (e) => {
        if (e.target !== flip || e.propertyName !== 'transform') return;
        flip.removeEventListener('transitionend', onEnd);
        finishFlip(nextIndex);
      };
      flip.addEventListener('transitionend', onEnd);
    };

    const turnBackward = () => {
      if (busy || spreadIndex <= 0) return;
      busy = true;
      syncControls();

      const prevIndex = spreadIndex - 1;
      showFlip(
        'is-turning-backward-start',
        this.spreadHtml(spreads[prevIndex], prevIndex, spreads, panels),
      );

      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          flip.className = 'comic-book-layer comic-book-layer--flip is-turning-backward';
        });
      });

      const onEnd = (e) => {
        if (e.target !== flip || e.propertyName !== 'transform') return;
        flip.removeEventListener('transitionend', onEnd);
        finishFlip(prevIndex);
      };
      flip.addEventListener('transitionend', onEnd);
    };

    prevBtn.addEventListener('click', turnBackward);
    nextBtn.addEventListener('click', turnForward);
    hitPrev.addEventListener('click', turnBackward);
    hitNext.addEventListener('click', turnForward);

    container.querySelector('#comicBook')?.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft') turnBackward();
      if (e.key === 'ArrowRight') turnForward();
    });

    let touchX = null;
    container.querySelector('#comicViewport')?.addEventListener('touchstart', (e) => {
      touchX = e.changedTouches[0]?.clientX ?? null;
    }, { passive: true });
    container.querySelector('#comicViewport')?.addEventListener('touchend', (e) => {
      if (touchX == null) return;
      const dx = (e.changedTouches[0]?.clientX ?? touchX) - touchX;
      if (dx < -40) turnForward();
      if (dx > 40) turnBackward();
      touchX = null;
    }, { passive: true });

    renderSpread(base, spreadIndex);
    hideFlip();
    syncControls();
  },
};
