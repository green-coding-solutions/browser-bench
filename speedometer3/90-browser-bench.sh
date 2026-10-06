#!/bin/sh
# browser-bench: the run phase connects to port 9000 and waits. socat answers
# every connection with wait-score, which only replies once Speedometer has
# finished. The nginx image runs this before it starts nginx.
socat TCP-LISTEN:9000,reuseaddr,fork EXEC:/usr/local/bin/wait-score &
