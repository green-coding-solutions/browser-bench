# Emulated web sites for the web-usage scenario. All pages, texts and images
# come from a fixed seed, so every build serves the same content, and the
# browser under test never talks to anything but this container.
FROM python:3.13-alpine3.24 AS build
RUN apk add --no-cache imagemagick ffmpeg
WORKDIR /build
COPY build_site.py .
COPY static/ static/
RUN python3 build_site.py /out && cp -r static /out/static \
 && magick -size 32x32 xc:'#1a56c4' /out/favicon.ico

# The videos are from Tears of Steel, (c) Blender Foundation,
# mango.blender.org, CC BY 3.0: the 1080p VP9 transcode on Wikimedia Commons,
# 24 fps with Opus audio. VP9 is what YouTube serves to desktop browsers, and
# every browser of this repository decodes it. Commons answers several quick
# seeks with 429 Too Many Requests, so ffmpeg fetches the part from 2:00 to
# 8:00 in one go, about 125 MB, and retries after a pause if it is throttled.
# Everything else is cut from that local copy. The exact bytes depend on the
# ffmpeg version, so the checks are on codec, size and length, and the build
# log shows the checksums.
ARG VIDEO_URL=https://upload.wikimedia.org/wikipedia/commons/transcoded/1/10/Tears_of_Steel_in_4k_-_Official_Blender_Foundation_release.webm/Tears_of_Steel_in_4k_-_Official_Blender_Foundation_release.webm.1080p.vp9.webm
RUN for attempt in 1 2 3 4; do \
      ffmpeg -hide_banner -loglevel error -user_agent "browser-bench (https://github.com/green-coding-solutions/browser-bench)" \
        -ss 120 -i "$VIDEO_URL" -t 360 -map 0:v:0 -map 0:a:0 -c copy -y /tmp/source.webm && break; \
      [ "$attempt" = 4 ] && exit 1; echo "download failed, retrying in 60 s"; sleep 60; \
    done

# The video site: 4 minutes, from 2:00 to 6:00 of the film.
RUN mkdir -p /out/video/media \
 && ffmpeg -hide_banner -loglevel error -i /tmp/source.webm -t 240 -c copy -map_metadata -1 -fflags +bitexact /out/video/media/clip.webm \
 && probe=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate -show_entries format=duration -of csv=p=0 /out/video/media/clip.webm | tr '\n' ',') \
 && echo "clip: $probe" && sha256sum /out/video/media/clip.webm \
 && echo "$probe" | grep -q '^vp9,1920,858,24/1,' \
 && echo "$probe" | awk -F, '{ exit !($5 > 235 && $5 < 245) }'

# Twelve 10 s clips for the posts of the social feed, the twelve 10 s parts
# of 6:00 to 8:00. Feeds show square video at about 720p, so the clips are
# cropped to the middle and encoded as 720x720 VP9 at 24 fps. The encoder's
# realtime mode takes about a second per clip.
RUN mkdir -p /out/social/media \
 && for i in 0 1 2 3 4 5 6 7 8 9 10 11; do \
      ffmpeg -hide_banner -loglevel error -ss $((240 + i * 10)) -i /tmp/source.webm -t 10 -vf "crop=858:858,scale=720:720" \
        -c:v libvpx-vp9 -deadline realtime -cpu-used 8 -b:v 1200k -maxrate 1500k -bufsize 3000k -g 48 \
        -c:a libopus -b:a 96k -map_metadata -1 -fflags +bitexact /out/social/media/clip$i.webm || exit 1; \
      ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height -of csv=p=0 /out/social/media/clip$i.webm | grep -q '^vp9,720,720$' || exit 1; \
    done \
 && sha256sum /out/social/media/*.webm && rm /tmp/source.webm

FROM nginx:1.29-alpine3.23
RUN apk add --no-cache socat
COPY --from=build /out /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY wait-mark serve-mark /usr/local/bin/
COPY 90-browser-bench.sh /docker-entrypoint.d/90-browser-bench.sh
RUN chmod 0755 /usr/local/bin/wait-mark /usr/local/bin/serve-mark /docker-entrypoint.d/90-browser-bench.sh
