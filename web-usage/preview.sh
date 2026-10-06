#!/usr/bin/env bash
# Watch the web-usage session in your own browser, faster than real time.
#
# usage: web-usage/preview.sh [speed]
#
# Builds the web container, serves it on http://localhost:8088 and opens the
# session there with ?speed=<speed> (default 10). Every wait, keystroke,
# scroll step and the video run that many times faster, so the whole session
# takes about a minute at speed 10. Waiting for pages to load stays in real
# time. The marks of the phases are printed as they arrive. Ctrl+C stops the
# container. GMT runs never use this and always run at the real speed.
set -euo pipefail
speed=${1:-10}
name=browser-bench-web-preview
cd "$(dirname "$0")/server"
echo "Building the web container ..."
docker build -q -t browser-bench-web . > /dev/null
docker rm -f "$name" > /dev/null 2>&1 || true
docker run -d --rm --name "$name" -p 127.0.0.1:8088:80 browser-bench-web > /dev/null
trap 'docker rm -f "$name" > /dev/null 2>&1 || true' EXIT
url="http://localhost:8088/start/?session=1&speed=$speed"
echo "Session at $url"
xdg-open "$url" > /dev/null 2>&1 || echo "Open it in a new browser tab."
echo "Marks (Ctrl+C to stop):"
docker exec "$name" sh -c 'touch /var/log/nginx/marks.log && tail -f /var/log/nginx/marks.log'
