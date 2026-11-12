"""Simple Todo API (FastAPI + SQLite)."""
import os
import sqlite3
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

DB_PATH = os.environ.get("TODO_DB_PATH", "todos.db")
STATIC_DIR = Path(__file__).parent / "static"
RATE_LIMIT = int(os.environ.get("RATE_LIMIT_PER_MIN", "120"))

app = FastAPI(title="Todo App", docs_url=None, redoc_url=None)


# ---- storage ---------------------------------------------------------------
@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS todos ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "title TEXT NOT NULL,"
            "done INTEGER NOT NULL DEFAULT 0)"
        )
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---- models (allow-list validation) ----------------------------------------
class TodoIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    done: bool | None = None


def _row(r: sqlite3.Row) -> dict:
    return {"id": r["id"], "title": r["title"], "done": bool(r["done"])}


# ---- middleware: rate limit, security headers, no internal error leakage ---
_hits: dict[str, deque] = defaultdict(deque)


@app.middleware("http")
async def guard(request: Request, call_next):
    if request.url.path.startswith("/api"):
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        q = _hits[ip]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= RATE_LIMIT:
            return JSONResponse({"detail": "Too many requests"}, status_code=429)
        q.append(now)
    try:
        response = await call_next(request)
    except Exception:  # never expose internals
        return JSONResponse({"detail": "Internal server error"}, status_code=500)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


# ---- routes ----------------------------------------------------------------
@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/api/todos")
def list_todos():
    with db() as c:
        return [_row(r) for r in c.execute("SELECT * FROM todos ORDER BY id")]


@app.post("/api/todos", status_code=201)
def create_todo(body: TodoIn):
    with db() as c:
        cur = c.execute("INSERT INTO todos (title) VALUES (?)", (body.title.strip(),))
        return _row(c.execute("SELECT * FROM todos WHERE id=?", (cur.lastrowid,)).fetchone())


@app.patch("/api/todos/{todo_id}")
def update_todo(todo_id: int, body: TodoUpdate):
    with db() as c:
        row = c.execute("SELECT * FROM todos WHERE id=?", (todo_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Not found")
        title = body.title.strip() if body.title is not None else row["title"]
        done = int(body.done) if body.done is not None else row["done"]
        c.execute("UPDATE todos SET title=?, done=? WHERE id=?", (title, done, todo_id))
        return _row(c.execute("SELECT * FROM todos WHERE id=?", (todo_id,)).fetchone())


@app.delete("/api/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int):
    with db() as c:
        if c.execute("DELETE FROM todos WHERE id=?", (todo_id,)).rowcount == 0:
            raise HTTPException(404, "Not found")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
