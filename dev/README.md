# Local Development

## Requirements

- Podman (with Compose V2)

## Compose Files

| File | Description |
|------|-------------|
| `docker-compose.yml` | Minimal stack: Kafka, MinIO, Redis, and Puptoo |
| `full-stack.yml` | Full pipeline: adds Ingress, Host Inventory (MQ + Web), and PostgreSQL |
| `test-stack.yml` | IO test harness: Kafka, MinIO, Puptoo, plus a test producer and consumer |

All compose files use **KRaft-mode Kafka** (no Zookeeper) with healthchecks and
proper `depends_on` conditions, so services start in the correct order
automatically.

All three compose files include **Tempo** and **Grafana** for local distributed
tracing.  Puptoo starts with `OTEL_ENABLED=true` by default in the dev stacks
so traces are collected automatically.

## Quick Start

Build and launch the minimal stack:

```sh
cd dev
podman compose up --build
```

Tear down (including named volumes):

```sh
podman compose down -v
```

## Launching the Full Stack

The full stack stands up Ingress, Kafka, MinIO, Redis, Puptoo, and Host
Inventory so the entire first segment of the platform pipeline can be tested.

```sh
cd dev
podman compose -f full-stack.yml up --build
```

> **Note:** The Ingress and Inventory images are pulled from `quay.io`.  See
> those projects for details on building custom images.

## Launching the Test Stack

The test stack lets you watch archives flow through Puptoo end-to-end with a
test producer and consumer — no other platform components required.

1. Start the core services and let healthchecks settle:

   ```sh
   cd dev
   podman compose -f test-stack.yml up --build
   ```

2. Start the consumer (reads from `platform.inventory.host-ingress`):

   ```sh
   podman compose -f test-stack.yml up -d consumer
   ```

3. Fire the producer (sends 100 copies of the configured archive):

   ```sh
   podman compose -f test-stack.yml up -d producer
   ```

The consumer logs the `elapsed_time` showing how long Puptoo took to process
each archive.

## Viewing Traces

Open Grafana at [http://localhost:3000](http://localhost:3000) → **Explore** →
select the **Tempo** datasource.  Traces show the full span tree:
`puptoo.handle_message` → HTTP archive download → `puptoo.extract_facts` →
Kafka produce.

To disable tracing locally, set `OTEL_ENABLED=false` before starting the stack:

```sh
OTEL_ENABLED=false docker compose up --build
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
