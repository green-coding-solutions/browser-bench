// Webmail behaviour: the inbox is loaded as JSON, messages open in a reader
// pane, a reply can be written and sent, and the client polls for new mail
// every 30 s like common webmail clients, also when it sits in a background tab.
(() => {
  const inbox = document.getElementById('inbox');
  if (!inbox) return;
  const reader = document.getElementById('reader');
  const composer = document.getElementById('composer');
  const open = async (li) => {
    inbox.querySelectorAll('li.open').forEach((o) => o.classList.remove('open'));
    li.classList.add('open');
    const m = await (await fetch(`/mail/msg/${li.dataset.id}.json`)).json();
    composer.hidden = true;
    reader.hidden = false;
    reader.innerHTML = `<h2>${m.subject}</h2><p><b>${m.from}</b></p>${m.html}<button id="reply" type="button">Reply</button>`;
    document.getElementById('reply').addEventListener('click', () => {
      reader.hidden = true;
      composer.hidden = false;
      document.getElementById('body').focus();
    });
  };
  fetch('/mail/inbox.json').then((r) => r.json()).then((mails) => {
    inbox.replaceChildren(...mails.map((m) => {
      const li = document.createElement('li');
      li.className = 'mail';
      li.dataset.id = m.id;
      li.innerHTML = `<b>${m.from} <small>${m.time}</small></b>${m.subject}<br><span>${m.preview}</span>`;
      li.addEventListener('click', () => open(li));
      return li;
    }));
    document.body.dataset.ready = '1';
  });
  document.getElementById('send').addEventListener('click', async () => {
    const body = document.getElementById('body');
    await fetch(`/mail/send?len=${body.value.length}`, { cache: 'no-store' });
    body.value = '';
    composer.hidden = true;
    reader.hidden = false;
    reader.innerHTML = '<p class="empty">Message sent</p>';
  });
  setInterval(() => fetch('/mail/poll.json', { cache: 'no-store' }).catch(() => {}), 30000);
})();
