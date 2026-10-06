// Shop behaviour: product image gallery and a cart kept in localStorage.
(() => {
  const read = () => { try { return JSON.parse(localStorage.getItem('cart') || '[]'); } catch (e) { return []; } };
  const save = (c) => { try { localStorage.setItem('cart', JSON.stringify(c)); } catch (e) { /* ignore */ } };
  const count = document.getElementById('cart-count');
  if (count) count.textContent = read().length;

  const main = document.querySelector('main.product');
  if (main) {
    const pics = JSON.parse(main.dataset.gallery);
    const img = document.getElementById('gallery-image');
    let i = 0;
    const show = (d) => { i = (i + d + pics.length) % pics.length; img.src = pics[i]; };
    document.getElementById('gallery-next').addEventListener('click', () => show(1));
    document.getElementById('gallery-prev').addEventListener('click', () => show(-1));
    document.getElementById('add-to-cart').addEventListener('click', () => {
      const c = read(); c.push(document.querySelector('h1').textContent); save(c);
      count.textContent = c.length;
    });
  }
  const items = document.getElementById('cart-items');
  if (items) items.replaceChildren(...read().map((t) => Object.assign(document.createElement('li'), { textContent: t })));
})();
