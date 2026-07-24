# IQE Test Environment Setup

Quick guide to setting up and running IQE tests for the puptoo service.

## Prerequisites

### 1. VPN and Certificates
- Connect to the Red Hat VPN
- Install [Red Hat certificates](https://source.redhat.com/groups/public/identity-access-management/it_iam_pki_rhcs_and_digicert/faqs_new_corporate_root_certificate_authority):
  ```bash
  # Add to ~/.bashrc or ~/.zshrc
  export REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt
  ```

### 2. Vault Access
Configure Vault for IQE credentials (add to `~/.bashrc` or `~/.zshrc`):
```bash
export DYNACONF_IQE_VAULT_LOADER_ENABLED=true
export DYNACONF_IQE_VAULT_URL="https://vault.devshift.net/"
export DYNACONF_IQE_VAULT_VERIFY=true
export DYNACONF_IQE_VAULT_MOUNT_POINT="insights"
export DYNACONF_IQE_VAULT_OIDC_AUTH="1"

# If not using Firefox or Kerberos locally:
export DYNACONF_IQE_VAULT_OIDC_HEADLESS="false"
```

**Important**: Ensure you have a user file in app-interface with `insights-qe` and `insights-engineers` roles. See [IQE documentation](https://insights-qe.pages.redhat.com/iqe-core-docs/configuration.html#getting-access) for details.

## Setup

### One-Time Setup
```bash
# From repository root (requires VPN for Nexus access)
uv --project iqe-insights-upload-processor sync --frozen
```

This installs all IQE dependencies and the local plugin in editable mode into
`iqe-insights-upload-processor/.venv/`.

### Activate IQE Environment
```bash
source iqe-insights-upload-processor/.venv/bin/activate
```

### IQE Dependency Update

The IQE dependencies mostly live in a Red Hat private Nexus repository.

To update them, run the following commands and push the changes to the lockfile as a PR.

```bash
uv --project iqe-insights-upload-processor lock
uv --project iqe-insights-upload-processor sync
```

Then commit the updated lockfile:
```bash
git add iqe-insights-upload-processor/uv.lock
```

## Running Tests

### Run Smoke Tests
```bash
ENV_FOR_DYNACONF=stage_proxy uv --project iqe-insights-upload-processor run \
    iqe tests plugin puptoo -m smoke
```

### Run All Tests
```bash
ENV_FOR_DYNACONF=stage_proxy uv --project iqe-insights-upload-processor run \
    iqe tests plugin puptoo
```

### Run a Specific Test
```bash
ENV_FOR_DYNACONF=stage_proxy uv --project iqe-insights-upload-processor run \
    iqe tests plugin puptoo -k test_plugin_accessible
```

### Environment Options
Change `ENV_FOR_DYNACONF` to test different environments:
- `stage_proxy` — Stage environment (default)
- `prod` — Production

## Running Tests in Ephemeral Environment

First, complete the [on-boarding](https://consoledot.pages.redhat.com/docs/dev/creating-a-new-app/using-ee/getting-started-with-ees.html) to the ephemeral environments.

Then follow these steps:

1. Reserve a namespace:
   ```bash
   NAMESPACE=$(bonfire namespace reserve -d 2)
   ```
2. Deploy puptoo to that namespace:
   ```bash
   bonfire deploy --source appsre --ref-env insights-stage ingress -n $NAMESPACE
   ```
3. Run the tests:
   ```bash
   POD=$(bonfire deploy-iqe-cji puptoo -m smoke -n $NAMESPACE)
   ```
4. View the live results:
   ```bash
   oc logs -n $NAMESPACE $POD -f
   ```

### Running Tests with Local Changes

To test local IQE plugin changes in an ephemeral environment, use the
`run_cji_with_local_plugin.sh` script. This deploys a debug CJI pod, copies
the local plugin into it, and runs the tests:

```bash
export NAMESPACE=$(bonfire namespace reserve -d 2)
bonfire deploy --source appsre --ref-env insights-stage ingress -n $NAMESPACE
export COMPONENT_NAME=puptoo
export IQE_LOCAL_PLUGIN_PATH="$PWD/iqe-insights-upload-processor"
export IMAGE_TAG=$(git rev-parse --short HEAD)
source run_cji_with_local_plugin.sh
```

## Troubleshooting

**Certificate errors during install:**
```bash
# Linux
sudo curl https://certs.corp.redhat.com/certs/Current-IT-Root-CAs.pem -o /etc/pki/ca-trust/source/anchors/Current-IT-Root-CAs.pem
sudo update-ca-trust

# macOS
cat `python -m certifi` > ~/bundle.crt
curl https://certs.corp.redhat.com/certs/Current-IT-Root-CAs.pem >> ~/bundle.crt
export REQUESTS_CA_BUNDLE=~/bundle.crt
```

**Plugin not found:**
Check installation:
```bash
uv --project iqe-insights-upload-processor run iqe plugin list
```

**Which environment am I in?**
```bash
which python
# .venv/bin/python                                    = main puptoo environment
# iqe-insights-upload-processor/.venv/bin/python       = IQE test environment
```

## Further Reading
- Full IQE plugin documentation: `iqe-insights-upload-processor/README.md`
- [IQE Core Documentation](https://insights-qe.pages.redhat.com/iqe-core-docs/)
