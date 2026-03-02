import uuid

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.postgres import SessionLocal
from app.models.paper import Paper
from app.models.user import User


def main() -> int:
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "testuser3").first()
        if not user:
            raise RuntimeError("testuser3 not found")

        samples = [
            (
                "Fall detection with wearable sensors: a transformer baseline",
                "We study fall detection for elderly care using wearable IMU time-series. "
                "We propose a transformer encoder with data augmentation and evaluate on public datasets.",
                "This paper proposes a transformer encoder model for fall detection using inertial sensor data. "
                "We describe preprocessing, augmentation, training, and evaluation against SVM and CNN baselines.",
            ),
            (
                "Graph neural networks for citation recommendation",
                "We present a graph neural network for citation recommendation leveraging paper graphs and text embeddings.",
                "We build a citation graph and train a GNN to recommend citations. We compare to BM25 and dense retrieval baselines.",
            ),
            (
                "A survey of multimodal anomaly detection in smart homes",
                "This survey reviews multimodal anomaly detection methods for smart home monitoring, focusing on elderly safety.",
                "We summarize multimodal sensors, fusion strategies, benchmarks, and open challenges in smart-home anomaly detection.",
            ),
        ]

        created = 0
        for title, abstract, content in samples:
            exists = db.query(Paper).filter(Paper.user_id == user.id, Paper.title == title).first()
            if exists:
                continue
            p = Paper(
                id=uuid.uuid4(),
                user_id=user.id,
                title=title,
                abstract=abstract,
                content=content,
                filename=f"seed-{created + 1}.txt",
                file_path=f"seed://{created + 1}",
                file_size=0,
                paper_metadata={},
            )
            db.add(p)
            created += 1
        db.commit()
        print("seeded", created)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
