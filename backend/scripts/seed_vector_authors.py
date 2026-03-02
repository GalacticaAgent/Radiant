import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.postgres import SessionLocal
from app.models.kb import Author, Embedding, PaperAuthor
from app.models.paper import Paper
from app.models.user import User
from app.services.embedding_service import EmbeddingService


def main() -> int:
    service = EmbeddingService()
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "testuser3").first()
        if not user:
            raise RuntimeError("testuser3 not found")

        papers = (
            db.query(Paper)
            .filter(Paper.user_id == user.id, Paper.filename.like("seed-%"))
            .order_by(Paper.created_at.asc())
            .all()
        )
        if not papers:
            raise RuntimeError("seed papers not found; run seed_vector_papers.py first")

        people = [
            ("Dr. Alice Chen", "Smart Health Lab, University A"),
            ("Dr. Bruno Silva", "Graph Systems Group, Institute B"),
            ("Dr. Clara Wang", "Multimodal AI Center, University C"),
        ]

        created = 0
        for i, p in enumerate(papers[:3]):
            name, aff = people[i]
            external_id = f"seed:{i+1}"
            author = db.query(Author).filter(Author.source == "seed", Author.external_id == external_id).first()
            if not author:
                author = Author(
                    source="seed",
                    external_id=external_id,
                    name=name,
                    affiliations=[aff],
                    h_index=10 + i * 3,
                    citation_count=200 + i * 50,
                    paper_count=20 + i * 5,
                    raw_profile={
                        "top_papers": [
                            {"title": p.title, "year": 2025, "venue": "DemoConf", "citation_count": 12 + i},
                        ]
                    },
                )
                db.add(author)
                db.commit()
                db.refresh(author)
                created += 1

            link = db.query(PaperAuthor).filter(PaperAuthor.paper_id == p.id, PaperAuthor.author_id == author.id).first()
            if not link:
                db.add(PaperAuthor(paper_id=p.id, author_id=author.id, author_order=0))
                db.commit()

            raw = author.raw_profile or {}
            top_papers = raw.get("top_papers") or []
            top_titles = [x.get("title") for x in top_papers if isinstance(x, dict) and x.get("title")]
            text = "\n".join(
                [
                    f"Name: {author.name}",
                    f"Affiliation: {aff}",
                    f"Topics: {p.title}",
                    "Representative works:",
                    *[f"- {t}" for t in top_titles[:8]],
                ]
            ).strip()
            h = service.content_hash(text)
            emb = db.query(Embedding).filter(Embedding.object_type == "author", Embedding.object_id == author.id, Embedding.model == service.model).first()
            if emb and emb.content_hash == h and emb.vector is not None:
                continue
            vec = service.embed_text(text)
            if not emb:
                emb = Embedding(object_type="author", object_id=author.id, model=service.model, dim=len(vec))
            emb.dim = len(vec)
            emb.vector = vec
            emb.vector_jsonb = vec
            emb.content_hash = h
            db.add(emb)
            db.commit()

        print("authors_created", created)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

