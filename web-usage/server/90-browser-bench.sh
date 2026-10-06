#!/bin/sh
# browser-bench: the startup phase connects to port 9000, sends the name of a
# mark and waits. socat answers every connection with serve-mark, which only
# replies once that mark has arrived. The nginx image runs this before it
# starts nginx.
socat TCP-LISTEN:9000,reuseaddr,fork EXEC:/usr/local/bin/serve-mark &
