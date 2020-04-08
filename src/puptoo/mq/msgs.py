import datetime


def get_time():
    return datetime.datetime.now().isoformat()


def inv_message(operation, data, metadata):
    message = {"operation": operation, "data": data, "platform_metadata": metadata}

    message["data"]["account"] = metadata.get("account")

    return message


def tracker_message(extra, status, status_msg):

    message = {
        "account": extra["account"],
        "request_id": extra["request_id"],
        "payload_id": extra["request_id"],
        "service": "puptoo",
        "status": status,
        "status_msg": status_msg,
        "date": get_time(),
    }

    return message


def validation_message(msg, facts, result):

    data = {**msg, **facts}
    message = {"validation": result, **data}

    return message
