from redis import Redis
import json
import time

redis_conn = Redis(host="redis", port=6379)

def log_execution(code, language, output):
    entry = {
        "timestamp": time.time(),
        "language": language,
        "code": code,
        "output": output
    }
    redis_conn.rpush("execution_history", json.dumps(entry))

def get_execution_history():
    history = redis_conn.lrange("execution_history", 0, -1)
    return [json.loads(entry) for entry in history]