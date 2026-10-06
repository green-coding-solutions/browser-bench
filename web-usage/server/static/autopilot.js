// The simulated user of the web-usage scenario.
//
// It runs the visits in window.BB_PLAN (static/plan.js) one after the other.
// Only the tab that was opened with ?session=1 takes part. That tab keeps its
// position in the plan in sessionStorage, which belongs to the tab, so pages
// opened in other tabs stay untouched.
//
// Every action uses the page like a person would: it types into fields one
// character at a time, scrolls in mouse wheel steps, clicks links and buttons
// and waits in between. The browser does all the loading, layout and painting
// itself. Nothing is skipped or faked.
//
// /mark/<name> tells the GMT scenario where a phase ends. /mark/error makes
// the run fail, so a browser that cannot do the session does not pass as idle.
//
// ?session=1&speed=10 runs the whole session ten times faster, to check the
// steps by eye. GMT runs always use the real speed of 1.
(() => {
  const KEY = 'bb-visit';
  const params = new URLSearchParams(location.search);
  if (params.has('session')) {
    sessionStorage.setItem(KEY, '0');
    sessionStorage.setItem('bb-speed', params.get('speed') || '1');
  }
  const speed = Math.max(0.1, parseFloat(sessionStorage.getItem('bb-speed') || '1') || 1);
  const stored = sessionStorage.getItem(KEY);
  const plan = window.BB_PLAN;
  if (stored === null || !plan) return;
  const index = parseInt(stored, 10);
  const visit = plan.visits[index];
  if (!visit) return;

  // Deterministic jitter, so every browser gets exactly the same session.
  let seed = 7919 * (index + 1);
  const rand = () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const between = (lo, hi) => lo + (hi - lo) * rand();
  // sleep is session time and runs faster in fast mode. realSleep is for
  // waiting on the page itself, which takes as long as it takes.
  const realSleep = (s) => new Promise((resolve) => setTimeout(resolve, s * 1000));
  const sleep = (s) => realSleep(s / speed);
  const mark = (name) => fetch(`/mark/${name}`, { cache: 'no-store' }).catch(() => {});
  const fail = async (msg) => {
    await mark(`error?visit=${index}&path=${encodeURIComponent(location.pathname)}&msg=${encodeURIComponent(msg)}`);
    throw new Error(msg);
  };
  const find = async (sel, nth = 0) => {
    for (let i = 0; i < 100; i++) {
      const el = document.querySelectorAll(sel)[nth];
      if (el) return el;
      await realSleep(0.1);
    }
    return fail(`element not found: ${sel} #${nth}`);
  };
  const advance = () => sessionStorage.setItem(KEY, String(index + 1));

  // One mouse wheel notch at a time. The browser animates each one itself.
  const wheel = async (px, seconds) => {
    const steps = Math.max(1, Math.round(Math.abs(px) / plan.wheelNotchPx));
    const dir = Math.sign(px);
    for (let i = 0; i < steps; i++) {
      window.scrollBy({ top: dir * plan.wheelNotchPx, behavior: 'smooth' });
      await sleep(seconds / steps);
    }
  };
  const bringIntoView = async (el) => {
    const r = el.getBoundingClientRect();
    if (r.top < 80 || r.bottom > innerHeight) await wheel(r.top - innerHeight / 3, 1.5);
  };

  const actions = {
    // Think time, reading time or simply looking at the page.
    wait: async (a) => sleep(a.s),
    mark: async (a) => mark(a.name),
    // Typing, one character at a time at the typing speed of the plan.
    type: async (a) => {
      const el = await find(a.sel);
      el.focus();
      for (const ch of a.text) {
        el.value += ch;
        el.dispatchEvent(new InputEvent('input', { bubbles: true, data: ch, inputType: 'insertText' }));
        await sleep(plan.secondsPerKeystroke * between(0.6, 1.4));
      }
    },
    // Enter in a form.
    submit: async (a) => { advance(); (await find(a.sel)).requestSubmit(); },
    // A click on a link that leads to the next visit.
    follow: async (a) => {
      const el = await find(a.sel, a.nth || 0);
      await bringIntoView(el);
      await sleep(0.6);
      advance();
      el.click();
    },
    // A click that stays on the page, a button or a list entry.
    click: async (a) => {
      const el = await find(a.sel, a.nth || 0);
      await bringIntoView(el);
      await sleep(0.4);
      el.click();
    },
    // Opening an address directly, as from a bookmark or the address bar.
    go: async (a) => { advance(); location.assign(a.path); },
    // Reading an article for a.s seconds at reading speed. The page scrolls
    // along with the text, as far as that many words reach on this layout.
    read: async (a) => {
      const el = await find(a.sel);
      const share = Math.min(1, ((a.s / 60) * plan.readingWordsPerMinute) / parseInt(el.dataset.words, 10));
      await wheel(el.getBoundingClientRect().height * share, a.s);
    },
    // Scrolling a given distance in a given time, for skimming.
    scroll: async (a) => wheel(a.px, a.s),
    // A feed: scroll one post on, look at it, scroll on, for a.s seconds.
    // A video post that is at least half on the screen for the first time is
    // watched for a.watch seconds before scrolling on.
    feed: async (a) => {
      const end = performance.now() + (a.s * 1000) / speed;
      const watched = new Set();
      const newVideo = () => [...document.querySelectorAll('#feed video')].find((v) => {
        const r = v.getBoundingClientRect();
        return !watched.has(v) && Math.min(r.bottom, innerHeight) - Math.max(r.top, 0) >= r.height / 2;
      });
      while (performance.now() < end) {
        await wheel(between(a.px[0], a.px[1]), 0.6);
        const v = newVideo();
        if (v) watched.add(v);
        const left = ((end - performance.now()) / 1000) * speed;
        await sleep(Math.max(0, Math.min(left, v ? a.watch : between(a.dwell[0], a.dwell[1]))));
      }
      // How many of the feed's videos really played, for the run's log.
      const played = [...document.querySelectorAll('#feed video')].filter((v) => v.played.length > 0);
      const frames = played.reduce((n, v) => n + (v.getVideoPlaybackQuality ? v.getVideoPlaybackQuality().totalVideoFrames : 0), 0);
      await mark(`stat?feed=1&videos=${played.length}&decoded=${frames}`);
    },
    // Watching the video for a.s seconds. Muted, because the container has no
    // sound device and muted playback starts without a click in every browser.
    watch: async (a) => {
      const v = await find(a.sel);
      v.muted = true;
      v.loop = true;
      try { await v.play(); } catch (e) { return fail(`video did not play: ${e.name}`); }
      const end = performance.now() + (a.s * 1000) / speed;
      let last = v.currentTime;
      let stalled = 0;
      while (performance.now() < end) {
        await realSleep(Math.min(5, a.s / speed));
        stalled = v.currentTime === last ? stalled + Math.min(5, a.s / speed) : 0;
        if (stalled >= 15) return fail('video stalled');
        last = v.currentTime;
      }
      const q = v.getVideoPlaybackQuality ? v.getVideoPlaybackQuality() : {};
      v.pause();
      await mark(`stat?video=1&decoded=${q.totalVideoFrames}&dropped=${q.droppedVideoFrames}&expected=${Math.round((a.s * 24) / speed)}`);
    },
    // Wait until a page script reports that it is ready.
    ready: async (a) => {
      for (let i = 0; i < 100 && document.body.dataset[a.flag] === undefined; i++) await realSleep(0.1);
      if (document.body.dataset[a.flag] === undefined) await fail(`page not ready: ${a.flag}`);
    },
  };

  const run = async () => {
    if (!location.pathname.startsWith(visit.path)) await fail(`expected ${visit.path}`);
    for (const a of visit.actions) {
      const act = actions[a.do];
      if (!act) await fail(`unknown action ${a.do}`);
      await act(a);
    }
    // In fast mode, say clearly that the session is over. A GMT run closes
    // the browser at this point, so it never shows there.
    if (index === plan.visits.length - 1 && speed !== 1) {
      const note = document.createElement('div');
      note.textContent = `browser-bench session finished at speed ${speed}. Every wait, and the time spent watching videos, was ${speed} times shorter than in a real run.`;
      note.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:99;padding:16px 24px;background:#1d2330;color:#fff;font:18px system-ui,sans-serif;text-align:center';
      document.body.appendChild(note);
    }
  };
  const start = () => run().catch((e) => console.error('browser-bench autopilot:', e));
  if (document.readyState === 'complete') start();
  else window.addEventListener('load', start, { once: true });
})();
