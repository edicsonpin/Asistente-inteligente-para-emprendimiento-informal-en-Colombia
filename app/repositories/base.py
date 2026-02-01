from typing import Generic, TypeVar, Type, List, Optional, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.config2 import Base
from sqlalchemy.inspection import inspect

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model
        
        # Detectar clave primaria automáticamente
        mapper = inspect(model)
        self.pk = mapper.primary_key[0].name  # ej: "usuario_id"

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(getattr(self.model, self.pk) == id).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = obj_in.dict()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        obj_data = db_obj.__dict__
        update_data = obj_in.dict(exclude_unset=True)

        for field in update_data:
            setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: Any) -> ModelType:
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def get_by_field(self, db: Session, field: str, value: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(getattr(self.model, field) == value).first()

    def get_multi_by_field(self, db: Session, field: str, value: Any, skip: int = 0, limit: int = 100):
        return db.query(self.model).filter(getattr(self.model, field) == value).offset(skip).limit(limit).all()
