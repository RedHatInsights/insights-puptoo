# RHSM raw host record v1

This contract defines host records sent by Errata Notifications (EN, producer)
to insights-upload-processor (consumer) for mapping to HBI `add_host` messages.

## Transport and naming

- One UTF-8 JSON object per host, as the value of one Kafka message.
- Path: EN -> IT Kafka -> rhsm-system-profile-bridge -> HCC Kafka -> upload-processor.
  The bridge copies the value and headers and sets the outgoing key from the `org_id` header.
- Incoming Kafka key: the record's `org_id`.
- Everything under `consumer` is raw data forwarded from Candlepin (filtered by an allow-list).

EN sends the `org_id` Kafka header with UTF-8 value, the upload-processor uses this header to
set the Kafka key on its outgoing messages to HBI. EN can send other Kafka headers which
won't be used by the insights-upload-processor.

## Record envelope

| Field | Type / presence | Meaning |
|---|---|---|
| `schema_version` | Required integer | Record-format version. Unsupported versions are rejected; a boolean is not an integer here. |
| `platform_metadata` | Required object | Contains the required `request_id` string. No identity credentials. |
| `platform_metadata.request_id` | Required UUID string | EN-generated correlation ID, reused by the bridge, upload-processor, HBI, and any attached reference message. |
| `org_id` | Required nonempty string | Must exactly equal `consumer.owner.key`; do not coerce to an integer or strip leading zeroes. |
| `reporter` | Required nonempty string | HBI reporter attribution, copied unchanged to `add_host.data.reporter`. EN sends `rhsm-system-profile-bridge`. |
| `trigger` | Required string | One of `created`, `modified`, `bulk_migration`, `bulk_modification`, `heartbeat`, `system_profile_upload`. Used for logs/metrics only; does not select a different mapping. |
| `observed_at` | Required RFC 3339 timestamp string with an offset | When EN fetched this consumer snapshot, not the original event time or profile-upload time. Logs/latency only. |
| `set_display_name` | Required boolean | Whether to copy `consumer.name` into HBI's display name. EN makes this stateful decision. |
| `consumer` | Required object | The allow-listed projection of the fetched Candlepin consumer. |
| `profile` | Optional object | Available stored package/module/reported-repository data and EN-resolved repositories. Omit when unavailable. Each member is independently optional. |
| `shadow` | Optional boolean, default `false` | `true` unconditionally forbids publication to HBI. See [shadow processing](shadow-mode.md). |
| `legacy_add_host` | Optional object, only with `shadow: true` | A serialized EN `add_host` reference message for the same update. Omit when no message was built. |

## Data availability: absent is not empty

Since `consumer` is just forwarded data from Candlepin,
we can only make sure these rules apply for `profile` subfields.
However, EN's Consumer object defaults shouldn't manufacture empty
fields, if those fields are omitted from Candlepin's ConsumerDTO.

| Representation | Meaning |
|---|---|
| Property absent | The data is unavailable, was not collected/requested, or collection failed. Do not infer a value or a deletion. |
| Property present with `null`, `[]`, or `""` | The data was collected and is explicitly empty, using the source field's empty representation. |
| Property present with a populated value | The data was collected and has that value. |

This distinction should be preserved recursively. Within an object, absent children means unavailable;
the presence of the parent does not make every possible child known. For example,
`profile: {}` supplies no package, module, or repository observations and must not
be expanded into four empty collections.

## Forwarding allow-list for `consumer`

EN manages the forwarding allow-list. Changes require coordinated contract,
producer/consumer, and example updates.

### Whole consumer fields

```text
uuid
name
owner
releaseVer
environments
installedProducts
facts
```

When available, all subfields and collection entries of a forwarded field are
retained as supplied by Candlepin in the EN's `Consumer` object,
except that `facts` is filtered separately. Fields outside the list are excluded even when empty.
Timestamp strings under `consumer` retain Candlepin's format (for example,
`2026-11-12T08:00:00+0000`). The envelope's `observed_at` is separately generated
by EN and uses RFC 3339.

### Consumer facts sub-fields

**Namespaces**, including all their dotted subfields:

```text
distribution
network
dmi
net
openshift
uname
lscpu
bootc
```

**Exact scalar fields**:

```text
insights_id
google_instance_id
gcp_instance_id
azure_instance_id
aws_instance_id
```

