import json, hashlib, time

def log(report):
    payload = json.dumps(report, sort_keys=True).encode()
    h = hashlib.sha256(payload).hexdigest()
    record = {
        "hash": h,
        "timestamp": int(time.time()),
        "report": report
    }
    return record
