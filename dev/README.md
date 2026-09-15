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
make inject-all                # Inject all advisor test archives
make inject-qpc ARCHIVE=dev/test-archives/qpc/report_sat_6_7_5.tar.gz
make inject-all-qpc            # Inject all QPC test archives
make dev-hosts                 # Query ingested hosts from Inventory API
make dev-logs                  # Follow puptoo logs (advisor/compliance/malware-detection)
make dev-logs-qpc              # Follow puptoo-qpc logs (QPC)
make dev-down                  # Tear down everything (including volumes)
```

`make inject` / `make inject-all` upload advisor archives to the Ingress API on `localhost:8080`.
`make inject-qpc` / `make inject-all-qpc` upload QPC archives from `dev/test-archives/qpc/`.
`make dev-hosts` queries the Host Inventory REST API on `localhost:8082`.

For a lightweight setup without Ingress or Inventory:

```sh
make dev-up-minimal            # Start minimal stack (Kafka, MinIO, Redis, Puptoo)
make dev-down-minimal          # Tear down minimal stack
```

## Two-Container Setup

Both compose files run two puptoo instances side by side, each scoped to a handler set and
its own Kafka inventory topic:

| Container | Handlers | Inventory topic | Port |
|-----------|----------|----------------|------|
| `puptoo` | `advisor`, `compliance`, `malware-detection` | `platform.inventory.host-ingress-p1` (high priority) | 8000 |
| `puptoo-qpc` | `qpc` | `platform.inventory.host-ingress` (standard priority) | 8001 |

Both containers share the same image, MinIO bucket, Redis instance, and Kafka broker.

### QPC feature flags

QPC processing is **disabled by default** — all three feature flags are set to `false` in
the compose files until the QPC handler is fully wired up:

| Env var | Default | Purpose |
|---------|---------|---------|
| `QPC_PROCESSING_ENABLED` | `false` | Master switch — enables `process_report()` |
| `QPC_ORG_MIGRATION_ENABLED` | `false` | Enables org ID migration logic |
| `QPC_HOSTS_TRANSFORMATION_ENABLED` | `false` | Enables host transformation modifiers |

To enable QPC processing locally, override in the compose env or set
`QPC_PROCESSING_ENABLED=true` before starting the stack.

## Compose Files

| File | Description |
|------|-------------|
| `docker-compose.yml` | Minimal stack: Kafka, MinIO, Redis, Puptoo + Puptoo-QPC |
| `full-stack.yml` | Full pipeline: adds Ingress, Host Inventory (MQ + Web), and PostgreSQL |

Both compose files use **KRaft-mode Kafka** (no Zookeeper) with healthchecks and
proper `depends_on` conditions, so services start in the correct order
automatically.

Both compose files include **Tempo** and **Grafana** for local distributed
tracing. Puptoo starts with `OTEL_ENABLED=true` by default in the dev stacks
so traces are collected automatically.

## Launching the Full Stack

The full stack stands up Ingress, Kafka, MinIO, Redis, Puptoo, Puptoo-QPC, and Host
Inventory so the entire first segment of the platform pipeline can be tested.

```sh
make dev-up
```

> **Note:** The Ingress and Inventory images are pulled from `quay.io`. See
> those projects for details on building custom images.

## Test Archives

### Advisor / Compliance / Malware Detection

Archives in `dev/test-archives/*.tar.gz` are advisor-type archives:

```sh
make inject ARCHIVE=dev/test-archives/rhel94_core_collect.tar.gz
make inject-all
```

### QPC

Archives in `dev/test-archives/qpc/*.tar.gz` are real QPC reports (satellite, discovery,
AWS, virtual/physical, virtwho):

```sh
make inject-qpc ARCHIVE=dev/test-archives/qpc/report_sat_6_7_5.tar.gz
make inject-all-qpc
```

QPC archives are accepted by Ingress and routed to `puptoo-qpc`. With
`QPC_PROCESSING_ENABLED=false` (the default), the container logs a skip message and
returns without further processing — useful for validating routing before enabling the handler.

## Grafana Dashboard

The puptoo Grafana dashboard is maintained as a ConfigMap in
`dashboards/grafana-dashboard-insights-puptoo-general.configmap.yaml` (the
source of truth deployed to OpenShift). For local development, the dashboard
JSON is extracted from this ConfigMap and placed in
`dev/grafana/dashboards/puptoo.json`.

`make dev-up` runs this extraction automatically before starting the stack, so
the local dashboard always stays in sync with the ConfigMap.

You can also regenerate the dashboard file on its own:

```sh
make dev-dashboard
```

This runs `dev/extract-dashboard.py`, which:
1. Parses the ConfigMap YAML and extracts the embedded dashboard JSON.
2. Replaces template-variable datasource UIDs (`${datasource}`,
   `${datasource_aws}`) with the local `prometheus` datasource.
3. Writes the result to `dev/grafana/dashboards/puptoo.json`.

Once the stack is running, open Grafana at
[http://localhost:3000](http://localhost:3000) and navigate to
**Dashboards > Insights > Puptoo (local)** to view the dashboard.

## Viewing Traces

Open Grafana at [http://localhost:3000](http://localhost:3000) → **Explore** →
select the **Tempo** datasource. Traces show the full span tree:
`puptoo.handle_message` → HTTP archive download → `puptoo.extract_facts` →
Kafka produce.

To disable tracing locally, set `OTEL_ENABLED=false` before starting the stack:

```sh
OTEL_ENABLED=false make dev-up
```

## Configuration

MinIO credentials default to `minioaccess` / `miniosecret`. Override via
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
| Puptoo | 8000 | Prometheus metrics (advisor/compliance/malware-detection) |
| Puptoo-QPC | 8001 | Prometheus metrics (qpc) |
| Prometheus | 9090 | Metrics backend |
| Tempo | 4318 (OTLP) / 3200 (API) | Trace backend |
| Grafana | 3000 | Dashboards & Traces UI |
| Ingress | 8080 | Upload API (full-stack only) |
| Inventory MQ | 8081 | Inventory MQ service (full-stack only) |
| Inventory Web | 8082 | Inventory Web API (full-stack only) |
| PostgreSQL | 5432 | Inventory DB (full-stack only) |
