# browser-bench

Browser benchmarks for the [Green Metrics Tool](https://github.com/green-coding-solutions/green-metrics-tool) (GMT).

There are three benchmarks, each with one scenario per browser.

- **`speedometer2/`** measures how fast a browser is, with Speedometer 2.1. Each scenario installs one browser in a fresh Ubuntu 26.04 container and starts it once without a URL for 60 s. It then starts it again on Speedometer 2.1 until the benchmark has finished and finally uninstalls it. Every step is a GMT phase, so idle and benchmark energy are reported separately, and the score is stored as the GMT custom metric `speedometer_score`.
- **`speedometer3/`** does the same with Speedometer 3.1. Its scenarios differ from the 2.1 ones only in the name, the server and the unit of the score.
- **`web-usage/`** measures a browser the way people use it. A simulated user searches, reads, shops, scrolls a feed, answers a mail and watches a video for ten minutes, against sites emulated in a container. Its pacing comes from published studies of real users. See [web-usage/README.md](web-usage/README.md).

This README describes the browsers, the display setup and the Speedometer scenarios. The Speedometer 2.1 scenarios come from `code/us_*.yml` in [GreenCodeLabel](https://github.com/ribalba/GreenCodeLabel), which measured them on machine 12 in May 2025. The changes are listed below.

## Layout

```text
speedometer2/
  Dockerfile                      Speedometer 2.1 server (WebKit/Speedometer, branch release/2.1, port 8080)
  index.html                      Replaces Speedometer's start page and starts the benchmark on load
  browser-bench.js                Added to Speedometer's page, reports the score when the benchmark has finished
  wait-score                      Answers the waiting run phase with that score on port 9000
  usage_scenario_<browser>.yml    One scenario per browser
speedometer3/
  Dockerfile                      Speedometer 3.1 server (WebKit/Speedometer, release/3.1 pinned to 1386415, port 8080)
  nginx.conf                      Serves it with the module MIME types and the COOP and COEP headers Speedometer 3 needs
  browser-bench.js                Added to Speedometer's page, reports the score when the benchmark has finished
  wait-score                      Answers the waiting run phase with that score on port 9000
  90-browser-bench.sh             Starts socat on port 9000 next to nginx
  usage_scenario_<browser>.yml    One scenario per browser
web-usage/
  server/                         The emulated sites and the simulated user
  usage_scenario_<browser>.yml    One scenario per browser
  README.md                       The session, its sources and its limits
```

## Browsers

| Browser | Scenario | Installed from | Version on 2026-10-06 |
| --- | --- | --- | --- |
| Brave | `usage_scenario_brave.yml` | Brave apt repository | 1.96.61 |
| Google Chrome | `usage_scenario_chrome.yml` | Google apt repository | 154.0.8037.97 |
| Chromium | `usage_scenario_chromium.yml` | xtradeb PPA (Ubuntu itself only ships a snap) | 154.0.8037.92 |
| Ecosia | `usage_scenario_ecosia.yml` | Snap Store, unpacked without snapd, pinned | 152.0.7977.8 |
| Microsoft Edge | `usage_scenario_edge.yml` | Microsoft apt repository | 154.0.4258.62 |
| Falkon | `usage_scenario_falkon.yml` | Ubuntu 26.04 archive | 25.12.3 |
| Firefox | `usage_scenario_firefox.yml` | Mozilla apt repository | 157.0 |
| Nyxt | `usage_scenario_nyxt.yml` | GitHub release tarball, pinned | 4.0.0 |
| Opera | `usage_scenario_opera.yml` | Opera apt repository | 136.0.6008.80 |
| Vivaldi | `usage_scenario_vivaldi.yml` | Vivaldi apt repository | 8.2.4133.83 |
| Waterfox | `usage_scenario_waterfox.yml` | Waterfox CDN tarball, pinned | 6.7.5 |

Browsers from an apt repository always install the newest release, so a later run measures a later version. The install phase prints the installed version into the run log. Ecosia, Nyxt and Waterfox are pinned in their download URL and have to be bumped by hand.

Ecosia ships its Linux browser only as a Snap and a Flatpak. snapd does not run in a container, so the scenario downloads the snap from the Snap Store, unpacks it and starts the Chromium binary inside directly. The snap is newer than the Flatpak (148.1.7778.10). Ecosia has HTTPS-First Mode on by default and blocks the plain HTTP Speedometer page, so install sets the `HttpAllowlist` policy for the host `speedometer` only. A side effect is that Ecosia reports itself as managed by an organisation. Ecosia is not part of GreenCodeLabel.

Flathub has Falkon 26.04.3, which is newer than Ubuntu's 25.12.3. Flatpak inside Docker needs the `parrot-flatpak` AppArmor profile on the host, so the scenario uses the Ubuntu package.

## Flow of the Speedometer scenarios

`speedometer2/` and `speedometer3/` have the same flow:

| Phase | What happens |
| --- | --- |
| install | Installs the browser and prints its version |
| sleep | 10 s pause |
| idle | Starts the browser without a URL, kills it after 60 s |
| sleep2 | 10 s pause |
| run | Starts the browser on `http://speedometer:8080` and ends when Speedometer has finished |
| close | Closes the browser with SIGTERM and kills what is left after 10 s |
| sleep3 | 10 s pause |
| uninstall | Removes the browser |

Speedometer starts by itself, 2.1 through the replaced start page and 3.1 through its `startAutomatically` parameter. The 3.1 server is pinned to a commit of the `release/3.1` branch.

### How the run phase ends with the benchmark

The run phase lasts exactly as long as the browser start and the benchmark, and the score becomes the GMT custom metric `speedometer_score`.

1. `browser-bench.js` is added to Speedometer's page. When Speedometer has finished, it reports the score once to `/bench/done` on the Speedometer server. Speedometer 3.1 switches the page to `#summary` at that point, and 2.1 calls `benchmarkClient.didFinishLastIteration`. The script reacts to that and does nothing while the benchmark runs.
2. The run phase's command starts the browser in the background and then connects to port 9000 of the Speedometer server with plain bash (`/dev/tcp`). It waits on that connection without using any CPU.
3. `socat` answers every connection to port 9000 with `wait-score`. It looks for the report in the server's access log and then sends back the score in the format GMT reads custom metrics from, for example `1791311889454000 speedometer_score=2570`.
4. The run command prints that line and returns, which ends the phase. GMT stores `custom_speedometer_score` for the run phase. Speedometer shows its score with one decimal and GMT takes integers, so the value is the score times 100. An invalid result, or none within 600 s, fails the run.
5. The browser writes its output into `/tmp/browser.log`, so it does not keep the phase open. The close phase ends it and prints the end of that log.

Checked in GMT on a desktop's `:0` on 2026-10-06:

| Scenario | Run phase, browser start included | `speedometer_score` |
| --- | --- | --- |
| `speedometer2/` Google Chrome | 20.6 s | 49310 |
| `speedometer2/` Falkon | 33.9 s | 23240 |
| `speedometer3/` Google Chrome | 23.7 s | 2690 |
| `speedometer3/` Brave | 26.4 s | 2510 |
| `speedometer3/` Vivaldi | 31.0 s | 2440 |
| `speedometer3/` Firefox | 32.8 s | 2130 |
| `speedometer3/` Ecosia | 35.7 s | 1840 |
| `speedometer3/` Nyxt | 35.3 s | 1650 |
| `speedometer3/` Falkon | 42.9 s | 1180 |

The browser has to start inside the phase that waits for it. GMT pauses between two phases for the sampling interval of its slowest metric provider, 999 ms on the cluster machines. A browser started in a phase of its own, in the background, would spend that pause starting up. That part of the start would then belong to no phase, and how much of it varies from run to run.

All eleven browsers finish Speedometer 3.1, checked on a private display on 2026-10-06:

| Browser | Score | Finished after |
| --- | --- | --- |
| Brave | 28.2 | 26 s |
| Google Chrome | 27.2 | 26 s |
| Opera | 25.6 | 26 s |
| Vivaldi | 24.4 | 32 s |
| Microsoft Edge | 22.6 | 26 s |
| Chromium | 22.1 | 26 s |
| Ecosia | 21.6 | 30 s |
| Firefox | 19.7 | 36 s |
| Nyxt | 17.2 | 36 s |
| Waterfox | 16.3 | 73 s |
| Falkon | 14.1 | 43 s |

The scores are from a laptop with software rendering and only show that each browser completes the benchmark.

The idle phase stops the browser with `timeout -s SIGKILL`. So in the run phase most browsers restore the idle tab or offer to restore it, as in GreenCodeLabel. Right after the `timeout`, the same command kills whatever is left of the browser with `pkill -u ubuntu`, because only the browser runs as that user. Ubuntu 26.04 replaced GNU `timeout` with the uutils one, which only kills its direct child and not the process group. Brave's launcher does not `exec` the browser, so without the `pkill` Brave kept running after the idle phase. Both run in one command because leftover processes hold the output pipe, and Docker keeps the phase open for up to 2 s more.

## Changes from GreenCodeLabel

- **Ubuntu 26.04** instead of 24.04 as the base image.
- **No apt proxy.** `192.168.178.43:3142` is only reachable inside that network, and no cluster run used it in the last 120 days.
- **`shm_size: 4gb`** instead of `--shm-size=4gb` in `docker-run-args`. The size is the same. The compose key is not checked against the cluster's `allowed_run_args`, which only allow `--shm-size=1g`.
- **No `ports`** on the speedometer service. The browser reaches it over the Docker network, and the cluster skips `ports` anyway.
- **No `label` block** and therefore no `ignore-unsupported-compose`, so GMT reports unknown keys again.
- **All browsers run as uid 1000**, the user `ubuntu` in the container. In GreenCodeLabel only Falkon and Nyxt did. See [Display](#display) for why.
- **Same flow everywhere.** Only Brave, Chrome and Chromium had the sleep phases, now all scenarios have them. All of them kill leftovers after the `timeout` as described above.
- **Chromium** gets the xtradeb PPA through its key and a source line. `add-apt-repository` needs `software-properties-common`, which left `packagekitd` and `polkitd` running in the container for the whole measurement.
- **Falkon** is a Qt 6 application now. With `QT_XCB_GL_INTEGRATION=none` its window stays black, so that variable is gone. The Ubuntu package's postinst fails without `/usr/share/qt5`, so setup creates it.
- **Waterfox** 6.7.5 is downloaded from the Waterfox CDN in the install phase. GreenCodeLabel served 6.5.7 from a local httpd container, but the 6.7.5 tarball is 132 MB and too big for a GitHub repository.
- **Nyxt** 4.0.0 is the official release, which renders with Electron. GreenCodeLabel used the `ribalba/nyxt` image, a build of Nyxt's master branch from May 2025 with the WebKitGTK renderer, so old and new Nyxt numbers are not comparable. The release is an AppImage. A container has no FUSE, so it is extracted during install. Electron needs `--no-sandbox` in a container. A killed Nyxt leaves its sockets behind and the next start never opens a window, so they are removed after each kill.
- **Fixes.** Most scenarios were called `chrome`. Chromium was started with `--disable-syn`. Opera's uninstall removed a package called `opera` that does not exist.

The three scenarios in GreenCodeLabel's `code/broken/` (Epiphany, Konqueror, Pale Moon) are not part of this repository.

## Running locally

Only GMT's Postgres has to run. Use local runs to check that a scenario works, not for energy numbers.

```bash
cd ~/code/green-metrics-tool
venv/bin/python runner.py \
  --uri ~/code/browser-bench \
  --filename speedometer2/usage_scenario_chrome.yml \
  --name "Speedometer 2.1 Chrome" \
  --dev-no-sleeps --dev-cache-build --skip-download-dependencies --skip-optimizations \
  --allow-unsafe
```

Every scenario mounts `/tmp/.X11-unix`, and Edge and Firefox use `--security-opt seccomp=unconfined`. A local run needs `--allow-unsafe` for both.

The built services have their own image names (`speedometer-2-1`, `speedometer-3-1`, `browser-bench-web`). GMT keys its local build cache under `--dev-cache-build` on that name, so the two Speedometer servers are never mixed up. After changing a server, remove its cached `<name>_gmt_run_tmp` image, or run without `--dev-cache-build`.

## Display

The browsers draw on the host's X server on `:0`, as in GreenCodeLabel. `/tmp/.X11-unix` is mounted into the container, and the browser windows open on the host's screen. Every browser runs as the container user `ubuntu`, uid 1000, and connects without an X cookie. Two things on the host have to fit.

- **The socket `/tmp/.X11-unix/X0` must be writable for uid 1000.** On a Wayland desktop the compositor creates it with mode `0755` for the session user, so the desktop session has to belong to uid 1000. A classic Xorg session creates it with mode `0777`, which works for any uid.
- **The X server must let uid 1000 in without a cookie.** Run this in the session that owns `:0`.

```bash
xhost +si:localuser:$(id -un 1000)
```

The browsers do not run as root because of the first point. As root, the GPU process of Chromium-based browsers drops all capabilities, `CAP_DAC_OVERRIDE` included. A `0755` socket that belongs to the desktop user then refuses its connection with `EACCES`. The browser keeps running and rendering, and Chrome logs `XGetWindowAttributes failed`, but no frame ever reaches the window. On a Wayland desktop that shows up as a black or flickering window.

If either point does not hold, or there is no X server on `:0`, the browser cannot show a window. The idle and run commands ignore errors, so the run still passes. Check that the Speedometer requests in the run phase are there. Other windows on top of the browser can change what it has to draw, so leave the desktop alone while a run is in progress.

The screen must also stay unlocked and switched on for the whole run. On a locked Wayland desktop the compositor stops giving windows new frames. Speedometer 3.1 then stalls in the middle of a run, and the web-usage session fails at its next mark.

## Running on the cluster

Runs are only comparable on the same machine, so pick one and keep it. `submit_software.py` is in `api/` of [gmt-helpers](https://github.com/green-coding-solutions/gmt-helpers).

```bash
python submit_software.py submit \
  --name "Speedometer 2.1 Chrome" \
  --repo-url "https://github.com/green-coding-solutions/browser-bench" \
  --branch main \
  --filename speedometer2/usage_scenario_chrome.yml \
  --machine-id 15 \
  --schedule-mode one-off
```

The cluster user's `allowed_volume_mounts` contain `/tmp/.X11-unix`, and its `allowed_run_args` contain `--security-opt seccomp=unconfined`. No other `docker-run-args` are used. The machine has to have an X server on `:0` that lets the container in, see [Display](#display).
