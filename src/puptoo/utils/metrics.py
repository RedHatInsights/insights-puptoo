from prometheus_client import Counter, Histogram, Summary

GET_FILE = Summary("puptoo_get_file_seconds", "Time spent retrieving file from S3")
EXTRACT = Summary(
    "puptoo_total_extraction_seconds", "Total time spent extracting facts"
)
SYSTEM_PROFILE = Summary(
    "puptoo_system_profile_seconds", "Total time spent extracting system profile"
)

msg_count = Counter(
    "puptoo_messages_consumed_total", "Total messages consumed from the kafka topic"
)
failed_msg_count = Counter(
    "puptoo_messages_consume_failure_total", "Total messages that failed to be consumed"
)
extraction_count = Counter(
    "puptoo_extractions_total", "Total archive extractions attempted"
)
extract_failure = Counter(
    "puptoo_failed_extractions_total", "Total archives that failed to extract"
)
extract_success = Counter(
    "puptoo_successful_extractions_total", "Total archives successfully extracted"
)
msg_processed = Counter(
    "puptoo_messages_processed_total", "Total messages successful process"
)
msg_produced = Counter(
    "puptoo_messages_produced_total", "Total messages produced", ["topic"]
)
msg_send_failure = Counter(
    "puptoo_messages_produced_failure_total", "Total messages that failed to send", ["topic"]
)

send_time = Histogram(
    "puptoo_message_send_time_seconds", "Total time spent sending a message"
)
