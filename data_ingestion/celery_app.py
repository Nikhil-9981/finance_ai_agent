from celery import Celery
import subprocess
from .celeryconfig import beat_schedule

app = Celery(
    "data_ingestion",  # match folder/module name!
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)
app.conf.beat_schedule = beat_schedule
app.conf.timezone = "Asia/Kolkata"

@app.task
def rebuild_faiss_index():
    docs_folder = "data_ingestion/docs"
    index_path = "data_ingestion/faiss_index"
    result = subprocess.run(
        ["python3", "data_ingestion/build_faiss.py", "--docs_folder", docs_folder, "--index_path", index_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"FAISS index rebuild failed: {result.stderr}")
    return f"FAISS index rebuilt: {result.stdout}"
