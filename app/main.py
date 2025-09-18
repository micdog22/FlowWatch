import os
from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, or_, desc
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from .db import Base, engine, SessionLocal
from .models import Event
from .schemas import EventIn

load_dotenv()

APP_TITLE = os.getenv("APP_TITLE", "FlowWatch")
FLOWWATCH_TOKEN = os.getenv("FLOWWATCH_TOKEN", "").strip()

app = FastAPI(title=APP_TITLE)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# DB init
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    workflow_name: str | None = None,
    resolved: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Event).order_by(desc(Event.created_at))
    if workflow_name:
        stmt = stmt.filter(Event.workflow_name.ilike(f"%{workflow_name}%"))
    if resolved in {"true", "false"}:
        want = resolved == "true"
        stmt = stmt.filter(Event.resolved == want)
    if q:
        stmt = stmt.filter(or_(Event.error_message.ilike(f"%{q}%"), Event.error_stack.ilike(f"%{q}%")))
    events = db.scalars(stmt).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "events": events, "title": APP_TITLE, "filters": {"workflow_name": workflow_name or "", "resolved": resolved or "", "q": q or ""}},
    )

@app.post("/resolve/{event_id}")
def resolve_event(event_id: int, db: Session = Depends(get_db)):
    e = db.get(Event, event_id)
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
    if not e.resolved:
        from datetime import datetime, timezone
        e.resolved = True
        e.resolved_at = datetime.now(timezone.utc)
        db.add(e); db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/webhooks/n8n")
async def webhook_n8n(event: EventIn, request: Request, db: Session = Depends(get_db)):
    token = request.query_params.get("token", "")
    if not FLOWWATCH_TOKEN or token != FLOWWATCH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

    e = Event(
        workflow_id=event.workflow_id,
        workflow_name=event.workflow_name,
        node=event.node,
        error_message=event.error_message,
        error_stack=event.error_stack,
        run_id=event.run_id,
        attempt=event.attempt or 0,
        payload=event.payload,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return {"id": e.id, "status": "stored"}

@app.get("/api/events")
def api_events(
    page: int = 1,
    per_page: int = 20,
    resolved: str | None = None,
    workflow_name: str | None = None,
    db: Session = Depends(get_db),
):
    page = max(page, 1)
    per_page = max(min(per_page, 100), 1)

    stmt = select(Event).order_by(desc(Event.created_at))
    if resolved in {"true","false"}:
        want = resolved == "true"
        stmt = stmt.filter(Event.resolved == want)
    if workflow_name:
        stmt = stmt.filter(Event.workflow_name.ilike(f"%{workflow_name}%"))

    total = db.scalar(select(Event).count())
    items = db.scalars(stmt.offset((page-1)*per_page).limit(per_page)).all()
    return {"page": page, "per_page": per_page, "count": len(items), "total": total, "items": [
        {
            "id": e.id,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "workflow_id": e.workflow_id,
            "workflow_name": e.workflow_name,
            "node": e.node,
            "error_message": e.error_message,
            "run_id": e.run_id,
            "attempt": e.attempt,
            "resolved": e.resolved,
        } for e in items
    ]}
