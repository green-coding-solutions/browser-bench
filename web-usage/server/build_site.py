#!/usr/bin/env python3
"""Generate the emulated web sites for the web-usage scenario.

Everything is derived from a fixed seed, so every build produces the same
pages, texts and images. Nothing on these pages loads from outside the
container. The sites are deliberately ordinary: a search engine, a news site,
an encyclopedia, a shop, a social feed, a webmail and a video site, each with
the kind of layout, images and page scripts such sites have.

usage: build_site.py <output folder>
"""
import json
import random
import re
import subprocess
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
STATIC = Path(__file__).parent / 'static'
RNG = random.Random(20261006)

WORDS = """the of and to in is that for it as was with be by on not he this are or his from at
which but have an they you were her she there their one all we can has more when will would also
who been if no out so what up its about into than them only other new some could time these two may
first then do any like my now over such our man me even most made after many must before years
through back much where your way well down should because each just those people how too little
state good very make world still own see men work long get here between both life being under never
day same another know while last might us great old year off come since against go came right used
take three states himself few house use during without again place around however home small found
mrs thought went say part once general high upon school every does got united left number course war
until always away something fact though water less public put think almost hand enough far took head
yet government system better set told nothing night end why called didnt eyes find going look asked
later knew city light energy battery market price winter morning river forest garden kitchen bread
music village station letter window company family weather report research science history travel
mountain coast island bridge museum library council project budget engine signal network screen
""".split()

TOPICS = {
    'cars': ['electric', 'battery', 'range', 'charging', 'winter', 'motor', 'road', 'tyres', 'heat pump'],
    'bread': ['sourdough', 'starter', 'flour', 'dough', 'oven', 'crust', 'proof', 'yeast', 'water'],
    'sound': ['headphones', 'noise', 'cancelling', 'battery', 'bass', 'comfort', 'bluetooth', 'case'],
    'city': ['council', 'bridge', 'tram', 'budget', 'housing', 'river', 'museum', 'station', 'park'],
    'space': ['probe', 'orbit', 'moon', 'launch', 'telescope', 'signal', 'crew', 'rocket', 'mission'],
    'trains': ['timetable', 'station', 'delay', 'night train', 'ticket', 'route', 'platform', 'border'],
}

FIRST = ['Anna', 'Ben', 'Clara', 'David', 'Elif', 'Felix', 'Greta', 'Hugo', 'Ines', 'Jonas', 'Kim',
         'Lena', 'Malik', 'Nora', 'Omar', 'Paula', 'Quentin', 'Rosa', 'Sami', 'Tara', 'Uwe', 'Vera']
LAST = ['Becker', 'Costa', 'Dubois', 'Engel', 'Fischer', 'Garcia', 'Hansen', 'Ivanova', 'Jung',
        'Klein', 'Lopez', 'Meyer', 'Novak', 'Olsen', 'Peters', 'Richter', 'Schulz', 'Weber']


def sentence(topic=None, lo=8, hi=20):
    n = RNG.randint(lo, hi)
    words = [RNG.choice(WORDS) for _ in range(n)]
    if topic:
        for _ in range(RNG.randint(1, 3)):
            words[RNG.randrange(n)] = RNG.choice(TOPICS[topic])
    if n > 10 and RNG.random() < 0.4:
        words[RNG.randrange(3, n - 3)] += ','
    return ' '.join(words).capitalize() + '.'


def paragraph(topic=None, lo=3, hi=6):
    return ' '.join(sentence(topic) for _ in range(RNG.randint(lo, hi)))


def title(topic, lo=5, hi=9):
    words = [RNG.choice(WORDS) for _ in range(RNG.randint(lo, hi))]
    words[RNG.randrange(len(words))] = RNG.choice(TOPICS[topic])
    return ' '.join(words).capitalize()


def person():
    return f'{RNG.choice(FIRST)} {RNG.choice(LAST)}'


def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def count_words(html):
    return len(re.sub(r'<[^>]+>', ' ', html).split())


# Images ---------------------------------------------------------------------
IMAGES = []


def image(path, w, h, quality=80):
    """Register a JPEG to render. Plasma fractals have photo-like detail, so
    they cost about as much to transfer and decode as a photo of that size."""
    IMAGES.append((path, w, h, len(IMAGES) + 1, quality))
    return '/' + path


