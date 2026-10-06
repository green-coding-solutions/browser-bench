# Web usage

A ten minute desktop browsing session, done by a simulated user in each browser. It is meant to measure a browser the way people use it, where Speedometer measures how fast it is. The session searches, reads news and reference pages, shops, scrolls a social feed, answers a mail and watches a video. How long each activity takes, and how fast the user types and reads, comes from published studies of real users. The sources are listed at the end.

All sites are emulated by the `web` container. The browser under test never talks to the internet, and every run gets exactly the same pages, images and video.

## Layout

```text
web-usage/
  usage_scenario_<browser>.yml   One GMT scenario per browser
  preview.sh                     Shows the session in your own browser, faster than real time
  server/
    Dockerfile                   Builds the web container
    build_site.py                Generates all sites from a fixed seed
    nginx.conf                   Serves them and logs the phase marks
    wait-mark                    Lets a GMT phase wait for the end of a part of the session
    serve-mark                   Answers a phase that waits on port 9000 for a mark, used by startup
    90-browser-bench.sh          Starts socat on port 9000 next to nginx
    static/plan.js               The session: what the user does and for how long
    static/autopilot.js          The simulated user that carries the session out
    static/*.js, site.css        Behaviour and style of the sites
```

## The sites

| Site | Emulates | What it does like the real thing |
| --- | --- | --- |
| Seekr, `/start/` and `/search/` | A search engine | One suggestion request per keystroke, a results page with a top stories row and a side panel |
| The Daily Ledger, `/news/` | A news site | Long articles with a hero image, inline images, related links and comments |
| OpenPedia, `/wiki/` | An encyclopedia or documentation | Long articles with a sticky table of contents, tables and images |
| Shopwell, `/shop/` | A web shop | A product grid, product pages with an image gallery and reviews, a cart in localStorage |
| Circle, `/social/` | A social network | A feed rendered from JSON that loads the next posts while you scroll. Every post is a video that plays muted while it is on the screen |
| Postbox, `/mail/` | A webmail | An inbox loaded as JSON, a reader pane, a reply editor, a poll for new mail every 30 s |
| ViewTube, `/video/` | A video site | A 1080p VP9 video with recommendations and comments |

`build_site.py` generates all texts, prices, names and mails from a fixed seed. ImageMagick renders the images as plasma fractals. They have photo-like detail, so they cost about as much to transfer and decode as photos of the same size. The videos are from Tears of Steel, (c) Blender Foundation, mango.blender.org, licensed CC BY 3.0. The build downloads 2:00 to 8:00 of the 1080p VP9 transcode on Wikimedia Commons in one request, about 125 MB. Commons answers several quick seeks with 429 Too Many Requests, so everything else is cut from that local copy.

- The video site plays 2:00 to 6:00 as it is: 1920x858 at 24 fps with Opus audio, about 2.8 Mbit/s.
- The feed gets twelve different 10 s clips from 6:00 to 8:00, cropped to the middle and encoded as 720x720 VP9 at 24 fps, the size feeds show video at.

VP9 is what YouTube serves to desktop browsers, and every browser of this repository decodes it.

Static files are cacheable for a day and pages are revalidated, as on most real sites. So a page that the session opens twice comes partly from the browser cache.

## How the session runs

`static/autopilot.js` is part of every page and carries out the visits of `static/plan.js` one after the other. Only the tab that was opened with `?session=1` takes part. It keeps its place in the plan in `sessionStorage`, which belongs to the tab, so the second tab stays untouched in the background.

The simulated user acts on the page the way a person would:

- It types into fields one character at a time.
- It scrolls in mouse wheel steps, which the browser animates.
- It clicks links and buttons, and it waits while reading or looking.

The browser does all loading, layout, painting and video decoding itself. It needs no WebDriver and no X input, so it works the same in all eleven browsers, including Falkon and Nyxt.

At the end of each part of the session the page requests `/mark/<phase>`. Each GMT phase of the session runs `wait-mark <phase>` in the `web` container and ends when that mark arrives. The phases therefore line up with what the browser actually does. If the simulated user hits a problem, for example a video that does not play, it requests `/mark/error`, and the run fails. A mark that does not arrive in time also fails the run. A browser that cannot do the session never passes as an idle browser.

The startup phase is different, because it starts the browser. Its command starts the browser in the background and then waits on port 9000 of the `web` container, where `socat` hands the connection to `serve-mark`. That answers once the start page has reported `/mark/ready`. So the phase begins before the browser exists and contains its whole start. A browser started in a phase of its own would spend GMT's pause between two phases starting up. That pause lasts for the sampling interval of the slowest metric provider, 999 ms on the cluster machines, and belongs to no phase. The browser writes its output into `/tmp/browser.log`, so it does not keep a phase open, and the close phase prints the end of that log.

