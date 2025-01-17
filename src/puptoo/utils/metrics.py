from prometheus_client import Counter, Histogram, Summary

GET_FILE = Summary("puptoo_get_file_seconds", "Time spent retrieving file from S3")
EXTRACT = Summary(
    "puptoo_total_extraction_seconds", "Total time spent extracting facts"
)
SYSTEM_PROFILE = Summary(
    "puptoo_system_profile_seconds", "Total time spent extracting system profile"
)

# For messages processed for all services
msg_count = Counter(
    "puptoo_messages_consumed_total", "Total messages processed for all services"
)
msg_success_count = Counter(
    "puptoo_messages_consumed_success_total", "Total messages processed successfully for all services"
)

# For kafka message consume error counter, keep it for back compatibility
kafka_consume_msg_failure_count = Counter(
    "puptoo_messages_consume_failure_total", "Total messages that failed to be consumed"
)

# For advisor service archive unpacking
extraction_count = Counter(
    "puptoo_extractions_total", "Total archive extractions attempted"
)
extract_failure = Counter(
    "puptoo_failed_extractions_total", "Total archives that failed to extract"
)
extract_success = Counter(
    "puptoo_successful_extractions_total", "Total archives successfully extracted"
)

# For messages processed for advisor services only
msg_processed_count = Counter(
    "puptoo_messages_processed_total", "Total messages processed for advisor service"
)
msg_processed_failure = Counter(
    "puptoo_messages_processed_failure_total", "Total messages failed processed for advisor service"
)
msg_processed_success = Counter(
    "puptoo_messages_processed_success_total", "Total messages successful processed for advisor service"
)

msg_produced = Counter(
    "puptoo_messages_produced_total", "Total messages produced", ["topic"]
)
msg_send_failure = Counter(
    "puptoo_messages_produced_failure_total",
    "Total messages that failed to send",
    ["topic"],
)
msg_size_exceeded = Counter(
    "puptoo_max_extracted_size_exceeded_total",
    "Total archives with exceeded extracted size",
)

send_time = Histogram(
    "puptoo_message_send_time_seconds", "Total time spent sending a message"
)

msg_extraction_size = Histogram("puptoo_extraction_sizes", "Extracted archive sizes")
