// browser-bench addition to Speedometer, not part of the benchmark itself.
// When Speedometer shows its results it switches the page to #summary. This
// reports the score to the server once, where wait-score answers the waiting
// run phase with it. It only listens for that switch, so it does nothing while
// the benchmark runs.
(() => {
  let sent = false;
  const report = () => {
    if (sent || location.hash !== '#summary') return;
    sent = true;
    const summary = document.getElementById('summary');
    const score = document.getElementById('result-number').textContent;
    fetch(`/bench/done?class=${encodeURIComponent(summary.className)}&score=${encodeURIComponent(score)}`, { cache: 'no-store' });
  };
  window.addEventListener('hashchange', report);
  report();
})();