## The session

| GMT phase | What the user does | Target | Chrome, development run |
| --- | --- | --- | --- |
| idle | The browser starts once without an address for 60 s, then it is killed. This takes first-run pages out of the session. | 60 s | |
| startup | The browser starts with the search start page and a news front page in a second tab | | |
| search-news | Types "electric car range in winter", looks at the results for 8 s, opens the first one | about 17 s | 17.0 s |
| news | Looks at the article for 5 s, then reads for 30 s while scrolling along | 35 s | 35.7 s |
| search-lookup-1 | Types "weather berlin tomorrow", reads the answer on the results page for 8 s | about 16 s | 16.5 s |
| search-shop | Types "noise cancelling headphones", looks at the results for 8 s, opens the shop | about 17 s | 17.0 s |
| shop | Looks over the product list (9.4 s), opens a product, flips through its pictures, reads reviews, adds it to the cart, looks at the cart (9.4 s) | 47 s | 51.7 s |
| social | Scrolls the feed post by post and looks at each one for 2 to 5 s. Every post is a video, which is watched for its full 10 s. | 45 s | 47.5 s |
| mail | Reads two mails, writes a two-sentence reply and sends it | 37 s | 38.5 s |
| search-lookup-2 | Types "euro to dollar", reads the answer for 8 s | about 14 s | 14.2 s |
| search-reference | Types "how to bake sourdough bread", looks at the results for 8 s, opens the encyclopedia article | about 17 s | 16.5 s |
| reference | Looks at the article for 6 s, then reads for 145 s while scrolling along | 151 s | 151.7 s |
| video | Watches the video for 200 s | 200 s | 202.1 s |
| close | The browser is closed with SIGTERM, leftovers are killed after 10 s | | |

The session is 600 s of activity. The last column is a development run of Chrome 154 on a private Xvfb, the run the plan was tuned with. It includes page loads, so other browsers take a little more or less time, and that difference is part of what is measured. The video played without a single dropped frame in that run.

## Where the numbers come from

**The mix of activities.** Ruth et al. measured where desktop users spend their time, from Chrome telemetry of several hundred million users [1]. Their Figure 2 gives the share of time on the top 10,000 sites for Windows.

| Category in [1] | Share of time | Used for |
| --- | --- | --- |
| Video Streaming | 33.25 % | video |
| Search Engines | 9.15 % | search |
| Technology | 7.90 % | reference |
| Business | 4.41 % | reference |
| Education | 4.15 % | reference |
| News & Media | 3.80 % | news |

Social networks and chat are not shown separately for the top 10,000 sites. For them the session uses the time shares of the top 100 sites from the same figure, 4.93 % for Social Networks and 4.01 % for Chat and Messaging. The paper gives no time share for e-commerce at all. The session uses its share of page loads on the top 10,000 sites, 5.12 %, instead. These two substitutions are the weakest part of the mix.

Video gets its share directly, 33.25 % of 600 s, which is 200 s. The remaining 400 s are split in proportion to the other shares, whose sum is 43.47 %.

| Activity | Share | Seconds |
| --- | --- | --- |
| Search | 9.15 % | 84 |
| Reference (technology, business, education) | 16.46 % | 151 |
| News | 3.80 % | 35 |
| Social | 4.93 % | 45 |
| Messaging | 4.01 % | 37 |
| Shopping | 5.12 % | 47 |

Not part of the session are Movies and Home Video (5.33 %), Gaming (4.91 %), Television (3.88 %), Economy & Finance (3.44 %) and Other (19.78 %). They need logins, games or DRM video that cannot be emulated in a meaningful way. Movies and television are also video playback, so the video share is on the low side.

**Pacing.**

- Typing: one character every 238.7 ms on average, the average inter-key interval of 136 million keystrokes [3]. Each keystroke varies between 60 % and 140 % of that, the same way in every run.
- Reading: 238 words per minute, the average silent reading rate of adults for non-fiction [4]. The page scrolls along as far as that many words reach on the screen.
- Search results: 8.0 s, the median stay on Google result pages [2].
- Other pages: 9.4 s, the median stay on any page, and 12.4 s for a page visited for the first time [2].
- Tabs: two, because users had on average 2.1 windows or tabs open when they opened a page [2].
- Searches: 84 s at about 17 s per search make five searches. Three lead to a page and two are look-ups whose answer is on the results page.

**Checks against other studies.** The session opens about 17 pages in 400 s of browsing besides the video, one every 24 s. Kumar and Tomkins report a median gap of 12 s between page views [5], and Crichton et al. report 154 pages per day in 1.7 hours of browsing, one every 40 s [6]. The session sits between the two.

## Assumptions

These values are not from the papers.

