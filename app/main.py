import subprocess
import json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

ROOT_PATH = os.environ.get("ROOT_PATH", "")
app = FastAPI(title="MediaPeek", root_path=ROOT_PATH)

# Strip ROOT_PATH from incoming requests when behind reverse proxy
if ROOT_PATH:
    @app.middleware("http")
    async def strip_prefix_middleware(request: Request, call_next):
        path = request.url.path
        if path.startswith(ROOT_PATH):
            # Create new scope with stripped path
            request.scope["path"] = path[len(ROOT_PATH):] or "/"
        response = await call_next(request)
        return response

MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", "/media"))

MEDIA_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
    ".mpg", ".mpeg", ".ts", ".m2ts", ".mts", ".vob", ".ogv", ".3gp",
    ".mp3", ".flac", ".aac", ".ogg", ".wav", ".m4a", ".wma", ".opus",
    ".aiff", ".ape", ".mka",
}


class ProbeRequest(BaseModel):
    path: str


def run_ffprobe(filepath: str) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        filepath,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail=f"ffprobe error: {result.stderr.strip()}")
        return json.loads(result.stdout)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="ffprobe not found in PATH")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="ffprobe timed out")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse ffprobe output")


@app.get("/")
def root():
    return FileResponse("/app/static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/browse")
def browse(path: str = ""):
    target = (MEDIA_ROOT / path).resolve()
    if not str(target).startswith(str(MEDIA_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    if not target.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    if not target.is_dir():
        raise HTTPException(status_code=400, detail="Not a directory")

    entries = []
    try:
        for entry in sorted(target.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
            if entry.name.startswith("."):
                continue
            is_dir = entry.is_dir()
            is_media = not is_dir and entry.suffix.lower() in MEDIA_EXTENSIONS
            if is_dir or is_media:
                rel = str(entry.relative_to(MEDIA_ROOT))
                entries.append({
                    "name": entry.name,
                    "path": rel,
                    "is_dir": is_dir,
                    "size": entry.stat().st_size if not is_dir else None,
                    "ext": entry.suffix.lower() if not is_dir else None,
                })
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    parent = str(Path(path).parent) if path and path != "." else None
    if parent == ".":
        parent = ""

    return {
        "current": path,
        "parent": parent,
        "entries": entries,
    }


@app.post("/api/probe")
def probe(req: ProbeRequest):
    target = (MEDIA_ROOT / req.path).resolve()
    if not str(target).startswith(str(MEDIA_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if target.is_dir():
        raise HTTPException(status_code=400, detail="Path is a directory")
    return run_ffprobe(str(target))


app.mount("/", StaticFiles(directory="/app/static"), name="static")
