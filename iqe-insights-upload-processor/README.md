# IQE Puptoo Plugin

[![pipeline status](https://gitlab.cee.redhat.com/insights-qe/iqe-puptoo-plugin/badges/master/pipeline.svg)](https://gitlab.cee.redhat.com/insights-qe/iqe-puptoo-plugin/commits/master)

## Overview

This plugin is designed to perform a set of functional tests targeting the
Insights Platform Upload Processor

#### Contents

* [Getting Started](#getting-started)
* [Installation Confirmation](#installation-confirmation)
* [Health check](#health-check)
* [Authentication](#authentication)
* [Running Tests](#running-tests)

## Getting Started

Make sure your machine has [Red Hat certificates](https://insights-qe.pages.redhat.com/iqe-core-docs/tutorial/part3.html?highlight=cert#prerequisites)
and Python 3.8 before proceeding. To install the plugin:

```sh
# Clone the repository
git clone git@gitlab.cee.redhat.com:insights-qe/iqe-puptoo-plugin.git

# Change to the plugin directory
cd iqe-puptoo-plugin

# Setup the virtual environment
python3.8 -m venv venv
# Activate the virtual environment
source venv/bin/activate

# Make cert available on your env
export REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt

# Setup pip to be able to download the iqe python proprietary packages from Nexus
pip config set global.index-url https://nexus.corp.redhat.com/repository/cqt-pypi/simple --site
pip config set global.index https://nexus.corp.redhat.com/repository/cqt-pypi/simple/ --site
pip install -U pip wheel

# Install IQE Framework
pip install iqe-core

# Install the plugin (use this option if you intend to develop this plugin)
iqe plugin install --editable .
pre-commit install

# Install the plugin (use this option if you don't intend to develop this plugin)
iqe plugin install puptoo
```

## Installation Confirmation

Once you have the plugin installed, you can confirm its installation like this:

```
iqe plugin list
INSTALLED PLUGINS

Name                   Package                           Version
---------------------  --------------------------------  -------------------------------
puptoo                 iqe-puptoo-plugin                 1.2.3
```

## Health check

Run a basic "operational check" for this plugin. This runs a single test to confirm the plugin was installed successfully and is operational. Example command and output upon success are included below.

Note: don't forget to activate your virtual environment
```
iqe tests plugin puptoo -k test_plugin_accessible

iqe-puptoo-plugin/iqe_puptoo/tests/test_plugin.py::test_plugin_accessible PASSED
```

## Authentication

To run tests, IQE must be provided with secrets, such as authentication credentials. The secret
enablement procedure is typical, and covered by the [iqe-docs credentials](https://insights-qe.pages.redhat.com/iqe-core-docs/configuration.html#credentials) guide.

In addition, IQE should be configured to talk to stage or prod. This can be done by setting the
``ENV_FOR_DYNACONF`` environment variable, as covered by the [iqe-docs configuration](https://insights-qe.pages.redhat.com/iqe-core-docs/configuration.html). If IQE
is configured to talk to stage, the internal Red Hat certificate must be installed, as covered by
the [iqe-docs prerequisites](https://insights-qe.pages.redhat.com/iqe-core-docs/tutorial/part3.html#prerequisites) guide.

To summarize:

```sh
# let IQE pull secrets from vault
export DYNACONF_IQE_VAULT_LOADER_ENABLED=true
export DYNACONF_IQE_VAULT_URL="https://vault.devshift.net/"
export DYNACONF_IQE_VAULT_VERIFY=true
export DYNACONF_IQE_VAULT_MOUNT_POINT="insights"
export DYNACONF_IQE_VAULT_OIDC_AUTH=1
```

## Running Tests

Assuming you have the environment set up correctly, the basic command to run the rest service tests looks like this:

```sh
ENV_FOR_DYNACONF=stage_proxy iqe tests plugin puptoo
```

## Markers

This section enumerates known markers and their meaning.

* `smoke` - Generically speaking, these are designated REST service "smoke" tests.
