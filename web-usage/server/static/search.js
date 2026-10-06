// Search engine page behaviour: a suggestion request on every keystroke, as
// the large search engines do, and Enter leads to the results page.
(() => {
  const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const q = document.getElementById('q');
  const form = document.getElementById('search-form');
  const list = document.getElementById('suggestions');
  if (!q || !form) return;
  let seq = 0;
  q.addEventListener('input', async () => {
    const mine = ++seq;
    const prefix = q.value;
    if (!list || !prefix.trim()) return;
    try {
      const r = await fetch(`/search/suggest/${slug(prefix)}.json`);
      if (mine !== seq) return;
      const items = r.ok ? await r.json() : [];
      list.replaceChildren(...items.map((t) => Object.assign(document.createElement('li'), { textContent: t })));
    } catch (e) { /* no suggestions */ }
  });
  form.addEventListener('submit', (ev) => {
    ev.preventDefault();
    location.assign(`/search/${slug(q.value)}.html`);
  });
})();
