import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.redis import redis_client


def main(argv: list[str]) -> int:
    ids = argv[1:]
    if not ids:
        print("usage: python scripts/inspect_rule_task.py <task_id> [task_id...]")
        return 2
    for t in ids:
        try:
            tid = uuid.UUID(t)
        except Exception as e:
            print(t, "invalid uuid:", e)
            continue
        key = f"format_rule:task:{tid}"
        v = redis_client.get_json(key)
        print(t, json.dumps(v, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
