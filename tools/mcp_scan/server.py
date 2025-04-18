from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess, os, tempfile, json

app = FastAPI()
BASE = "/code"

class ScanReq(BaseModel):
    path: str = "."

@app.post("/scan")
def bandit_scan(req: ScanReq):
    tgt = os.path.abspath(os.path.join(BASE, req.path))
    if not tgt.startswith(BASE):
        raise HTTPException(400, "Bad path")
    out = tempfile.mktemp(suffix=".json")
    cmd = f"bandit -r {tgt} -f json -o {out}"
    subprocess.run(cmd, shell=True, capture_output=True)
    try:
        data = json.load(open(out))
    except Exception:
        raise HTTPException(500, "Scan failed")
    return data
