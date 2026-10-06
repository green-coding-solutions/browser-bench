# Speedometer 3.1 (WebKit/Speedometer, branch release/3.1), served by nginx on
# port 8080. The commit is pinned, so every build serves the same benchmark.
# Speedometer 3 loads ES modules, so nginx sends the right MIME types, and the
# COOP and COEP headers that its timing relies on.
FROM alpine:3.23 AS src
ARG SPEEDOMETER_COMMIT=1386415be8fef2f6b6bbdbe1828872471c5d802a
RUN apk add --no-cache git \
 && git init -q /src && cd /src \
 && git fetch -q --depth 1 https://github.com/WebKit/Speedometer.git "$SPEEDOMETER_COMMIT" \
 && git checkout -q FETCH_HEAD

FROM nginx:1.29-alpine3.23
RUN rm -rf /usr/share/nginx/html/*
COPY --from=src /src/index.html /src/about.html /src/instructions.html /usr/share/nginx/html/
COPY --from=src /src/resources/ /usr/share/nginx/html/resources/
COPY nginx.conf /etc/nginx/conf.d/default.conf

# browser-bench addition: a script that reports the score when Speedometer
# has finished, and the command that answers the waiting run phase with it on
# port 9000.
RUN apk add --no-cache socat
COPY browser-bench.js /usr/share/nginx/html/browser-bench.js
RUN sed -i 's|</body>|<script src="browser-bench.js"></script></body>|' /usr/share/nginx/html/index.html \
 && grep -q 'browser-bench.js' /usr/share/nginx/html/index.html
COPY wait-score /usr/local/bin/wait-score
COPY 90-browser-bench.sh /docker-entrypoint.d/90-browser-bench.sh
RUN chmod 0755 /usr/local/bin/wait-score /docker-entrypoint.d/90-browser-bench.sh
EXPOSE 8080 9000
