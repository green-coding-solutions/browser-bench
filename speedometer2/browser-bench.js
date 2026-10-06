// browser-bench addition to Speedometer 2.1, not part of the benchmark itself.
// Speedometer calls benchmarkClient.didFinishLastIteration when it is done and
// shows its score there. This wraps that call and reports the score once to
// the server, where wait-score answers the waiting run phase with it. It does
// nothing while the benchmark runs.
(() => {
  const client = window.benchmarkClient;
  const finish = client.didFinishLastIteration;
  client.didFinishLastIteration = function (...args) {
    const result = finish.apply(this, args);
    const score = document.getElementById('result-number').textContent;
    fetch(`/bench/done?score=${encodeURIComponent(score)}`, { cache: 'no-store' });
    return result;
  };
})();
