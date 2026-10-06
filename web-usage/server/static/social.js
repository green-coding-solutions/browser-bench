// Social feed behaviour: posts are rendered from JSON, and the next page of
// posts is fetched when the reader gets close to the end (infinite scroll).
// Video posts play muted and looped while at least half of them is on the
// screen and pause when they leave it, like the feeds of the large networks.
(() => {
  const feed = document.getElementById('feed');
  if (!feed) return;
  const autoplay = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (e.isIntersecting) e.target.play().catch(() => {});
      else e.target.pause();
    }
  }, { threshold: 0.5 });
  const render = (p) => {
    const el = document.createElement('article');
    el.className = 'post';
    const media = p.video
      ? `<video class="pic" src="${p.video}" muted loop playsinline preload="metadata" width="720" height="720"></video>`
      : (p.image ? `<img class="pic" src="${p.image}" width="1080" height="1080" loading="lazy" alt="">` : '');
    el.innerHTML = `<div class="who"><img src="${p.avatar}" width="48" height="48" alt="">${p.author}</div>
<p>${p.text}</p>${media}
<div class="bar"><span>♥ ${p.likes}</span><span>${p.comments} comments</span><button type="button" class="like">Like</button></div>`;
    feed.appendChild(el);
    const v = el.querySelector('video');
    if (v) { v.muted = true; autoplay.observe(v); }
  };
  JSON.parse(feed.dataset.first).forEach(render);
  let next = 1;
  let loading = false;
  const more = async () => {
    if (loading || next >= 20) return;
    loading = true;
    try {
      const r = await fetch(`/social/feed/${next}.json`);
      if (r.ok) { (await r.json()).forEach(render); next += 1; }
    } finally { loading = false; }
  };
  const sentinel = () => feed.lastElementChild;
  const io = new IntersectionObserver((entries) => { if (entries.some((e) => e.isIntersecting)) more(); }, { rootMargin: '1500px' });
  const watch = () => { io.disconnect(); if (sentinel()) io.observe(sentinel()); };
  new MutationObserver(watch).observe(feed, { childList: true });
  watch();
})();
