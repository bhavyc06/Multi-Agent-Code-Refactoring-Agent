# backend/main.py
import os, uuid, sys, io, shutil, redis, logfire
from fastapi import FastAPI
from pydantic import BaseModel
from crew_agents import build

# Configure Logfire (traces appear in your dashboard)
logfire.configure()

app = FastAPI()
WORK = "/app/code"
os.makedirs(WORK, exist_ok=True)

@app.get("/healthz", tags=["meta"])
def healthz():
    """Kubernetes‑style liveness probe."""
    return {"status": "ok"}


redis_cli = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

class RefactorRequest(BaseModel):
    code: str
    filename: str = "snippet.py"

@app.post("/refactor")
def refactor(req: RefactorRequest):
    # 1) Save the snippet to disk
    sid = uuid.uuid4().hex[:8]
    fname = f"{sid}_{req.filename}"
    path = os.path.join(WORK, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(req.code)

    # 2) Build & run the CrewAI pipeline, capturing console logs
    crew = build(path)
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf

    with logfire.span("crew_run", attributes={"session": sid}):
        result = crew.kickoff()

    sys.stdout = old_stdout
    logs = buf.getvalue()

    # 3) Persist outputs (optional, for retrieval by session)
    redis_cli.hset(sid, mapping=result)

    # 4) Return session, logs, and each task output
    return {
        "session": sid,
        "logs": logs,
        **result
    }
