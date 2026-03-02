import uuid


def external_paper_uuid(source: str, external_id: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"external_paper:{source}:{external_id}")

