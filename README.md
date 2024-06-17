# Platform Upload Processor II

The Platform Upload Processor II (PUPTOO) is designed to recieve payloads for the `advisor` service
via the message queue, extract facts from the payload, forward the information to the inventory
service.

## Details

The PUPTOO service is a component of the Insights Platform that validates the payloads uploaded
to Red Hat by the insights-client. The service is engaged after an upload has been recieved and stored in
cloud storage.

PUPTOO retrieves payloads via URL in the message, processes it through
insights-core to extract facts and guarantee integrity of the archive, and send the extracted info to the inventory service.

The service runs in Openshift Dedicated.

## How it Works

![UML](https://www.plantuml.com/plantuml/png/VLDHRzem47xFhpXbZojPW81KX50VkacJfgbQrvUrLUGu1_7cs9bzfgCL_tss0m8s0G_8khllxllkljnOOePSAnCI917k7kxWpcYErWgrWazIloIeV6u3dMIqrARDN2SrgpEcb7QAuxdycabHCn9Q9PsV8RZec2BeN4TQ_mSIQkr3scooHbloiusdS09iAf7uVgnY5i6EEpGjKnwJd2CsMFIpPj3QLV9L4u8HguP0By-AcS5RoZZtRqfdCDyzGRcsGhEuUb8fPuGhpzEdKwwbH1uafZ6b5Q6YaZOTXZJhEYau2_aFQrLd1kk6KJQtQDQ2es8jBh93Z_UqUerzMYGMbAQUJPPjGyZWRuUMIb77nXMlXwDn4Qix8rHOaGo4kJC65SaDK8EWpGe-tqRQ_jc3v_qh1dT4GlIOKqo9rn0V3OjyE0a1P-A0XszVW3JK-aM5nSKnpF16h16MHhTmFuxuQbhuAVsL0ovSRLe0Agvhh66VYhKaMhJ4sYve6-MZqI2V38Rvz_nwDYncHPvDXkF9z3gV5Z_IRN9q-iTtbNJuV3ZqxOwMFU7qfEx7K3d-2odfAm-8Zt_8C4uMbk4_bk-nJ-f5K0D2sU0QE-3QOC8aWNMS1tU2_-txNJPoj62iFxLXZmwcqrvKT4gyRrsN0HtlktF2uriQAGPJRAzIkx64RTaPlHGIOt3x7ChtHCeZ5ysrdoWKawMdKVwqMYss2KgBNhMGpk2HbCDEptxF_wYHk3mLSycjXouXjHllhuggJYxlSB1eAj6Fll7LhfL_0G00 "PUPToo Processing Flow")

The PUP service workflow is as follows:

- Recieve a message from `platform.upload.advisor` topic in the MQ
- PUP downloads the archive from the url specified in the message
- Insights Core is engaged to open the tar file and extract the facts as determined by the `get_canonical_facts` method in insights-core
- During extraction it also runs a custom `system-profile` ruleset to extract more information about the ssytem
- PUP sends the result to inventory via the message queue

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

### Running

The default environment variables should be acceptable for testing.
PUPTOO does expect a kafka message queue to be available for connection.

#### Prerequisites

- python3

- optional:
  - [poetry](https://python-poetry.org/)

#### Python

Create a virtualenv using pipenv and install requirements. Once complete you can start the app by running `puptoo`

```sh
python -m venv path/to/venv
source path/to/venv/bin/activate
pip3 install .
```

#### Running Locally

Activate your virtual environment and run the validator

```sh
source path/to/venv/bin/activate
puptoo
```

#### Running with Docker Compose

Two docker-compose files are made available in this repo for standing up a local dev environment. The `docker-compose.yml` file stands up putoo, kafka, and minio for isolated tested. The `full-stack.yml` file stands up ingress, kafka, puptoo, minio, and inventory components so that the entire first bits of the platform pipeline can be tested.

Stand Up Isolated Puptoo

```sh
cd dev && sudo docker-compose up
```

Stand Up Full stack

```sh
cd dev && sudo docker-compose -f full-stack.yml up
```

**NOTE**: The full stack expects you to have an ingress and inventory image available. See those projects for steps for building the images needed. It's also typical for puptoo to fail to start if it can't initially connect to kafka. If this happens, simply run `sudo docker-compose -f full-stack.yml up -d pup` to have it attempt another startup.

#### Bonfire

Deploying with bonfire to an ephemeral environmnet is the preferred way to test puptoo. See the [bonfire documentation](https://clouddot.pages.redhat.com/docs/dev/getting-started/ephemeral/deploying.html) for more information.

## File Processing

The best way to test is by standing up this server and incorporating it with the upload-service. The [insights-upload](https://www.github.com/RedHatInsights/insights-upload) repo has a docker-compose that will get you most of the way there. Other details regarding
posting your archive to the service can be found in that readme.

This test assumes you have an inventory service available and ready to use. Visit the `insights-host-inventory` repo for those instructions.

## Testing System Profile

Occassionaly, an archive may be rejected by puptoo for a reason that is unclear. You may also see an archive that doens't seem to work properly or gathers the wrong information. In order to test this locally, you can use the `insights-run` tool to process the system-profile of that archive easily.

```sh
   poetry run insights-run -p src.puptoo ~/path/to/archive
```

This will print the system_profile so you can analyze it for issues.

### Testing with provided test-archive sample

Puptoo has a `dev/test-archives/core-base` folder that contains a test sample of insights-archive. It emulates a minimized set of files inside a real archive that required by the puptoo system-profile usage.

From this nature, this test-archive example can be used for system-profile QA Verification, and related tests.

Tar the provided test-archive example with:
```sh
$ tar -zcvf insights-puptoo-test-archive.tar.gz ./dev/test-archives/core-base
```

## Deployment

The PUPTOO service `master` branch has a webhook that notifies App-interface to build a new image within Jenkins. The image build will then trigger a redployment of the service in `ingress-stage`. In order to push to production, an app-interface PR should be created with the git ref for the image that should exist within `ingress-prod` on the Production cluster.

## Contributing

All outstanding issues or feature requests should be filed as Issues on this Github repo or within JIRA. PRs should be submitted against the master branch for any features or changes.

Any new system-profile items should include a test file inside `dev/test-archives/core-base`. This file should emulate the file that would be found
inside a real archive, and the test itself should be written and provided in the `tests` directory.

## Running unit tests

```sh
    ACG_CONFIG=./cdappconfig.json pytest
```

## Versioning

New functionality that may effect other services should increment by `1`. Minor features and bugfixes can increment by `0.0.1`

## Authors

- **Stephen Adams** - **Initial Work** - [SteveHNH](https://github.com/SteveHNH)
