FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir hatchling

COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir .

FROM python:3.12-slim AS runner

WORKDIR /app

RUN groupadd -r contracthub && useradd -r -g contracthub contracthub

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/contracthub /usr/local/bin/contracthub

RUN mkdir -p /data && chown -R contracthub:contracthub /data

USER contracthub

ENV CONTRACTHUB_DB="sqlite:////data/contracthub.db" \
    PORT=8000

EXPOSE 8000

VOLUME ["/data"]

ENTRYPOINT ["contracthub", "serve", "--host", "0.0.0.0", "--port", "8000"]