For a namespace `N`, a flat fact key is forwarded if it starts with `N + "."`.
`uname.machine` is forwarded, but `uname_extra.machine` is not.
Scalar keys require exact equality. `google_instance_id` is retained because EN's
existing `add_host` mapping reads that key to populate the GCP provider ID.
It is not the fact name produced by subscription-manager's GCP collector:
the collector reports `gcp_instance_id`, so that key is forwarded as well.

## Profile data

`profile` is separate from ConsumerDTO. EN supplies available data from its stored
profile and repository resolution. All four members are optional.
If data for any member is unavailable, omit it.
An explicit null or empty array means that member was collected and is empty.

| Field | Populated value | Meaning |
|---|---|---|
| `packages` | Array of RPM objects with `name`, `epoch`, `version`, `release`, `arch` | Package inventory; epoch is a JSON integer, not a string. |
| `modules` | Array of module objects with `name`, `stream`, `status`, `active` and available metadata | Module data may also include `version`, `context`, `arch`, `profiles`, `installed_profiles`. `active` can be absent on sources that report only status. |
| `reported_repositories` | Array of strings | Repository IDs reported by subscription-manager. |
| `repositories` | Array of objects with `name`, `content_set_label`, and any available `pulp_id` | EN-resolved repositories; reported repository IDs are not a replacement for resolution results. |

For example, successful repository resolution returning no repositories is
`"repositories": []`; unavailable/failed resolution is represented by omitting
`repositories`, not by sending an empty array. A repository-only profile need not
include packages or modules. Presence of `profile` is not evidence that all of its
members were collected. Consumer-only records can omit the `profile` object.

## Facts reference and future extensions

Subscription-manager's built-in fact collectors are in
[`rhsmlib/facts` on GitHub](https://github.com/candlepin/subscription-manager/tree/main/src/rhsmlib/facts),
especially [`AllFactsCollector`](https://github.com/candlepin/subscription-manager/blob/main/src/rhsmlib/facts/all.py).
Some names are dynamic (interfaces, DMI, lscpu, proc_cpuinfo), so this is not a
closed list guaranteed on every machine. Plugins, `/etc/rhsm/facts/*.facts`, other
RHSM producers, and client versions can supply additional facts, including names
inside an allowed namespace.

The consumer references below include illustrative facts outside the allow-list,
such as `cpu.*`, `memory.*`, `virt.*`, `system.*` and AWS account/region data. They
show potentially accessible data. To use additional facts to populate more HBI fields
we need to extend the allow-list with the new facts.

## Contract and examples

- [Profile record](examples/v1/profile.json): consumer plus packages, modules, and
  repositories; includes architecture and bootc facts.
- [Consumer-only record](examples/v1/consumer-only.json): a heartbeat with populated
  release, environment, and installed-product data; demonstrates the architecture
  fallback and `i686` to `i386` normalization.
- [Shadow record with a reference message](examples/v1/shadow-with-legacy.json):
  populated consumer and all four profile fields, plus the corresponding EN
  `add_host` message.
- [Shadow record without a reference message](examples/v1/shadow-without-legacy.json):
  no package used by EN's architecture heuristic, so EN skips repository
  resolution and does not build a legacy message. The record still carries the
  reported repository IDs, and upload-processor can derive architecture from facts.

Every example is synthetic. See [shadow processing](shadow-mode.md)
for comparison rules and publication safeguards. Shadow records must never be
published to HBI.

## Consumer references, not wire records

These two JSON files show different representations of the same synthetic host:

1. [Candlepin API ConsumerDTO](reference/consumer-dto-api.example.json), before
   the allow-list, with credential contents replaced by placeholders. Its shape
   follows the [Candlepin 5.0.2 API schema](https://github.com/candlepin/candlepin/blob/58038c1443ec11dd4c55e10a2074cc745db756fc/api/candlepin-api-spec.yaml#L9061-L9279).
   Fields can vary by API version; for example, newer schemas omit `canActivate`.
2. [Serialized EN internal Consumer](reference/en-consumer.example.json), after
   `Consumers.fromConsumerDTO()`, also before the allow-list. This illustrates EN's
   internal model, not the generated API DTO or an HBI message.

Neither reference is a valid raw host record or a production capture. They show
potentially accessible data for additional mappings.
