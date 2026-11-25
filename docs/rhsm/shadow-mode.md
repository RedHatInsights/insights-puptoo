# RHSM shadow processing

This diagnostic mode uses the [v1 raw host record](README.md) to compare
an insights-upload-processor candidate with an EN-built reference message, without
publishing the candidate to HBI.

## Input and publication safeguards

EN sends a raw record for every host passing its producer-side eligibility filters
(anonymous org, non-existing consumer, inactive consumer, invalid consumer type)
and sets `shadow: true`. If EN built an `add_host` reference for that update, it
attaches the exact serialized message as `legacy_add_host`. Otherwise
(in cases when the legacy EN workflow wouldn't send `add_host` message to HBI
but it still sends message to the upload-processor, like when the host is an
OpenShift cluster, or it has unsupported OS), it omits
that field; it does not fabricate a message or use null as an attachment.

**Upload-processor never publishes a record with `shadow: true`, regardless of
deployment flags or whether `legacy_add_host` is present.** It also defensively
prohibits publication of records carrying `legacy_add_host`. A global publishing
disable suppresses all output. Comparison results cannot override these guards.

## Comparing outcomes

| Reference attachment | Upload-processor outcome | Comparison |
|---|---|---|
| Present | Builds | Compare messages using only the fixed normalizations below. |
| Present | Drops | Mismatch. |
| Absent | Builds | Mismatch unless this is the profile/package-architecture case below. |
| Absent | Drops | Match - both paths dropped |

## Fixed comparison rules

These are not configurable tolerances. `SP` below means `data.system_profile`.

1. An added `SP.arch` on a consumer-only candidate is an expected difference from
   a reference that has no architecture (because of a change in how architecture is
   determined - from packages vs. from RHSM facts). A profile architecture value differing
   from its reference remains a mismatch.
2. Ignore `data.stale_timestamp` in the reference; upload-processor does not produce it.
3. Top-level `operation_args: {}` and absent `operation_args` are equivalent.
4. List order is irrelevant. Ignore ordering, not duplicate counts.

Anything else is a mismatch. In particular, do not normalize absent data to null
or an empty collection. A reference containing an empty list and a candidate
omitting that field are different observations, not an ordering difference or an
additional comparison exception.
