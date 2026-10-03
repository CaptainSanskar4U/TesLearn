/** Markdown → safe HTML with KaTeX (requires marked, DOMPurify, katex on page). */
const MD = {
  _mathStore: [],

  ready() {
    if (window.marked) {
      marked.setOptions({ breaks: true, gfm: true });
    }
  },

  _placeholder(i) {
    return `\uE000MATH${i}\uE001`;
  },

  _normalizeMath(tex) {
    // LLMs often emit `\` instead of `\\` before line breaks in aligned/array blocks.
    return tex.replace(/\\(\r?\n)/g, '\\\\$1');
  },

  _protectMath(text) {
    this._mathStore = [];
    const store = (tex, display) => {
      const i = this._mathStore.length;
      this._mathStore.push({ tex: this._normalizeMath(tex.trim()), display });
      return this._placeholder(i);
    };

    let out = String(text);
    out = out.replace(/\$\$([\s\S]+?)\$\$/g, (_, tex) => store(tex, true));
    out = out.replace(/\\\[([\s\S]+?)\\\]/g, (_, tex) => store(tex, true));
    out = out.replace(/\\\(([\s\S]+?)\\\)/g, (_, tex) => store(tex, false));
    out = out.replace(/(?<![\\$])\$(?!\$)((?:\\.|[^$\\])+)\$(?!\$)/g, (_, tex) => store(tex, false));
    return out;
  },

  _renderMath(tex, display) {
    if (!window.katex) return display ? `$$${tex}$$` : `$${tex}$`;
    try {
      return katex.renderToString(tex, {
        displayMode: display,
        throwOnError: false,
        strict: 'ignore',
        trust: true,
      });
    } catch {
      return display ? `$$${tex}$$` : `$${tex}$`;
    }
  },

  _restoreMath(html) {
    return html.replace(/\uE000MATH(\d+)\uE001/g, (_, idx) => {
      const block = this._mathStore[Number(idx)];
      if (!block) return '';
      return this._renderMath(block.tex, block.display);
    });
  },

  render(text) {
    if (!text) return '';
    this.ready();

    if (window.marked) {
      const protectedText = this._protectMath(text);
      let html = marked.parse(protectedText);
      if (window.DOMPurify) html = DOMPurify.sanitize(html);
      return this._restoreMath(html);
    }

    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br>');
  },

  typeset(el) {
    if (!el || !window.renderMathInElement) return;
    renderMathInElement(el, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '$', right: '$', display: false },
        { left: '\\(', right: '\\)', display: false },
        { left: '\\[', right: '\\]', display: true },
      ],
      throwOnError: false,
    });
  },
};

MD.ready();
