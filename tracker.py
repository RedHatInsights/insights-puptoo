import datetime

from utils import config

def get_time():
    return datetime.datetime.now().isoformat()

def tracker_msg(extra, status, status_msg):

    message = {"account": extra["account"],
               "request_id": extra["request_id"],
               "payload_id": extra["request_id"],
               "service": "puptoo",
               "status": status,
               "status_msg": status_msg,
               "date": get_time()
               }

    return {"topic": config.TRACKER_TOPIC, "msg": message, "extra": extra}
