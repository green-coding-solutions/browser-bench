# Dockerfile
FROM python:3.9-slim

# Install git so we can clone, and socat for the run phase's waiting connection
RUN apt-get update && apt-get install -y git socat && rm -rf /var/lib/apt/lists/*

# Set up the working directory
WORKDIR /app

# Clone the Speedometer repository
RUN git clone https://github.com/WebKit/Speedometer.git /app
RUN git fetch --all
RUN git checkout release/2.1

COPY index.html /app/index.html

# browser-bench addition: a script that reports the score when Speedometer
# has finished, and the command that answers the run phase with it.
COPY browser-bench.js /app/browser-bench.js
COPY wait-score /usr/local/bin/wait-score
RUN chmod 0755 /usr/local/bin/wait-score

# Expose the default python http.server port, and the port the run phase waits on
EXPOSE 8080 9000

# Run a simple Python HTTP server when container starts. Its access log also
# goes to a file for wait-score. socat answers each connection to port 9000
# with wait-score.
CMD [ "bash", "-c", "socat TCP-LISTEN:9000,reuseaddr,fork EXEC:/usr/local/bin/wait-score & exec python -m http.server 8080 2> >(tee -a /var/log/speedometer-access.log >&2)" ]