def render_images():
    jobs = []
    for path, w, h, seed, quality in IMAGES:
        target = OUT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        jobs.append(['magick', '-seed', str(seed), '-size', f'{w}x{h}', 'plasma:fractal',
                     '-blur', '0x1', '-quality', str(quality), '-strip', str(target)])
    procs = []
    for cmd in jobs:
        procs.append(subprocess.Popen(cmd))
        if len(procs) >= 8:
            for p in procs:
                if p.wait():
                    raise SystemExit('magick failed')
            procs = []
    for p in procs:
        if p.wait():
            raise SystemExit('magick failed')


# Page skeleton --------------------------------------------------------------
def page(site, page_title, body, scripts=(), body_class=''):
    tags = ''.join(f'<script src="{s}" defer></script>' for s in scripts)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title}</title>
<link rel="stylesheet" href="/static/site.css">
<script src="/static/plan.js"></script>
<script src="/static/autopilot.js" defer></script>{tags}
</head>
<body class="site-{site} {body_class}">
{body}
</body>
</html>
'''


def write(path, text):
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


def header(site, name, links):
    nav = ''.join(f'<a href="{href}">{label}</a>' for label, href in links)
    return f'<header class="top"><a class="logo" href="/{site}/">{name}</a><nav>{nav}</nav></header>'


FOOTER = '<footer class="bottom"><p>Emulated site for the browser-bench web usage scenario. All content is generated.</p></footer>'

# Content model ----------------------------------------------------------------
NEWS = []      # (path, title, topic)
WIKI = []
PRODUCTS = []  # (path, name)
VIDEOS = []


def build_news():
    nav = [('World', '/news/'), ('Science', '/news/'), ('Cities', '/news/'), ('Sport', '/news/')]
    topics = ['cars', 'city', 'space', 'trains', 'cars', 'city', 'space', 'trains', 'bread', 'sound']
    for i, topic in enumerate(topics, 1):
        NEWS.append((f'news/a{i}.html', title(topic), topic))
    for i, (path, t, topic) in enumerate(NEWS, 1):
        hero = image(f'news/img/a{i}-hero.jpg', 1600, 900)
        parts = []
        for j in range(14):
            parts.append(f'<p>{paragraph(topic)}</p>')
            if j in (3, 7, 11):
                parts.append(f'<figure><img src="{image(f"news/img/a{i}-{j}.jpg", 1200, 675)}" loading="lazy" width="1200" height="675" alt=""><figcaption>{sentence(topic, 6, 12)}</figcaption></figure>')
            if j in (5, 10):
                parts.append(f'<h2>{title(topic, 3, 6)}</h2>')
        story = ''.join(parts)
        related = [n for n in NEWS if n[0] != path][:3] if i > 1 else NEWS[1:4]
        rel = ''.join(f'<li><a class="related" href="/{p}"><img src="{image(f"news/img/a{i}-rel{k}.jpg", 320, 180)}" loading="lazy" width="320" height="180" alt="">{rt}</a></li>'
                      for k, (p, rt, _) in enumerate(related))
        comments = ''.join(f'<li><b>{person()}</b><p>{sentence(topic, 6, 30)}</p></li>' for _ in range(20))
        body = f'''{header("news", "The Daily Ledger", nav)}
<main class="news-article">
<article id="story" data-words="{count_words(story)}">
<h1>{t}</h1>
<p class="byline">By {person()} and {person()}</p>
<img class="hero" src="{hero}" width="1600" height="900" alt="">
<p class="lead">{paragraph(topic, 2, 3)}</p>
{story}
</article>
<aside><h3>Related</h3><ul class="related-list">{rel}</ul></aside>
<section class="comments"><h3>Comments</h3><ol>{comments}</ol></section>
</main>{FOOTER}'''
        write(path, page('news', t, body))
    cards = ''.join(f'<a class="card" href="/{p}"><img src="{image(f"news/img/front{k}.jpg", 480, 270)}" width="480" height="270" alt=""><span>{t}</span></a>'
                    for k, (p, t, _) in enumerate(NEWS))
    write('news/index.html', page('news', 'The Daily Ledger', f'{header("news", "The Daily Ledger", nav)}<main class="front">{cards}</main>{FOOTER}'))


def build_wiki():
    pages = [('sourdough-bread', 'Sourdough bread', 'bread'), ('electric-car-battery', 'Electric car battery', 'cars'),
             ('night-train', 'Night train', 'trains'), ('space-probe', 'Space probe', 'space')]
    for name, t, topic in pages:
        WIKI.append((f'wiki/{name}.html', t, topic))
    for name, t, topic in pages:
        sections = []
        toc = []
        for s in range(8):
            h = title(topic, 2, 4)
            toc.append(f'<li><a href="#s{s}">{h}</a></li>')
            paras = ''.join(f'<p>{paragraph(topic, 4, 7)}</p>' for _ in range(3))
            extra = ''
            if s == 2:
                rows = ''.join(f'<tr><td>{RNG.choice(TOPICS[topic])}</td><td>{RNG.randint(10, 999)}</td><td>{RNG.randint(1950, 2026)}</td></tr>' for _ in range(8))
                extra = f'<table><tr><th>Item</th><th>Value</th><th>Year</th></tr>{rows}</table>'
            if s in (1, 5):
                extra = f'<figure class="thumb"><img src="{image(f"wiki/img/{name}-{s}.jpg", 640, 480)}" loading="lazy" width="640" height="480" alt=""><figcaption>{sentence(topic, 5, 10)}</figcaption></figure>'
            sections.append(f'<h2 id="s{s}">{h}</h2>{extra}{paras}')
        content = ''.join(sections)
        body = f'''{header("wiki", "OpenPedia", [("Main page", "/wiki/"), ("Random", "/wiki/night-train.html")])}
