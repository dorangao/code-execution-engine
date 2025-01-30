import os
import uuid
import tarfile
import io
import docker
from redis import Redis
from rq import Queue, Worker
from history_tracker import log_execution


redis_conn = Redis(host=os.environ.get("REDIS_HOST", "redis"), port=6379)


def create_tar(file_name: str, file_content: str) -> bytes:
    tar_stream = io.BytesIO()
    with tarfile.TarFile(fileobj=tar_stream, mode="w") as tar:
        tarinfo = tarfile.TarInfo(name=file_name)
        tarinfo.size = len(file_content.encode("utf-8"))
        tar.addfile(tarinfo, io.BytesIO(file_content.encode("utf-8")))
    tar_stream.seek(0)
    return tar_stream.getvalue()


def execute_code(code: str, language: str) -> dict:
    file_ext = {"python": "py", "javascript": "js", "java": "java", "php": "php"}[language]
    filename = f"temp_{uuid.uuid4()}.{file_ext}"
    docker_image = {"python": "code_executor_python", "javascript": "code_executor_node",
                    "java": "code_executor_java", "php": "code_executor_php"}[language]

    client = docker.from_env()
    container = client.containers.run(image=docker_image, command="tail -f /dev/null", detach=True, tty=True,
                                      stdin_open=True)

    tar_data = create_tar(filename, code)
    container.put_archive("/tmp", tar_data)

    run_cmd = {"python": f"python /tmp/{filename}", "javascript": f"node /tmp/{filename}",
               "java": f"java /tmp/{filename}", "php": f"php /tmp/{filename}"}[language]

    output = container.exec_run(run_cmd).output.decode("utf-8")
    container.stop()
    container.remove()

    log_execution(code, language, output)
    return {"output": output, "status": "success"}


def run_worker():
    q = Queue("code_execution", connection=redis_conn)
    Worker([q]).work()


if __name__ == "__main__":
    run_worker()