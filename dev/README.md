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
make dev-unleash               # Open Unleash admin console
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

Both compose files include **Unleash** and **PostgreSQL** for feature flag
management.  Puptoo starts with `BYPASS_UNLEASH=true` by default, so the
Unleash server does not need to be running for normal development.  See the
[Feature Flags](#feature-flags) section below for details.

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

## Feature Flags

Puptoo uses [Unleash](https://www.getunleash.io/) for feature flag management,
following the same pattern as
[insights-host-inventory](https://github.com/RedHatInsights/insights-host-inventory).

By default, `BYPASS_UNLEASH=true` in `dev/.env`, so Puptoo uses hardcoded
fallback values for all flags and does not require a running Unleash server.

To develop or test with live feature flags:

1. Set `BYPASS_UNLEASH=false` in `dev/.env` (or export it in your shell).
2. Start the stack — the Unleash server and its PostgreSQL database will start
   automatically as part of the compose stack.
3. Open the Unleash admin console:

   ```sh
   make dev-unleash   # opens http://localhost:4242
   ```

4. Log in with the default admin credentials (`admin` / `unleash4all`).

Feature flag definitions are pre-loaded from `.unleash/flags.json` on each
container startup (`IMPORT_DROP_BEFORE_IMPORT=true`).  To add a new flag for
local development, add it to that file and restart the Unleash container.

The feature flag client is initialized in `src/puptoo/feature_flags.py`.
The public API is:

```python
from src.puptoo.feature_flags import get_flag_value

if get_flag_value("puptoo.some-flag", org_id):
    # feature-flagged code path
    ...
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BYPASS_UNLEASH` | `true` (dev) / `false` (prod) | Skip Unleash and use fallback values |
| `UNLEASH_URL` | `http://unleash:4242/api` | Unleash server API endpoint |
| `UNLEASH_TOKEN` | (see `dev/.env`) | Client API token for authentication |
| `UNLEASH_CACHE_DIR` | `/tmp/.unleashcache` | Local cache directory for flag state |
| `UNLEASH_REFRESH_INTERVAL` | `15` | Seconds between flag refresh polls |

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
| Unleash | 4242 | Feature flag admin console |
| PostgreSQL | 5432 | Unleash + Inventory DB |
| Ingress | 8080 | Upload API (full-stack only) |
| Inventory MQ | 8081 | Inventory MQ service (full-stack only) |
| Inventory Web | 8082 | Inventory Web API (full-stack only) |
