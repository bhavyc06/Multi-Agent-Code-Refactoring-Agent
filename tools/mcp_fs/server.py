from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

app = FastAPI()
BASE = "/code"

class ReadReq(BaseModel):
    path: str

class WriteReq(BaseModel):
    path: str
    content: str

class ListReq(BaseModel):
    path: str = "."

@app.post("/read")
def read_file(req: ReadReq):
    full = os.path.abspath(os.path.join(BASE, req.path))
    if not full.startswith(BASE):
        raise HTTPException(400, "Bad path")
    try:
        return {"content": open(full, encoding="utf-8", errors="ignore").read()}
    except FileNotFoundError:
        raise HTTPException(404, "Not found")

@app.post("/write")
def write_file(req: WriteReq):
    full = os.path.abspath(os.path.join(BASE, req.path))
    if not full.startswith(BASE):
        raise HTTPException(400, "Bad path")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(req.content)
    return {"ok": True}

@app.post("/list")
def list_dir(req: ListReq):
    full = os.path.abspath(os.path.join(BASE, req.path))
    if not full.startswith(BASE):
        raise HTTPException(400, "Bad path")
    return {"entries": os.listdir(full)}
