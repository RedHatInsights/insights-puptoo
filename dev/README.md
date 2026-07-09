# Local Development

## Requirements

- Podman (with Compose V2)

## Quick Start (Makefile)

The recommended way to run the local dev environment is via Makefile targets
from the **repo root**:

```sh
make dev-up                    # Start the full pipeline (detached)
make dev-status                # Check service health
make inject ARCHIVE=dev/test-archives/rhel94_core_collect.tar.gz
make inject-all                # Inject all test archives
make dev-hosts                 # Query ingested hosts from Inventory API
make dev-logs                  # Follow puptoo logs
make dev-down                  # Tear down everything (including volumes)
```

`make inject` uploads a single archive to the Ingress API on `localhost:8080`.
`make inject-all` loops over all `*.tar.gz` files in `dev/test-archives/`.
`make dev-hosts` queries the Host Inventory REST API on `localhost:8082`.

## Compose Files

| File | Description |
|------|-------------|
| `docker-compose.yml` | Minimal stack: Kafka, MinIO, Redis, and Puptoo |
| `full-stack.yml` | Full pipeline: adds Ingress, Host Inventory (MQ + Web), and PostgreSQL |

Both compose files use **KRaft-mode Kafka** (no Zookeeper) with healthchecks and
proper `depends_on` conditions, so services start in the correct order
automatically.

Both compose files include **Tempo** and **Grafana** for local distributed
tracing.  Puptoo starts with `OTEL_ENABLED=true` by default in the dev stacks
so traces are collected automatically.

## Launching the Full Stack

The full stack stands up Ingress, Kafka, MinIO, Redis, Puptoo, and Host
Inventory so the entire first segment of the platform pipeline can be tested.

```sh
cd dev
podman compose -f full-stack.yml up --build
```

> **Note:** The Ingress and Inventory images are pulled from `quay.io`.  See
> those projects for details on building custom images.

## Viewing Traces

Open Grafana at [http://localhost:3000](http://localhost:3000) → **Explore** →
select the **Tempo** datasource.  Traces show the full span tree:
`puptoo.handle_message` → HTTP archive download → `puptoo.extract_facts` →
Kafka produce.

To disable tracing locally, set `OTEL_ENABLED=false` before starting the stack:

```sh
OTEL_ENABLED=false podman compose -f full-stack.yml up --build
```

## Configuration

MinIO credentials default to `minioaccess` / `miniosecret`.  Override via
environment variables or by editing `dev/.env`:

```
MINIO_ACCESS_KEY=mykey
MINIO_SECRET_KEY=mysecret
```

## Exposed Ports

| Service | Port | Purpose |
|---------|------|---------|
| Kafka | 29092 (container) / 9092 (localhost) | Broker |
| MinIO | 9000 (API) / 9001 (Console) | Object store |
| Redis | 6379 | In-memory cache |
| Puptoo | 8000 | Prometheus metrics |
| Tempo | 4318 (OTLP) / 3200 (API) | Trace backend |
| Grafana | 3000 | Trace UI |
| Ingress | 8080 | Upload API (full-stack only) |
| Inventory MQ | 8081 | Inventory MQ service (full-stack only) |
| Inventory Web | 8082 | Inventory Web API (full-stack only) |
| PostgreSQL | 5432 | Inventory DB (full-stack only) |