- The session length of 600 s. It keeps a run with install, first start and session under 15 minutes. For comparison, Kumar and Tomkins report a median session of 16 minutes with 17 page views [5].
- 2 s of looking at a page before acting on it, 5 s before reading an article and 6 s before reading a reference article.
- One mouse wheel step is 100 px.
- The social feed: scrolling 500 to 900 px at a time and looking 2 to 5 s at each post.
- Every post of the feed is a 10 s video, and each one is watched for its full 10 s when it is half on the screen for the first time. In the 45 s of the feed that is about four videos.
- The mail part: 10 s for the first mail, 9.4 s for the second, then a reply of 52 characters.
- The shop part: three clicks through the pictures 2.5 s apart and 8 s of reading reviews.
- The queries, the texts and which result is opened.
- The news front page as the background tab.
- The video plays muted. The container has no sound device, and muted playback starts without a click in every browser.

## What the session does not do

- **Input is synthetic.** Keystrokes, wheel steps and clicks are dispatched by the page script, not by the operating system. The browser's own input handling is not part of the measurement.
- **No tab switching.** Crichton et al. found that switching tabs makes up 54.4 % of navigation [6], but a page cannot switch tabs. The session opens social, mail and video directly in the same tab instead.
- **The pages are light.** Real sites load advertising, trackers and large JavaScript frameworks. The emulated sites have the layout, images and page behaviour, but not that weight.
- **No HTTPS.** The sites are served over plain HTTP, so TLS is not measured. A certificate the browsers trust would have to be installed into eleven different trust stores.
- **Progressive video.** The video is one WebM file, while YouTube streams adaptively in small segments.

## Running it

Locally, like the Speedometer scenarios, with `--allow-unsafe` because of the X socket and the run arguments of Edge and Firefox:

```bash
cd ~/code/green-metrics-tool
venv/bin/python runner.py \
  --uri ~/code/browser-bench \
  --filename web-usage/usage_scenario_chrome.yml \
  --name "Web usage Chrome" \
  --dev-no-sleeps --dev-cache-build --skip-download-dependencies --skip-optimizations \
  --allow-unsafe
```

The display requirements are the same as for the Speedometer scenarios, see the main README. The screen must also stay unlocked and switched on for the whole run. On a locked Wayland desktop the compositor stops giving the browser frames. Scrolling and video then stall and the run fails at the next mark.

On the cluster, submit it like the Speedometer scenarios with `--filename web-usage/usage_scenario_<browser>.yml`. A run takes about 15 minutes. Building the `web` container downloads about 125 MB of video from Wikimedia Commons.

## Watching the session faster

`preview.sh` builds the `web` container, serves it on `http://localhost:8088` and opens the session in your default browser. The marks are printed as they arrive, and Ctrl+C stops the container.

```bash
web-usage/preview.sh 10
```

The number is the speed. Every wait, keystroke, scroll step and the time spent watching videos are divided by it, so at 10 the session takes about a minute. Waiting for pages to load stays in real time. The address that starts it is `/start/?session=1&speed=10`, which works in any browser that can reach the container. GMT runs never set a speed and always run in real time.

## References

1. Kimberly Ruth, Aurore Fass, Jonathan Azose, Mark Pearson, Emma Thomas, Caitlin Sadowski, Zakir Durumeric. A World Wide View of Browsing the World Wide Web. ACM Internet Measurement Conference (IMC) 2022. https://doi.org/10.1145/3517745.3561418. Figure 2, p. 6, and Section 4, pp. 4-5.
2. Harald Weinreich, Hartmut Obendorf, Eelco Herder, Matthias Mayer. Not Quite the Average: An Empirical Study of Web Use. ACM Transactions on the Web 2(1), 2008. https://doi.org/10.1145/1326561.1326566. Stay times p. 15 and 16, windows and tabs p. 13.
3. Vivek Dhakal, Anna Maria Feit, Per Ola Kristensson, Antti Oulasvirta. Observations on Typing from 136 Million Keystrokes. ACM CHI 2018. https://doi.org/10.1145/3173574.3174220. Inter-key interval p. 5.
4. Marc Brysbaert. How many words do we read per minute? A review and meta-analysis of reading rate. Journal of Memory and Language 109, 2019. https://doi.org/10.1016/j.jml.2019.104047. Abstract.
5. Ravi Kumar, Andrew Tomkins. A Characterization of Online Browsing Behavior. WWW 2010. https://doi.org/10.1145/1772690.1772748. Sessions and page view gaps p. 563.
6. Kyle Crichton, Nicolas Christin, Lorrie Faith Cranor. How Do Home Computer Users Browse the Web? ACM Transactions on the Web 16(1), 2022. https://doi.org/10.1145/3473343. Table 3 p. 3:9, Table 5 p. 3:12, tab switching p. 3:8.
