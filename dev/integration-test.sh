#!/usr/bin/env bash
#
# Integration test for the full-stack dev environment.
# Waits for all services, injects test archives, and verifies results.
#
# Usage: ./dev/integration-test.sh [compose-file]
#
# Environment variables controlling QPC test behavior:
#   QPC_PROCESSING_ENABLED        (default: false)
#   QPC_HOSTS_TRANSFORMATION_ENABLED (default: false)
#   QPC_ORG_MIGRATION_ENABLED     (default: false)
#   QPC_ORG_MIGRATION_LIST        (default: empty)
#
# shellcheck disable=SC2016
set -euo pipefail

COMPOSE_FILE="${1:-dev/full-stack.yml}"
COMPOSE_DIR="$(dirname "${COMPOSE_FILE}")"

# Source the .env file used by podman compose so the script's expected
# behavior matches the container configuration. Only set vars that are
# not already defined, so explicit env vars (e.g. from CI) win.
if [ -f "${COMPOSE_DIR}/.env" ]; then
    while IFS='=' read -r key value; do
        [[ -z "${key}" || "${key}" =~ ^# ]] && continue
        key="${key%%[[:space:]]*}"
        value="${value#\"}"
        value="${value%\"}"
        if [ -z "${!key+x}" ]; then
            export "${key}=${value}"
        fi
    done < "${COMPOSE_DIR}/.env"
fi
B64_IDENTITY="eyJpZGVudGl0eSI6eyJvcmdfaWQiOiIwMDAwMDEiLCJhdXRoX3R5cGUiOiJiYXNpYy1hdXRoIiwidHlwZSI6IlVzZXIiLCJpbnRlcm5hbCI6eyJvcmdfaWQiOiIwMDAwMDEifSwidXNlciI6eyJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJpc19vcmdfYWRtaW4iOnRydWV9LCJzeXN0ZW0iOnsiY24iOiIxYjM2YjIwZi03ZmEwLTQ1NzEtYTEwOC04ZWI4MDYyMDRkYzAifX19"
INVENTORY_URL="http://localhost:8082/api/inventory/v1/hosts"

pass=0
fail=0
results=()

log()  { echo "==> $*"; }

section() {
    results+=("SECTION|$*")
}

ok() {
    echo "  PASS: $*"
    pass=$((pass + 1))
    results+=("PASS|$*")
}

fail() {
    echo "  FAIL: $*"
    fail=$((fail + 1))
    results+=("FAIL|$*")
}

# shellcheck disable=SC2317
get_host_count() {
    curl -sS -H "x-rh-identity: ${B64_IDENTITY}" "${INVENTORY_URL}" 2>/dev/null \
        | jq -r ".total // 0"
}

get_advisor_host_count() {
    curl -sS -H "x-rh-identity: ${B64_IDENTITY}" \
        "${INVENTORY_URL}?registered_with=puptoo" 2>/dev/null \
        | jq -r ".total // 0"
}

get_qpc_host_count() {
    curl -sS -H "x-rh-identity: ${B64_IDENTITY}" \
        "${INVENTORY_URL}?registered_with=!puptoo" 2>/dev/null \
        | jq -r ".total // 0"
}

get_topic_offset() {
    podman exec puptoo-kafka kafka-get-offsets \
        --bootstrap-server localhost:29092 --topic "$1" 2>/dev/null \
        | awk -F: '{print $NF}'
}

delete_all_hosts() {
    local host_ids=""
    local filter
    for filter in "registered_with=puptoo" "registered_with=!puptoo"; do
        local ids
        ids=$(curl -sS -H "x-rh-identity: ${B64_IDENTITY}" \
            "${INVENTORY_URL}?per_page=100&${filter}" 2>/dev/null \
            | jq -r '[(.results // [])[].id] | join(",")')
        if [ -n "${ids}" ]; then
            host_ids="${host_ids:+${host_ids},}${ids}"
        fi
    done
    if [ -n "${host_ids}" ]; then
        log "Deleting existing hosts: ${host_ids}"
        curl -sS -X DELETE -H "x-rh-identity: ${B64_IDENTITY}" \
            "${INVENTORY_URL}/${host_ids}" 2>/dev/null | jq .
        local remaining
        remaining=$(curl -sS -H "x-rh-identity: ${B64_IDENTITY}" \
            "${INVENTORY_URL}" 2>/dev/null | jq -r ".total // 0")
        if [ "${remaining}" -eq 0 ]; then
            ok "all hosts deleted (inventory empty)"
        else
            fail "hosts remain in inventory after deletion (${remaining} left)"
        fi
    else
        log "No existing hosts to delete"
    fi
}

print_summary() {
    local width=60
    local scenario_len=$((${#SCENARIO} + 14))
    if [ "${scenario_len}" -gt "${width}" ]; then width=${scenario_len}; fi
    for r in "${results[@]}"; do
        local desc="${r#*|}"
        local len=$((${#desc} + 8))
        if [ "${len}" -gt "${width}" ]; then width=${len}; fi
    done

    local sep
    sep=$(printf '%*s' "${width}" '' | tr ' ' '=')

    echo ""
    echo "${sep}"
    echo "  Scenario: ${SCENARIO}"
    echo "${sep}"
    for r in "${results[@]}"; do
        local tag="${r%%|*}"
        local desc="${r#*|}"
        case "${tag}" in
            SECTION)
                echo ""
                echo "  ${desc}"
                ;;
            PASS)
                printf "    \033[32m✓\033[0m  %s\n" "${desc}"
                ;;
            FAIL)
                printf "    \033[31m✗\033[0m  %s\n" "${desc}"
                ;;
        esac
    done
    echo ""
    echo "${sep}"
    if [ "${fail}" -eq 0 ]; then
        printf "  Result: \033[32m%d passed\033[0m, %d failed\n" "${pass}" "${fail}"
    else
        printf "  Result: %d passed, \033[31m%d failed\033[0m\n" "${pass}" "${fail}"
    fi
    echo "${sep}"
}

# ---------------------------------------------------------------------------
# 1. Wait for services
# ---------------------------------------------------------------------------
wait_for() {
    local name="$1" url="$2" timeout_s="${3:-180}"
    log "Waiting for ${name} (${url}) ..."
    if timeout "${timeout_s}" bash -c '
        until curl -sf "'"${url}"'" >/dev/null 2>&1; do sleep 5; done
    '; then
        ok "${name} is healthy"
    else
        fail "${name} did not become healthy within ${timeout_s}s"
    fi
}

wait_for_container() {
    local name="$1" check_cmd="$2" timeout_s="${3:-180}"
    log "Waiting for ${name} ..."
    if timeout "${timeout_s}" bash -c "${check_cmd}"; then
        ok "${name} is healthy"
    else
        fail "${name} did not become healthy within ${timeout_s}s"
    fi
}

section "Services"
wait_for "puptoo"      "http://localhost:8000/" 180
wait_for "puptoo-qpc"  "http://localhost:8001/" 180
wait_for "ingress"     "http://localhost:8080/" 120

wait_for_container "kafka" \
    'until podman exec puptoo-kafka kafka-broker-api-versions --bootstrap-server localhost:29092 >/dev/null 2>&1; do sleep 5; done' \
    120

log "Kafka topics:"
podman exec puptoo-kafka kafka-topics --bootstrap-server localhost:29092 --list 2>/dev/null | sort | while read -r topic; do
    echo "  - ${topic}"
done

wait_for_container "db-host-inventory" \
    'until podman exec puptoo-db pg_isready -U insights -d insights >/dev/null 2>&1; do sleep 5; done' \
    120

wait_for_container "inventory-mq" \
    'until podman exec puptoo-inventory-mq test -f /tmp/.db-migrated 2>/dev/null; do sleep 5; done' \
    180

wait_for_container "inventory-mq consumer group" \
    'until podman exec puptoo-kafka kafka-consumer-groups --bootstrap-server localhost:29092 --list 2>/dev/null | grep -q inventory; do sleep 5; done' \
    120

log "Waiting for inventory-web ..."
if timeout 180 bash -c '
    until curl -sf \
        -H "x-rh-identity: '"${B64_IDENTITY}"'" \
        '"${INVENTORY_URL}"' 2>&1 | grep -q "total"; do
        sleep 5
    done
'; then
    ok "inventory-web is healthy"
else
    fail "inventory-web did not become healthy within 180s"
fi

podman compose -f "${COMPOSE_FILE}" ps

# Verify each container's INVENTORY_TOPIC is configured
PUPTOO_TOPIC=$(podman exec puptoo printenv INVENTORY_TOPIC 2>/dev/null)
QPC_TOPIC=$(podman exec puptoo-qpc printenv INVENTORY_TOPIC 2>/dev/null)

if [ -n "${PUPTOO_TOPIC}" ]; then
    ok "puptoo INVENTORY_TOPIC is set (${PUPTOO_TOPIC})"
else
    fail "puptoo INVENTORY_TOPIC is not set"
fi

if [ -n "${QPC_TOPIC}" ]; then
    ok "puptoo-qpc INVENTORY_TOPIC is set (${QPC_TOPIC})"
else
    fail "puptoo-qpc INVENTORY_TOPIC is not set"
fi

# ---------------------------------------------------------------------------
# 2. Clean slate — delete all existing hosts
# ---------------------------------------------------------------------------
delete_all_hosts

# ---------------------------------------------------------------------------
# 3. Inject advisor archive and verify host ingestion
# ---------------------------------------------------------------------------
section "Advisor pipeline"
advisor_offset_before=$(get_topic_offset "${PUPTOO_TOPIC}")
log "Injecting advisor archive ..."
if make inject ARCHIVE=dev/test-archives/rhel94_core_collect.tar.gz; then
    ok "advisor archive accepted by ingress"
else
    fail "advisor archive injection failed"
fi

log "Waiting for advisor hosts to appear in inventory ..."
if timeout 120 bash -c '
    while true; do
        count=$(curl -sS \
            -H "x-rh-identity: '"${B64_IDENTITY}"'" \
            '"${INVENTORY_URL}"'?registered_with=puptoo 2>/dev/null | jq -r ".total // 0")
        echo "  Advisor hosts found: ${count}"
        if [ "${count}" -gt 0 ]; then break; fi
        sleep 5
    done
'; then
    advisor_count=$(get_advisor_host_count)
    ok "advisor hosts ingested into inventory (count: ${advisor_count})"

    advisor_offset_after=$(get_topic_offset "${PUPTOO_TOPIC}")
    if [ "${advisor_offset_after}" -gt "${advisor_offset_before}" ]; then
        ok "puptoo produced to ${PUPTOO_TOPIC} (offset: ${advisor_offset_before} -> ${advisor_offset_after})"
    else
        fail "no new messages on ${PUPTOO_TOPIC} after advisor injection (offset: ${advisor_offset_before})"
    fi

    log "Re-injecting same advisor archive to check for duplicates ..."
    make inject ARCHIVE=dev/test-archives/rhel94_core_collect.tar.gz >/dev/null 2>&1
    sleep 10
    advisor_recount=$(get_advisor_host_count)
    if [ "${advisor_recount}" -eq "${advisor_count}" ]; then
        ok "no duplicate advisor hosts on re-injection (count: ${advisor_recount})"
    else
        fail "duplicate advisor hosts created on re-injection (${advisor_count} -> ${advisor_recount})"
    fi
else
    fail "advisor hosts did not appear in inventory within 120s"
fi

# ---------------------------------------------------------------------------
# 4. Inject QPC archive and verify based on feature flags
# ---------------------------------------------------------------------------
section "QPC pipeline"
QPC_ENABLED="${QPC_PROCESSING_ENABLED:-false}"
QPC_TRANSFORM="${QPC_HOSTS_TRANSFORMATION_ENABLED:-false}"
QPC_ORG_MIG="${QPC_ORG_MIGRATION_ENABLED:-false}"
QPC_ORG_LIST="${QPC_ORG_MIGRATION_LIST:-}"

# Determine scenario description from flags
if [ "${QPC_ENABLED}" != "true" ]; then
    SCENARIO="QPC disabled (all flags false)"
elif [ "${QPC_ORG_MIG}" = "true" ] && [ -n "${QPC_ORG_LIST}" ]; then
    if echo ",${QPC_ORG_LIST}," | grep -q ",000001,"; then
        SCENARIO="QPC + org migration (matching org: ${QPC_ORG_LIST})"
    else
        SCENARIO="QPC + org migration (non-matching org: ${QPC_ORG_LIST})"
    fi
else
    SCENARIO="QPC enabled (processing + transformation)"
fi

log "Scenario: ${SCENARIO}"

pre_qpc_advisor_count=$(get_advisor_host_count)
pre_qpc_qpc_count=$(get_qpc_host_count)
log "Host counts before QPC injection: advisor=${pre_qpc_advisor_count}, qpc=${pre_qpc_qpc_count}"
log "QPC_PROCESSING_ENABLED=${QPC_ENABLED}"
log "QPC_HOSTS_TRANSFORMATION_ENABLED=${QPC_TRANSFORM}"
log "QPC_ORG_MIGRATION_ENABLED=${QPC_ORG_MIG}"
log "QPC_ORG_MIGRATION_LIST=${QPC_ORG_LIST}"

qpc_offset_before=$(get_topic_offset "${QPC_TOPIC}")
log "Injecting QPC archive ..."
if make inject KIND=qpc ARCHIVE=dev/test-archives/qpc/report_sat_6_7_5.tar.gz; then
    ok "QPC archive accepted by ingress"
else
    fail "QPC archive injection failed"
fi

# Determine expected outcome:
#   - QPC disabled                         -> skipped (processing disabled)
#   - QPC enabled + org migration filters  -> skipped (org not in list)
#   - QPC enabled + no migration filter    -> hosts created
#   - QPC enabled + org in migration list  -> hosts created
qpc_should_create_hosts=false
if [ "${QPC_ENABLED}" = "true" ]; then
    if [ "${QPC_ORG_MIG}" = "true" ] && [ -n "${QPC_ORG_LIST}" ]; then
        if echo ",${QPC_ORG_LIST}," | grep -q ",000001,"; then
            qpc_should_create_hosts=true
        fi
    else
        qpc_should_create_hosts=true
    fi
fi

if [ "${qpc_should_create_hosts}" = "true" ]; then
    # --- QPC hosts should be processed and created in inventory ---
    log "Waiting for QPC hosts to appear in inventory ..."
    if timeout 120 bash -c '
        while true; do
            count=$(curl -sS \
                -H "x-rh-identity: '"${B64_IDENTITY}"'" \
                '"${INVENTORY_URL}"'"?registered_with=!puptoo" 2>/dev/null | jq -r ".total // 0")
            echo "  QPC hosts found: ${count}"
            if [ "${count}" -gt 0 ]; then break; fi
            sleep 5
        done
    '; then
        post_qpc_count=$(get_qpc_host_count)
        post_advisor_count=$(get_advisor_host_count)
        ok "QPC hosts ingested into inventory (qpc: ${post_qpc_count}, advisor: ${post_advisor_count})"

        qpc_offset_after=$(get_topic_offset "${QPC_TOPIC}")
        if [ "${qpc_offset_after}" -gt "${qpc_offset_before}" ]; then
            ok "puptoo-qpc produced to ${QPC_TOPIC} (offset: ${qpc_offset_before} -> ${qpc_offset_after})"
        else
            fail "no new messages on ${QPC_TOPIC} after QPC injection (offset: ${qpc_offset_before})"
        fi
    else
        fail "QPC hosts did not appear in inventory within 120s"
    fi

    log "Re-injecting same QPC archive to check for duplicates ..."
    make inject KIND=qpc ARCHIVE=dev/test-archives/qpc/report_sat_6_7_5.tar.gz >/dev/null 2>&1
    sleep 10
    qpc_recount=$(get_qpc_host_count)
    if [ "${qpc_recount}" -eq "${post_qpc_count}" ]; then
        ok "no duplicate QPC hosts on re-injection (count: ${qpc_recount})"
    else
        fail "duplicate QPC hosts created on re-injection (${post_qpc_count} -> ${qpc_recount})"
    fi

elif [ "${QPC_ENABLED}" != "true" ]; then
    # --- QPC processing disabled: verify skip log ---
    log "Checking puptoo-qpc logs for processing-disabled message ..."
    if timeout 60 bash -c '
        until podman compose -f "'"${COMPOSE_FILE}"'" logs puptoo-qpc 2>&1 | \
            grep -q "QPC processing disabled by feature flag"; do
            sleep 5
        done
    '; then
        ok "QPC processing was skipped (feature flag disabled)"
    else
        fail "skip message not found in puptoo-qpc logs"
    fi

    post_qpc_count=$(get_qpc_host_count)
    log "Host counts after QPC injection: qpc=${post_qpc_count}"
    if [ "${post_qpc_count}" -eq "${pre_qpc_qpc_count}" ]; then
        ok "no new QPC hosts created (qpc: ${post_qpc_count})"
    else
        fail "QPC injection created hosts despite QPC_PROCESSING_ENABLED=false (qpc: ${pre_qpc_qpc_count} -> ${post_qpc_count})"
    fi

else
    # --- QPC enabled but org migration filters out the archive ---
    log "Checking puptoo-qpc logs for org migration skip message ..."
    if timeout 60 bash -c '
        until podman compose -f "'"${COMPOSE_FILE}"'" logs puptoo-qpc 2>&1 | \
            grep -q "org_id=000001 is not in the allowed list"; do
            sleep 5
        done
    '; then
        ok "QPC archive skipped by org migration filter"
    else
        fail "org migration skip message not found in puptoo-qpc logs"
    fi

    post_qpc_count=$(get_qpc_host_count)
    log "Host counts after QPC injection: qpc=${post_qpc_count}"
    if [ "${post_qpc_count}" -eq "${pre_qpc_qpc_count}" ]; then
        ok "no new QPC hosts created (org filtered, qpc: ${post_qpc_count})"
    else
        fail "QPC injection created hosts despite org not in migration list (qpc: ${pre_qpc_qpc_count} -> ${post_qpc_count})"
    fi
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print_summary
exit "${fail}"
