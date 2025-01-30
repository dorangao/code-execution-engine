import os

from flask import Flask, request, jsonify, send_from_directory
from redis import Redis
from rq import Queue
from worker import execute_code
from history_tracker import get_execution_history

app = Flask(__name__)
redis_conn = Redis(host="redis", port=6379)
q = Queue("code_execution", connection=redis_conn)

@app.route("/")
def index():
    return send_from_directory(os.path.join(app.root_path, 'ui'), 'index.html')

@app.route("/execute", methods=["POST"])
def execute():
    data = request.get_json()
    job = q.enqueue(execute_code, data["code"], data["language"])
    return jsonify({"job_id": job.get_id()}), 200

@app.route("/result/<job_id>", methods=["GET"])
def get_result(job_id):
    from rq.job import Job
    job = Job.fetch(job_id, connection=redis_conn)
    return jsonify(job.result if job.is_finished else {"status": "queued"})

@app.route("/history", methods=["GET"])
def history():
    return jsonify(get_execution_history()), 200

@app.route("/ui/<path:path>")
def send_ui(path):
    return send_from_directory(os.path.join(app.root_path, 'ui'), path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)