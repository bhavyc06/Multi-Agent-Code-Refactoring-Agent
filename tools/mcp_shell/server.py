from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess, os

app = FastAPI()
BASE = "/code"

class ExecReq(BaseModel):
    command: str
    workdir: str = "."

@app.post("/exec")
def exec_cmd(req: ExecReq):
    wd = os.path.abspath(os.path.join(BASE, req.workdir))
    if not wd.startswith(BASE):
        raise HTTPException(400, "Bad working directory")
    try:
        out = subprocess.check_output(
            req.command, cwd=wd, shell=True,
            stderr=subprocess.STDOUT, text=True, timeout=30
        )
        return {"output": out}
    except subprocess.CalledProcessError as e:
        return {"exit": e.returncode, "output": e.output[:400]}
