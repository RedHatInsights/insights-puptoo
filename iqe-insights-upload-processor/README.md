# IQE Puptoo Plugin

## Overview

This plugin provides functional tests for the Insights Platform Upload Processor (puptoo).
It is embedded in the `insights-puptoo` repository under `iqe-insights-upload-processor/`,
following the pattern established by `insights-host-inventory` (RHINENG-21877).

The plugin was migrated from [GitLab](https://gitlab.cee.redhat.com/insights-qe/iqe-puptoo-plugin).

## Contents

* [Setup](#setup)
* [Running Tests](#running-tests)
* [Markers](#markers)
* [Dependency Updates](#dependency-updates)
* [Deprecating Code](#deprecating-code)
* [Further Reading](#further-reading)

## Setup

Installation and setup instructions are located in [docs/IQE.md](../docs/IQE.md).

## Running Tests

Assuming you have the environment set up correctly, the basic command to run the tests:

```bash
# Run all tests
ENV_FOR_DYNACONF=stage_proxy uv --project iqe-insights-upload-processor run \
    iqe tests plugin puptoo

# Run smoke tests only
ENV_FOR_DYNACONF=stage_proxy uv --project iqe-insights-upload-processor run \
    iqe tests plugin puptoo -m smoke

# Run a specific test
ENV_FOR_DYNACONF=stage_proxy uv --project iqe-insights-upload-processor run \
    iqe tests plugin puptoo -k test_plugin_accessible
```

### Health Check

Run a basic operational check to confirm the plugin is installed and working:

```bash
ENV_FOR_DYNACONF=stage_proxy uv --project iqe-insights-upload-processor run \
    iqe tests plugin puptoo -k test_plugin_accessible
```

## Markers

* `smoke` — smoke tests for puptoo PR checks

## Dependency Updates

The IQE dependencies live in a Red Hat private Nexus repository. To update them:

```bash
uv --project iqe-insights-upload-processor lock
uv --project iqe-insights-upload-processor sync
```

Then commit the updated lockfile:

```bash
git add iqe-insights-upload-processor/uv.lock
```

## Deprecating Code

The IQE framework provides deprecation support. Refer to the
[IQE deprecation instructions](https://insights-qe.pages.redhat.com/iqe-core-docs/deprecations.html)
for guidance.

## Further Reading

* Full setup guide: [docs/IQE.md](../docs/IQE.md)
* [IQE Core Documentation](https://insights-qe.pages.redhat.com/iqe-core-docs/)
