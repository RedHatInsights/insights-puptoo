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
extract_failure = Counter(
    "puptoo_failed_extractions_total", "Total archives that failed to extract"
)
msg_processed = Counter(
    "puptoo_messages_processed_total", "Total messages successful process"
)
msg_produced = Counter("puptoo_messages_produced_total", "Total messages produced")
msg_send_failure = Counter(
    "puptoo_messages_failed_to_send_total", "Total messages that failed to send"
)

send_time = Histogram(
    "puptoo_message_send_time_seconds", "Total time spent sending a message"
)
