/* Language toggle. The only script on the site.
   Loaded synchronously in <head> so the correct language is set before the
   body paints — no flash of the wrong language. Both languages are already in
   the DOM; CSS hides the inactive one. With JS disabled the page keeps the
   data-lang hardcoded in the HTML and still renders correctly. */
(function () {
  'use strict';

  var STORE = 'lang';
  var EN = 'en';
  var PT = 'pt-BR';
  var root = document.documentElement;

  function preferred() {
    try {
      var saved = localStorage.getItem(STORE);
      if (saved === EN || saved === PT) return saved;
    } catch (e) { /* private mode — fall through to navigator */ }
    return (navigator.language || EN).toLowerCase().indexOf('pt') === 0 ? PT : EN;
  }

  function label() {
    var btn = document.getElementById('lang-toggle');
    if (!btn) return;
    btn.setAttribute('aria-label',
      root.dataset.lang === EN ? 'Mudar para português' : 'Switch to English');
  }

  function apply(lang) {
    root.dataset.lang = lang;
    root.lang = lang;
    label();
  }

  apply(preferred());

  // the button does not exist yet at this point — set its label once it does
  document.addEventListener('DOMContentLoaded', label);

  document.addEventListener('click', function (ev) {
    if (!ev.target.closest || !ev.target.closest('#lang-toggle')) return;
    var next = root.dataset.lang === EN ? PT : EN;
    apply(next);
    try { localStorage.setItem(STORE, next); } catch (e) { /* ignore */ }
  });
})();

/* Tag filter for the blog index. Progressive enhancement: the buttons only
   exist inside a .filters element, and with JS off every post stays visible. */
(function () {
  'use strict';

  function init() {
    var filters = document.querySelector('.filters');
    var empty = document.getElementById('posts-empty');
    var items = document.querySelectorAll('.posts > li:not(.posts__empty)');
    if (!filters || !items.length) return;

    filters.hidden = false;

    filters.addEventListener('click', function (ev) {
      var btn = ev.target.closest('.filter');
      if (!btn) return;

      var tag = btn.dataset.filter;
      var i;

      for (i = 0; i < filters.children.length; i++) {
        filters.children[i].setAttribute('aria-pressed',
          filters.children[i] === btn ? 'true' : 'false');
      }

      var shown = 0;
      for (i = 0; i < items.length; i++) {
        var tags = (items[i].dataset.tags || '').split(' ');
        var hide = tag !== '*' && tags.indexOf(tag) === -1;
        items[i].hidden = hide;
        if (!hide) shown++;
      }

      if (empty) empty.hidden = shown > 0;
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