<main class="wiki"><nav class="toc"><h3>Contents</h3><ol>{"".join(toc)}</ol></nav>
<article id="story" data-words="{count_words(content)}"><h1>{t}</h1><p class="lead">{paragraph(topic, 2, 3)}</p>{content}</article></main>{FOOTER}'''
        write(f'wiki/{name}.html', page('wiki', f'{t} - OpenPedia', body))
    items = ''.join(f'<li><a href="/{p}">{t}</a></li>' for p, t, _ in WIKI)
    write('wiki/index.html', page('wiki', 'OpenPedia', f'{header("wiki", "OpenPedia", [])}<main class="wiki"><ul>{items}</ul></main>{FOOTER}'))


def build_shop():
    nav = [('Audio', '/shop/'), ('Home', '/shop/'), ('Outdoor', '/shop/'), ('Cart', '/shop/cart.html')]
    for i in range(1, 25):
        name = f'{RNG.choice(["Aria", "Bolt", "Cove", "Dune", "Echo", "Fjord", "Gale", "Halo"])} {RNG.choice(["Pro", "Air", "Max", "Lite", "One", "Go"])} {RNG.choice(["Headphones", "Earbuds", "Speaker", "Headset"])}'
        PRODUCTS.append((f'shop/p{i}.html', name))
    for i, (path, name) in enumerate(PRODUCTS, 1):
        gallery = [image(f'shop/img/p{i}-{g}.jpg', 1000, 1000) for g in range(5)]
        reviews = ''.join(f'<li><b>{person()}</b> <span class="stars">{"★" * RNG.randint(2, 5)}</span><p>{paragraph("sound", 1, 3)}</p></li>' for _ in range(15))
        recs = ''.join(f'<a class="rec" href="/{p}"><img src="/shop/img/list{k}.jpg" width="200" height="200" loading="lazy" alt="">{n}</a>'
                       for k, (p, n) in enumerate(PRODUCTS[:8]))
        body = f'''{header("shop", "Shopwell", nav)}
