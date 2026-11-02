# Platform Upload Processor II

The Platform Upload Processor II (PUPTOO) is the unified upload processing service
for the Insights Platform. It handles payloads from multiple service types:
**advisor**, **compliance**, **malware-detection**, and **QPC** (Discovery/Satellite).

## Details

PUPTOO is a component of the Insights Platform that validates payloads uploaded
to Red Hat by the insights-client and other reporters (including QPC/Discovery).
The service is engaged after an upload has been received and stored in cloud storage.

PUPTOO retrieves payloads via URL in the message, processes them through
service-specific handlers, and sends the results to the inventory service.

The service runs in OpenShift Dedicated as two deployments from a single
container image (see [Architecture](#architecture) below).

> **Note:** With QPC processing now consolidated into this codebase (formerly
> handled by the standalone [yuptoo](https://github.com/RedHatInsights/yuptoo)
> service), this project will transition to the name **insights-upload-processor**
> to reflect its broader scope. References to "puptoo" in code, configuration,
> and documentation will be migrated incrementally.

## Architecture

PUPTOO uses a **dual-deployment model**: one container image, two deployments,
each restricted to specific service types via `ENABLED_HANDLERS`.

| Deployment | Consumer Group | Handlers | Inventory Topic | Replicas (prod) |
|---|---|---|---|---|
| `processor` | `insights-puptoo` | `advisor`, `compliance`, `malware-detection` | `platform.inventory.host-ingress-p1` | 64 |
| `qpc-processor` | `qpc-group` | `qpc` | `platform.inventory.host-ingress` | 8 |

Both deployments consume from `platform.upload.announce`. The `ENABLED_HANDLERS`
environment variable controls which message types each deployment accepts;
unrecognized services are silently skipped. This consumer group isolation
prevents the two deployments from stealing each other's messages.

### Handler Registry

Handlers are registered via the `@handler("service")` decorator in
`src/puptoo/handlers/`. Currently registered:

- **advisor**: extracts canonical facts and system profile via insights-core
- **compliance**: extracts canonical facts, forwards to inventory (no system-profile processing)
- **malware-detection**: identical to compliance (subclasses `ComplianceHandler`)
- **qpc**: processes QPC/Discovery reports, transforming hosts for inventory ingestion

### QPC Processing

QPC (Quipucords/Discovery) report processing was consolidated from the former
standalone `yuptoo` service. Key differences from advisor processing:

- Reports can contain thousands of hosts (capped at `MAX_HOSTS_PER_REP`, default 10,000)
- Host transformation logic controlled by `QPC_HOSTS_TRANSFORMATION_ENABLED`
- Longer Kafka poll interval (`QPC_KAFKA_CONSUMER_MAXPOLL_INTERVAL`, default 1,800,000 ms)
- Sends to `platform.inventory.host-ingress` (standard priority, not `-p1`)

## How it Works

![UML](https://www.plantuml.com/plantuml/png/VLDHRzem47xFhpXbZojPW81KX50VkacJfgbQrvUrLUGu1_7cs9bzfgCL_tss0m8s0G_8khllxllkljnOOePSAnCI917k7kxWpcYErWgrWazIloIeV6u3dMIqrARDN2SrgpEcb7QAuxdycabHCn9Q9PsV8RZec2BeN4TQ_mSIQkr3scooHbloiusdS09iAf7uVgnY5i6EEpGjKnwJd2CsMFIpPj3QLV9L4u8HguP0By-AcS5RoZZtRqfdCDyzGRcsGhEuUb8fPuGhpzEdKwwbH1uafZ6b5Q6YaZOTXZJhEYau2_aFQrLd1kk6KJQtQDQ2es8jBh93Z_UqUerzMYGMbAQUJPPjGyZWRuUMIb77nXMlXwDn4Qix8rHOaGo4kJC65SaDK8EWpGe-tqRQ_jc3v_qh1dT4GlIOKqo9rn0V3OjyE0a1P-A0XszVW3JK-aM5nSKnpF16h16MHhTmFuxuQbhuAVsL0ovSRLe0Agvhh66VYhKaMhJ4sYve6-MZqI2V38Rvz_nwDYncHPvDXkF9z3gV5Z_IRN9q-iTtbNJuV3ZqxOwMFU7qfEx7K3d-2odfAm-8Zt_8C4uMbk4_bk-nJ-f5K0D2sU0QE-3QOC8aWNMS1tU2_-txNJPoj62iFxLXZmwcqrvKT4gyRrsN0HtlktF2uriQAGPJRAzIkx64RTaPlHGIOt3x7ChtHCeZ5ysrdoWKawMdKVwqMYss2KgBNhMGpk2HbCDEptxF_wYHk3mLSycjXouXjHllhuggJYxlSB1eAj6Fll7LhfL_0G00 "PUPToo Processing Flow")

The advisor/compliance/malware-detection workflow:

- Receive a message from `platform.upload.announce` topic
- Download the archive from the URL in the message
- Insights Core extracts facts via `get_canonical_facts` and runs a custom `system-profile` ruleset
- Send the extracted result to inventory via the message queue

The QPC workflow:

- Receive a QPC report message from `platform.upload.announce` (service: `qpc`)
- Validate and decompress the report payload
- Transform hosts per Discovery/Satellite schema into HBI-compatible format
- Send each host to inventory via `platform.inventory.host-ingress`

### The Compliance Situation

Puptoo also functions as a forwarder for compliance uploads put on the `platform.upload.compliance`. We do this because
compliance depends on an inventory ID that was taken away when ingress stopped retrieving that from inventory on its own. No processing
is performed on the compliance uploads. We simply forward it to inventory with canonical facts.

### JSON

Note: Puptoo now listens to the new ingress platform.upload.announce topic.

The JSON expected by the PUP service from the upload service looks like this:

```json
 {
	"account": "<account number>",
	"category": "collection",
	"content_type": "application/vnd.redhat.<servicename>.collection+tgz",
	"metadata": {
		"reporter": "",
		"stale_timestamp": "0001-01-01T00:00:00Z"
	},
	"request_id": "<UUID for the payload>",
	"principal": "<currently the org ID>",
	"org_id": "<org_id>",
	"service": "<servicename>",
	"size": 214015,
	"url": "<URL to download the archive from S3>",
	"b64_identity": "<base64 encoded identity>",
	"timestamp": "2022-05-10T09:14:40.513569064Z"
}
```

The message sent to the inventory service will include the facts extracted from the archive

```json
{"data": {"facts": [{"facts": {"insights_id": "a756b571-e227-46a5-8bcc-3a567b7edfb1",
                               "machine_id": null,
                               "bios_uuid": null,
                               "subscription_manager_id": null,
                               "ip_addresses": [],
                               "mac_addresses": [],
                               "fqdn": "Z0JTXJ7YSG.test"},
                     "namespace": "insights-client",
                     "system-profile": {"foo": "bar"}}]},
 "platform_metadata": {"key": "value"},
 "operation": "add_host"}
```

**The above facts are managed by the [insights-core](https://www.github.com/RedHatInsights/insights-core) project and may be added or taken away. The README should be updated to reflect those
changes**

Fields:

- account: The account number used to upload. Will be modified to `account_number` when posting to inventory
- principal: The upload org_id. Will be modified to `org_id` when posting to inventory
- request_id: The ID of the individual uploaded archive
- size: Size of the payload in bytes
- service: The service name as provided by the MIME type.
- url: The url from which the archive will be downloaded
- facts: An array containing facts for each host

If the fact extraction fails, the archive will be considered "bad." A message will be sent back to the upload service so the file can be moved to the rejected bucket.

Failure example:

```json
    {"validation": "failure", "request_id": "23oikjonsdv329"}
```

## Environment Variables

### Core Configuration

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `insights-puptoo` | Application identity for logging and OTel service name |
| `GROUP_ID` | `$APP_NAME` | Kafka consumer group identity |
| `ENABLED_HANDLERS` | *(unset, accept all)* | Comma-separated handler list (e.g. `advisor,compliance,malware-detection`). Unset or empty accepts all registered handlers |
| `INVENTORY_TOPIC` | `platform.inventory.host-ingress-p1` (Clowder) | Destination topic for inventory messages |
| `ANNOUNCE_TOPIC` | `platform.upload.announce` (Clowder) | Source topic for upload messages |

### QPC Configuration

| Variable | Default | Description |
|---|---|---|
| `QPC_PROCESSING_ENABLED` | `true` | Master switch for QPC report processing |
| `QPC_HOSTS_TRANSFORMATION_ENABLED` | `true` | Enable host transformation logic for QPC reports |
| `MAX_HOSTS_PER_REP` | `10000` | Maximum hosts per QPC report |
| `DISCOVERY_HOST_TTL` | `29` | TTL (days) for Discovery-sourced hosts |
| `SATELLITE_HOST_TTL` | `29` | TTL (days) for Satellite-sourced hosts |
| `BYPASS_PAYLOAD_EXPIRATION` | `false` | Skip payload age validation on QPC reports |

### Deployment Parameters (deployment.yaml)

The ClowdApp template defines parameters for both deployments. Key QPC-specific
parameters set via app-interface:

| Parameter | Default | Description |
|---|---|---|
| `QPC_MIN_REPLICAS` | `1` | Min replicas for qpc-processor deployment |
| `QPC_APP_NAME` | `insights-puptoo-qpc` | OTel service name for QPC deployment |
| `QPC_GROUP_ID` | `qpc-group` | Kafka consumer group for QPC deployment |
| `QPC_ENABLED_HANDLERS` | `qpc` | Handler restriction for QPC deployment |
| `QPC_INVENTORY_TOPIC` | `platform.inventory.host-ingress` | Inventory topic for QPC (standard priority) |
| `QPC_KAFKA_CONSUMER_MAXPOLL_INTERVAL` | `1800000` | Max poll interval (ms) for QPC consumers |

## Rollback Procedure

If QPC processing needs to be disabled in an environment, no code change is
required. Two app-interface parameter changes are sufficient:

1. Set `QPC_PROCESSING_ENABLED` to `false` (disables QPC message processing at the application level)
2. Set `QPC_MIN_REPLICAS` to `0` (scales down the qpc-processor deployment)

These changes can be applied via a single app-interface MR. The `processor`
deployment (advisor/compliance/malware-detection) is completely unaffected.

To re-enable, reverse both values and merge.

## Running

The default environment variables should be acceptable for testing.
PUPTOO does expect a kafka message queue to be available for connection.

#### Prerequisites

- Python 3.11
- [uv](https://docs.astral.sh/uv/) - Python package and project manager
- [pre-commit](https://pre-commit.com/) - Git hook framework

#### Setting up the development environment

Install dependencies and set up pre-commit hooks:

```sh
uv sync
pre-commit install
```

`uv sync` creates a virtual environment in `.venv/` and installs all project and dev dependencies from `uv.lock`.

Pre-commit hooks run automatically on every commit to enforce code quality:
- **ruff** - linting (with auto-fix) and formatting
- **trailing-whitespace** / **end-of-file-fixer** - whitespace hygiene
- **check-yaml** / **check-merge-conflict** - file integrity checks

To run the hooks manually against all files:

```sh
pre-commit run --all-files
```

#### Running Locally

Activate your virtual environment and run the validator

```sh
source .venv/bin/activate
puptoo
```

Or run directly with uv:

```sh
uv run puptoo
```

#### Running with Podman Compose

Several compose files are available in the `dev/` directory for standing up a local dev environment. See [`dev/README.md`](dev/README.md) for full details.

Both compose files run **two puptoo instances** side by side: `puptoo` (advisor, compliance,
malware-detection → `platform.inventory.host-ingress-p1`) and `puptoo-qpc` (qpc →
`platform.inventory.host-ingress`). QPC processing is disabled by default via feature flags.

Stand up the full pipeline (Ingress, Host Inventory, PostgreSQL, both puptoo instances):

```sh
make dev-up
```

Stand up the minimal stack (Kafka, RustFS, Redis, both puptoo instances — no Ingress/Inventory):

```sh
make dev-up-minimal
```

Inject archives and query results:

```sh
make inject ARCHIVE=dev/test-archives/rhel94_core_collect.tar.gz            # advisor archive
make inject-all                                                             # all advisor archives
make inject KIND=qpc ARCHIVE=dev/test-archives/qpc/report_sat_6_7_5.tar.gz # QPC archive
make inject-all KIND=qpc                                                    # all QPC archives
make dev-hosts                                                              # query ingested hosts
```

Tear down (including named volumes):

```sh
make dev-down
```

> **Note:** The Ingress and Inventory images are pulled from `quay.io`. See those projects for details on building custom images.

#### Bonfire

Deploying with bonfire to an ephemeral environment is the preferred way to test puptoo. See the [bonfire documentation](https://clouddot.pages.redhat.com/docs/dev/getting-started/ephemeral/deploying.html) for more information.

## File Processing

The best way to test is by standing up the local dev stack with `podman compose` (see [Running with Podman Compose](#running-with-podman-compose)). The [insights-upload](https://www.github.com/RedHatInsights/insights-upload) repo has additional details regarding posting archives to the service.

This test assumes you have an inventory service available and ready to use. Visit the `insights-host-inventory` repo for those instructions.

## Testing System Profile

Occasionally, an archive may be rejected by puptoo for a reason that is unclear. You may also see an archive that doesn't seem to work properly or gathers the wrong information. In order to test this locally, you can use the `insights-run` tool to process the system-profile of that archive easily.

```sh
   uv run insights-run -p src.puptoo ~/path/to/archive
```

This will print the system_profile so you can analyze it for issues.

### Testing with provided test-archive sample

Puptoo has a `dev/test-archives/core-base` folder that contains a test sample of insights-archive. It emulates a minimized set of files inside a real archive that required by the puptoo system-profile usage.

From this nature, this test-archive example can be used for system-profile QA Verification, and related tests.

Tar the provided test-archive example with:
```sh
$ cd ./dev/test-archives
$ tar -zcvf insights-puptoo-test-archive.tar.gz ./core-base
```

## Konflux Hermetic Build

Konflux Hermetic Build had been enabled for Puptoo repo.

A hermetic build is a secure, self-contained build process that doesn’t depend on anything outside of the build environment.
Konflux can prefetch dependencies for your hermetic builds using Cachi2 by generating a software bill of materials (SBOM) where all dependencies are properly declared and pinned to specific versions.

For any dependencies update introduced in [pyproject.toml](pyproject.toml) and [uv.lock](uv.lock), please update the following required files referring to this [Hermetic Build Process](.hermetic_builds/README.md):

  - Enabling prefetch builds for rpm
    - [rpms.in.yaml](rpms.in.yaml)
    - [rpms.lock.yaml](rpms.lock.yaml)

  - Enabling prefetch builds for pip
    - [requirements.txt](requirements.txt)
    - [requirements-dev.txt](requirements-dev.txt)
    - [requirements-build.in](requirements-build.in)
    - [requirements-build.txt](requirements-build.txt)
    - [requirements-extras.txt](requirements-extras.txt)

  - Enabling prefetch builds for generic fetcher
    - [artifacts.lock.yaml](artifacts.lock.yaml)

More Konflux Hermetic Build resources:
  - https://konflux-ci.dev/docs/building/hermetic-builds/
  - https://konflux-ci.dev/docs/building/prefetching-dependencies/

## Deployment

Container images are built via [Konflux](https://konflux-ci.dev/) hermetic builds (see [Konflux Hermetic Build](#konflux-hermetic-build) above). Merges to `master` trigger a new image build. To promote to production, an app-interface MR updates the image reference in the production deploy configuration.

## Contributing

All outstanding issues or feature requests should be filed as Issues on this Github repo or within JIRA. PRs should be submitted against the master branch for any features or changes.

Any new system-profile items should include a test file inside `dev/test-archives/core-base`. This file should emulate the file that would be found
inside a real archive, and the test itself should be written and provided in the `tests` directory.

## Running unit tests

```sh
uv run pytest tests/
```

## Versioning

New functionality that may effect other services should increment by `1`. Minor features and bugfixes can increment by `0.0.1`

## Authors

- **Stephen Adams** - **Initial Work** - [SteveHNH](https://github.com/SteveHNH)
- **Pranav Lawate** - **Maintainer** - [pranlawate](https://github.com/pranlawate)
