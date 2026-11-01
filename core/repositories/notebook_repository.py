import logging
logger = logging.getLogger("my_app.repositories.notebook_repository")

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from core.repositories.base_repository import BaseRepository
from core.repositories.mixins.cache_mixin import CacheMixin
from infrastructure.cache import CacheKeys
from utils.outbox import emit_event

from core.repositories.models.notebook_models import NotebookModel
from core.entities.notebook import Notebook, NotebookId, Timestamp  # <-- value objects


class NotebookRepository(BaseRepository, CacheMixin):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def get_by_id(self, notebook_id: UUID) -> Optional[Notebook]:
        key = CacheKeys.NOTEBOOK_BY_ID.format(notebook_id=notebook_id)
        return self.get_cached(key, lambda: self._load_notebook_by_id(notebook_id))

    def create(self, entity: Notebook) -> Notebook:
        with self._transaction():
            db_obj = self._to_db_model(entity)
            self.db.add(db_obj)
            self.db.flush()
            created = self._to_entity(db_obj)
            nid = created.id.value if hasattr(created.id, "value") else created.id
            self.invalidate_keys(CacheKeys.NOTEBOOK_BY_ID.format(notebook_id=nid))
            name = created.name
            created_at = created.modified_date
            user_id = created.user_id
            logger.info(f"[NotebookRepository] Created notebook: user: {user_id} name: {name} (id: {nid}) (created_at:{created_at})")
            emit_event({"op": "notebook_create", "user_id": user_id, "notebook_id": str(nid), "name": name, "created_at": created_at})
            return created

    def update(self, entity: Notebook) -> Notebook:
        with self._transaction():
            db_obj: NotebookModel = (
                self.db.query(NotebookModel).filter(NotebookModel.id == entity.id.value).first()
            )
            if not db_obj:
                raise ValueError("Notebook not found")
            db_obj.name = entity.name
            db_obj.color = entity.color
            self.db.flush()
            updated = self._to_entity(db_obj)
            nid = updated.id.value if hasattr(updated.id, "value") else updated.id
            self.invalidate_keys(CacheKeys.NOTEBOOK_BY_ID.format(notebook_id=nid))
            emit_event({"op": "notebook_update", "notebook_id": str(nid)})
            return updated

    def delete(self, notebook_id: UUID) -> None:
        with self._transaction():
            obj: NotebookModel = self.db.query(NotebookModel).filter(NotebookModel.id == notebook_id).first()
            if not obj:
                return
            self.db.delete(obj)
            self.db.flush()
            self.invalidate_keys(CacheKeys.NOTEBOOK_BY_ID.format(notebook_id=notebook_id))
            emit_event({"op": "notebook_delete", "notebook_id": str(notebook_id)})

    # --------- Helpers ---------
    def _load_notebook_by_id(self, notebook_id: UUID) -> Optional[Notebook]:
        obj: Optional[NotebookModel] = self.db.query(NotebookModel).filter(NotebookModel.id == notebook_id).first()
        return self._to_entity(obj) if obj else None

    @staticmethod
    def _to_entity(obj: Optional[NotebookModel]) -> Optional[Notebook]:
        if not obj:
            return None
        return Notebook(
            id=NotebookId(value=str(obj.id)),
            user_id=getattr(obj, "user_id", None),
            name=obj.name,
            color=obj.color,
            created_date=Timestamp(value=getattr(obj, "created_at", None)),
            modified_date=Timestamp(value=getattr(obj, "updated_at", None)),
        )

    @staticmethod
    def _to_db_model(entity: Notebook) -> NotebookModel:
        return NotebookModel(
            id=(entity.id.value if hasattr(entity.id, "value") else entity.id),
            user_id=getattr(entity, "user_id", None),
            name=entity.name,
            color=entity.color,
        )

    def _serialize(self, obj: Notebook) -> str:  # type: ignore[override]
        data = {
            "id": obj.id.value if hasattr(obj.id, "value") else str(obj.id),
            "user_id": getattr(obj, "user_id", None),
            "name": obj.name,
            "color": obj.color,
            "created_at": getattr(getattr(obj, "created_date", None), "value", None),
            "updated_at": getattr(getattr(obj, "modified_date", None), "value", None),
        }
        return super()._serialize(data)

    def _deserialize(self, data: str) -> Notebook:  # type: ignore[override]
        raw = super()._deserialize(data)
        return Notebook(
            id=NotebookId(value=str(raw["id"])),
            user_id=raw.get("user_id"),
            name=raw["name"],
            color=raw["color"],
            created_date=Timestamp(value=raw.get("created_at")),
            modified_date=Timestamp(value=raw.get("updated_at")),
        )