<main class="product" data-gallery='{json.dumps(gallery)}'>
<section class="gallery"><img id="gallery-image" src="{gallery[0]}" width="1000" height="1000" alt="">
<button id="gallery-prev" type="button">‹</button><button id="gallery-next" type="button">›</button></section>
<section class="buy"><h1>{name}</h1><p class="price">{RNG.randint(29, 349)},{RNG.choice(["00", "49", "99"])} €</p>
<p>{paragraph("sound", 2, 4)}</p><button id="add-to-cart" type="button">Add to cart</button> <a id="go-to-cart" href="/shop/cart.html">Go to cart (<span id="cart-count">0</span>)</a>
<ul class="specs">{"".join(f"<li>{sentence('sound', 4, 8)}</li>" for _ in range(6))}</ul></section>
<section class="reviews"><h2>Reviews</h2><ol>{reviews}</ol></section>
<section class="recs"><h2>Customers also bought</h2>{recs}</section>
</main>{FOOTER}'''
        write(path, page('shop', f'{name} - Shopwell', body, ['/static/shop.js']))
    grid = ''.join(f'<a class="product-card" href="/{p}"><img src="{image(f"shop/img/list{k}.jpg", 400, 400)}" width="400" height="400" loading="lazy" alt=""><span>{n}</span><b>{RNG.randint(29, 349)} €</b></a>'
                   for k, (p, n) in enumerate(PRODUCTS))
    write('shop/index.html', page('shop', 'Shopwell - Audio', f'{header("shop", "Shopwell", nav)}<main class="grid">{grid}</main>{FOOTER}', ['/static/shop.js']))
    write('shop/cart.html', page('shop', 'Cart - Shopwell', f'{header("shop", "Shopwell", nav)}<main class="cart"><h1>Your cart</h1><ul id="cart-items"></ul><button type="button">Checkout</button></main>{FOOTER}', ['/static/shop.js']))


def build_social():
    def post(n):
        # Every post is a 10 s video, one of the twelve different clips the
        # Dockerfile cuts.
        return {
            'id': n, 'author': person(), 'avatar': image(f'social/img/avatar{n % 40}.jpg', 96, 96) if n < 40 else f'/social/img/avatar{n % 40}.jpg',
            'text': ' '.join(sentence(RNG.choice(list(TOPICS)), 6, 18) for _ in range(RNG.randint(1, 3))),
            'image': None,
            'video': f'/social/media/clip{n % 12}.webm',
            'likes': RNG.randint(0, 900), 'comments': RNG.randint(0, 80),
        }
    posts = [post(n) for n in range(200)]
    first = posts[:10]
    for k in range(1, 20):
        write(f'social/feed/{k}.json', json.dumps(posts[k * 10:(k + 1) * 10]))
    body = f'''{header("social", "Circle", [("Home", "/social/"), ("Friends", "/social/"), ("Messages", "/social/")])}
<main class="feed" id="feed" data-first='{json.dumps(first)}'></main>{FOOTER}'''
    write('social/index.html', page('social', 'Circle', body, ['/static/social.js']))


def build_mail():
    mails = []
    for n in range(40):
        topic = RNG.choice(list(TOPICS))
        mails.append({'id': n, 'from': person(), 'subject': title(topic, 3, 7), 'preview': sentence(topic, 6, 12), 'time': f'{RNG.randint(7, 19):02d}:{RNG.randint(0, 59):02d}'})
        msg = {'id': n, 'from': mails[-1]['from'], 'subject': mails[-1]['subject'],
               'html': ''.join(f'<p>{paragraph(topic, 1, 4)}</p>' for _ in range(RNG.randint(2, 5)))}
        if n % 4 == 0:
            msg['html'] += f'<img src="{image(f"mail/img/m{n}.jpg", 800, 500)}" width="800" height="500" alt="">'
        write(f'mail/msg/{n}.json', json.dumps(msg))
    write('mail/inbox.json', json.dumps(mails))
    write('mail/poll.json', json.dumps({'new': 0}))
    body = f'''{header("mail", "Postbox", [("Inbox", "/mail/"), ("Sent", "/mail/"), ("Drafts", "/mail/")])}
<main class="mail"><ul id="inbox"></ul><section id="reader"><p class="empty">Select a message</p></section>
<section id="composer" hidden><textarea id="body" rows="10" cols="60"></textarea><button id="send" type="button">Send</button></section></main>{FOOTER}'''
    write('mail/index.html', page('mail', 'Inbox - Postbox', body, ['/static/mail.js']))


def build_video():
    recs = ''.join(f'<a class="rec" href="/video/watch.html"><img src="{image(f"video/img/rec{k}.jpg", 320, 180)}" width="320" height="180" alt=""><span>{title(RNG.choice(list(TOPICS)), 4, 8)}</span></a>' for k in range(12))
    comments = ''.join(f'<li><b>{person()}</b><p>{sentence(None, 5, 25)}</p></li>' for _ in range(30))
    body = f'''{header("video", "ViewTube", [("Home", "/video/watch.html"), ("Subscriptions", "/video/watch.html")])}
