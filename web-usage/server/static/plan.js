// The session of the simulated user. web-usage/README.md derives every number
// here from the cited papers and marks the few that are assumptions.
//
// [Ruth22]      Ruth et al., A World Wide View of Browsing the World Wide Web, IMC 2022
// [Weinreich08] Weinreich et al., Not Quite the Average: An Empirical Study of Web Use, ACM TWEB 2008
// [Dhakal18]    Dhakal et al., Observations on Typing from 136 Million Keystrokes, CHI 2018
// [Brysbaert19] Brysbaert, How many words do we read per minute?, J. Memory and Language 2019
//
// The session is 600 s of activity. Video gets its desktop time share of
// 33.25 % [Ruth22], so 200 s. The other 400 s go to the page-based activities
// in proportion to their desktop shares [Ruth22]: search 84 s, reference and
// work reading 151 s, news 35 s, social 45 s, messaging 37 s, shopping 47 s.
const SERP = 8.0; // median stay on search result pages [Weinreich08]
const STAY = 9.4; // median stay on a page [Weinreich08]
const FIRST = 12.4; // median stay on a page visited for the first time [Weinreich08]
const LOOK = 2; // looking at a freshly opened page before acting (assumption)

// One search, about 17 s: look at the start page, type the query, press
// Enter, look at the results. Five of these fill the 84 s of search.
const search = (query) => [{ do: 'wait', s: LOOK }, { do: 'type', sel: '#q', text: query }, { do: 'wait', s: 0.5 }, { do: 'submit', sel: '#search-form' }];

window.BB_PLAN = {
  secondsPerKeystroke: 0.2387, // average inter-key interval 238.656 ms [Dhakal18]
  readingWordsPerMinute: 238, // silent reading of non-fiction [Brysbaert19]
  wheelNotchPx: 100, // one mouse wheel step (assumption)
  visits: [
    // startup ends when the start page is there. Then search 1 of 5.
    { path: '/start/', actions: [{ do: 'mark', name: 'ready' }, ...search('electric car range in winter')] },
    { path: '/search/', actions: [{ do: 'wait', s: SERP }, { do: 'mark', name: 'search-news' }, { do: 'follow', sel: '.result-link', nth: 0 }] },
    // News, 35 s: a short look, then reading.
    { path: '/news/', actions: [{ do: 'wait', s: 5 }, { do: 'read', sel: '#story', s: 30 }, { do: 'mark', name: 'news' }, { do: 'go', path: '/start/' }] },
    // Search 2 of 5, a look-up that is answered on the results page.
    { path: '/start/', actions: search('weather berlin tomorrow') },
    { path: '/search/', actions: [{ do: 'wait', s: SERP }, { do: 'mark', name: 'search-lookup-1' }, { do: 'go', path: '/start/' }] },
    // Search 3 of 5, then shopping, 47 s: the product list, one product with
    // its gallery and reviews, into the cart, the cart.
    { path: '/start/', actions: search('noise cancelling headphones') },
    { path: '/search/', actions: [{ do: 'wait', s: SERP }, { do: 'mark', name: 'search-shop' }, { do: 'follow', sel: '.result-link', nth: 0 }] },
    { path: '/shop/', actions: [{ do: 'wait', s: 3 }, { do: 'scroll', px: 900, s: 4 }, { do: 'wait', s: STAY - 7 }, { do: 'follow', sel: 'a.product-card', nth: 5 }] },
    { path: '/shop/p', actions: [{ do: 'wait', s: 3 }, { do: 'click', sel: '#gallery-next' }, { do: 'wait', s: 2.5 }, { do: 'click', sel: '#gallery-next' }, { do: 'wait', s: 2.5 }, { do: 'click', sel: '#gallery-next' }, { do: 'wait', s: FIRST - 8 }, { do: 'scroll', px: 1200, s: 4 }, { do: 'wait', s: 8 }, { do: 'click', sel: '#add-to-cart' }, { do: 'wait', s: 2 }, { do: 'follow', sel: '#go-to-cart' }] },
    { path: '/shop/cart', actions: [{ do: 'wait', s: STAY }, { do: 'mark', name: 'shop' }, { do: 'go', path: '/social/' }] },
    // Social, 45 s: scrolling the feed post by post. Every post is a video,
    // which is watched for its full 10 s (assumption).
    { path: '/social/', actions: [{ do: 'feed', s: 45, px: [500, 900], dwell: [2, 5], watch: 10 }, { do: 'mark', name: 'social' }, { do: 'go', path: '/mail/' }] },
    // Messaging, 37 s: read two mails, answer one.
    { path: '/mail/', actions: [{ do: 'ready', flag: 'ready' }, { do: 'wait', s: LOOK }, { do: 'click', sel: 'li.mail', nth: 0 }, { do: 'wait', s: 10 }, { do: 'click', sel: 'li.mail', nth: 1 }, { do: 'wait', s: STAY }, { do: 'click', sel: '#reply' }, { do: 'type', sel: '#body', text: 'Thanks, Tuesday at ten works for me. See you then.' }, { do: 'click', sel: '#send' }, { do: 'wait', s: LOOK }, { do: 'mark', name: 'mail' }, { do: 'go', path: '/start/' }] },
    // Search 4 of 5, another look-up.
    { path: '/start/', actions: search('euro to dollar') },
    { path: '/search/', actions: [{ do: 'wait', s: SERP }, { do: 'mark', name: 'search-lookup-2' }, { do: 'go', path: '/start/' }] },
    // Search 5 of 5, then reference reading, 151 s.
    { path: '/start/', actions: search('how to bake sourdough bread') },
    { path: '/search/', actions: [{ do: 'wait', s: SERP }, { do: 'mark', name: 'search-reference' }, { do: 'follow', sel: '.result-link', nth: 0 }] },
    { path: '/wiki/', actions: [{ do: 'wait', s: 6 }, { do: 'read', sel: '#story', s: 145 }, { do: 'mark', name: 'reference' }, { do: 'go', path: '/video/watch.html' }] },
    // Video, 200 s.
    { path: '/video/', actions: [{ do: 'wait', s: LOOK }, { do: 'watch', sel: '#player', s: 198 }, { do: 'mark', name: 'video' }, { do: 'mark', name: 'done' }] },
  ],
};
