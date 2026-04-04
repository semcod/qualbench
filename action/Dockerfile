FROM python:3.12-slim

RUN pip install --no-cache-dir qualbench && \
    apt-get update && apt-get install -y --no-install-recommends git jq && \
    rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