<main class="watch"><section class="player">
<video id="player" src="/video/media/clip.webm" preload="auto" controls playsinline width="1280" height="720"></video>
<h1>Tears of Steel</h1>
<p class="credit">Tears of Steel, (c) Blender Foundation, mango.blender.org, CC BY 3.0. Cut and served locally.</p>
<p>{paragraph(None, 2, 3)}</p>
<section class="comments"><h3>Comments</h3><ol>{comments}</ol></section></section>
<aside class="recs">{recs}</aside></main>{FOOTER}'''
    write('video/watch.html', page('video', 'Tears of Steel - ViewTube', body))


# Search engine ----------------------------------------------------------------
QUERIES = {}   # query -> results page path


def build_search():
    targets = {
        'electric car range in winter': (NEWS[0], 'news'),
        'noise cancelling headphones': (('shop/index.html', 'Headphones and earbuds - Shopwell', 'sound'), 'shop'),
        'how to bake sourdough bread': (WIKI[0], 'wiki'),
    }
    # Look-ups whose answer is on the results page itself, without a click.
    answers = {
        'weather berlin tomorrow': ('city', '<b>Berlin, tomorrow</b><p class="big">14 °C, light rain</p><p>Wind 12 km/h, humidity 81 %, sunset 18:41</p>'),
        'euro to dollar': ('city', '<b>1 Euro equals</b><p class="big">1.09 US Dollar</p><p>Rate of 6 Oct 2026, 09:00 UTC</p>'),
    }
    for q, (topic, html) in answers.items():
        targets[q] = ((None, None, topic), 'answer')
    others = [(p, t, tp) for p, t, tp in NEWS[1:] + WIKI[1:]]
    for q, ((tpath, ttitle, topic), kind) in targets.items():
        s = slug(q)
        QUERIES[q] = f'search/{s}.html'
        results = []
        filler = RNG.sample(others, 9)
        entries = ([(tpath, ttitle)] if tpath else []) + [(p, t) for p, t, _ in filler]
        if kind == 'answer':
            results.append(f'<li class="answer">{answers[q][1]}</li>')
        for rank, (p, t) in enumerate(entries):
            results.append(f'<li class="result"><a class="result-link" href="/{p}">{t}</a><cite>web/{p}</cite><p>{sentence(topic, 15, 28)}</p></li>')
            if rank == 1:
                cards = ''.join(f'<a class="story-card" href="/{n[0]}"><img src="{image(f"search/img/{s}-c{c}.jpg", 240, 135)}" width="240" height="135" alt="">{n[1]}</a>' for c, n in enumerate(NEWS[2:5]))
                results.append(f'<li class="stories"><h3>Top stories</h3><div class="cards">{cards}</div></li>')
        panel = f'<aside class="panel"><img src="{image(f"search/img/{s}-panel.jpg", 400, 300)}" width="400" height="300" alt=""><h2>{q.capitalize()}</h2><p>{paragraph(topic, 2, 3)}</p></aside>'
        body = f'''<header class="top search"><a class="logo" href="/start/">Seekr</a>
<form id="search-form" action="/search/" role="search"><input id="q" name="q" value="{q}" autocomplete="off"></form></header>
<main class="serp"><p class="stats">About {RNG.randint(1, 900)},{RNG.randint(100, 999)},000 results</p><ol class="results">{"".join(results)}</ol>{panel}</main>{FOOTER}'''
        write(f'search/{s}.html', page('search', f'{q} - Seekr', body, ['/static/search.js']))
        for n in range(1, len(q) + 1):
            prefix = q[:n]
            if prefix.endswith(' '):
                continue
            sugg = [q] + [f'{prefix}{w}' for w in RNG.sample(['s', ' 2026', ' test', ' price', ' review', ' near me', ' tips'], 4)]
            write(f'search/suggest/{slug(prefix)}.json', json.dumps(sugg))
    tiles = ''.join(f'<a class="tile" href="/{p}"><img src="{image(f"start/img/t{k}.jpg", 320, 180)}" width="320" height="180" alt="">{t}</a>' for k, (p, t, _) in enumerate(NEWS[4:10]))
    body = f'''<main class="start"><h1 class="logo big">Seekr</h1>
<form id="search-form" action="/search/" role="search"><input id="q" name="q" autocomplete="off" placeholder="Search the web"><ul id="suggestions"></ul></form>
<section class="trending"><h3>Trending</h3><div class="tiles">{tiles}</div></section></main>{FOOTER}'''
    write('start/index.html', page('search', 'Seekr', body, ['/static/search.js']))
    write('search/index.json', json.dumps({slug(q): '/' + p for q, p in QUERIES.items()}))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    build_news()
    build_wiki()
    build_shop()
    build_social()
    build_mail()
    build_video()
    build_search()
    render_images()
    manifest = {'queries': {q: '/' + p for q, p in QUERIES.items()}, 'news': ['/' + n[0] for n in NEWS],
                'wiki': ['/' + w[0] for w in WIKI], 'products': ['/' + p[0] for p in PRODUCTS], 'images': len(IMAGES)}
    write('manifest.json', json.dumps(manifest, indent=1))
    print(json.dumps(manifest)[:400])


if __name__ == '__main__':
    main()
