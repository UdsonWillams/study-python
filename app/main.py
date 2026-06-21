"""Aplicação FastAPI: serve o site (Jinja2) e a API de progresso.

Roda com:  uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .database import get_db
from .models import Module, Progress, Roadmap, Topic
from .schemas import ProgressIn, ProgressOut
from .seed import seed

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas e carrega o conteúdo dos JSONs na inicialização.
    seed()
    yield


app = FastAPI(title="Python do Zero", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))


def _completed_topic_ids(db: Session) -> set[int]:
    return set(db.scalars(select(Progress.topic_id)).all())


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    roadmaps = db.scalars(
        select(Roadmap)
        .options(selectinload(Roadmap.modules).selectinload(Module.topics))
        .order_by(Roadmap.position)
    ).all()
    completed = _completed_topic_ids(db)

    # Calcula progresso por roadmap para a barra.
    stats = {}
    for rm in roadmaps:
        topics = [t for m in rm.modules for t in m.topics]
        done = sum(1 for t in topics if t.id in completed)
        stats[rm.id] = {
            "total": len(topics),
            "done": done,
            "pct": round(100 * done / len(topics)) if topics else 0,
        }

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "roadmaps": roadmaps,
            "completed": completed,
            "stats": stats,
        },
    )


@app.get("/topic/{slug}", response_class=HTMLResponse)
def topic_page(slug: str, request: Request, db: Session = Depends(get_db)):
    topic = db.scalar(
        select(Topic)
        .where(Topic.slug == slug)
        .options(selectinload(Topic.exercises))
    )
    if topic is None:
        raise HTTPException(status_code=404, detail="Tópico não encontrado")

    # Navegação: tópicos do mesmo roadmap em ordem (módulo, depois posição).
    roadmap = topic.module.roadmap
    ordered = [t for m in roadmap.modules for t in m.topics]
    idx = next(i for i, t in enumerate(ordered) if t.id == topic.id)
    prev_topic = ordered[idx - 1] if idx > 0 else None
    next_topic = ordered[idx + 1] if idx < len(ordered) - 1 else None

    completed = _completed_topic_ids(db)

    return templates.TemplateResponse(
        "topic.html",
        {
            "request": request,
            "topic": topic,
            "module": topic.module,
            "roadmap": roadmap,
            "prev_topic": prev_topic,
            "next_topic": next_topic,
            "is_done": topic.id in completed,
        },
    )


@app.get("/api/progress", response_model=ProgressOut)
def get_progress(db: Session = Depends(get_db)):
    return ProgressOut(completed_topic_ids=sorted(_completed_topic_ids(db)))


@app.post("/api/progress", response_model=ProgressOut)
def mark_progress(payload: ProgressIn, db: Session = Depends(get_db)):
    topic = db.get(Topic, payload.topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Tópico não encontrado")

    existing = db.scalar(select(Progress).where(Progress.topic_id == topic.id))
    if existing is None:
        db.add(Progress(topic_id=topic.id))
        db.commit()

    return ProgressOut(completed_topic_ids=sorted(_completed_topic_ids(db)))


@app.delete("/api/progress/{topic_id}", response_model=ProgressOut)
def unmark_progress(topic_id: int, db: Session = Depends(get_db)):
    existing = db.scalar(select(Progress).where(Progress.topic_id == topic_id))
    if existing is not None:
        db.delete(existing)
        db.commit()
    return ProgressOut(completed_topic_ids=sorted(_completed_topic_ids(db)))
