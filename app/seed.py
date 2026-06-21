"""Carga de conteúdo: lê os JSONs de `content/` e popula o banco via ORM.

Idempotente: a cada execução, o conteúdo (roadmaps/módulos/tópicos/exercícios) é
recriado a partir dos arquivos, mas a tabela `Progress` é **preservada** (o progresso
do aluno não se perde ao atualizar/adicionar aulas).

Para adicionar novos roadmaps, basta criar outro arquivo .json em `app/content/`
seguindo o mesmo formato e reiniciar o app.
"""

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .models import Exercise, Module, Roadmap, Topic

CONTENT_DIR = Path(__file__).resolve().parent / "content"


def _load_roadmap(db: Session, data: dict) -> None:
    """Cria (ou recria) um roadmap completo a partir do dict do JSON."""
    # Remove a versão anterior deste roadmap (cascade apaga módulos/tópicos/exercícios).
    # O Progress aponta para tópicos por id; ao recriar, os ids mudam, então
    # religamos o progresso por slug logo abaixo.
    existing = db.scalar(select(Roadmap).where(Roadmap.slug == data["slug"]))
    if existing is not None:
        db.delete(existing)
        db.flush()

    roadmap = Roadmap(
        slug=data["slug"],
        title=data["title"],
        description=data.get("description", ""),
        position=data.get("position", 0),
    )
    for m in data.get("modules", []):
        module = Module(
            slug=m["slug"],
            title=m["title"],
            summary=m.get("summary", ""),
            position=m.get("position", 0),
        )
        for t in m.get("topics", []):
            topic = Topic(
                slug=t["slug"],
                title=t["title"],
                lesson_md=t.get("lesson_md", ""),
                position=t.get("position", 0),
            )
            for ex in t.get("exercises", []):
                topic.exercises.append(
                    Exercise(
                        position=ex.get("position", 0),
                        prompt=ex["prompt"],
                        starter_code=ex.get("starter_code", ""),
                        test_code=ex.get("test_code", ""),
                        solution=ex.get("solution", ""),
                    )
                )
            module.topics.append(topic)
        roadmap.modules.append(module)

    db.add(roadmap)


def seed() -> None:
    """Cria as tabelas (se necessário) e carrega todos os JSONs de content/."""
    Base.metadata.create_all(engine)

    files = sorted(CONTENT_DIR.glob("*.json"))
    if not files:
        return

    with SessionLocal() as db:
        # Guarda os slugs de tópicos já concluídos para religar o progresso
        # depois que os tópicos forem recriados (os ids mudam).
        from .models import Progress

        completed_slugs = {
            slug
            for (slug,) in db.execute(
                select(Topic.slug).join(Progress, Progress.topic_id == Topic.id)
            ).all()
        }

        for path in files:
            data = json.loads(path.read_text(encoding="utf-8"))
            _load_roadmap(db, data)
        db.flush()

        # Religa o progresso pelos slugs preservados.
        db.query(Progress).delete()
        if completed_slugs:
            topics = db.scalars(
                select(Topic).where(Topic.slug.in_(completed_slugs))
            ).all()
            for topic in topics:
                db.add(Progress(topic_id=topic.id))

        db.commit()


if __name__ == "__main__":
    seed()
    print("Conteúdo carregado com sucesso.")
