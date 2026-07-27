from sqlalchemy.orm import Session

from app.domain.models import Artifact
from app.repositories.records import ArtifactRecord


class ArtifactRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def store(self, artifact: Artifact) -> ArtifactRecord:
        record = ArtifactRecord(**artifact.model_dump(exclude={"protocol_version"}))
        self._session.add(record)
        return record
