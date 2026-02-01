# services/base_service.py
from typing import TypeVar, Generic, List, Optional, Any, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from repositories.base import CRUDBase
from schemas.base import ModeloBase

ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType', bound=ModeloBase)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=ModeloBase)

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, repository: CRUDBase):
        self.repository = repository
        self.logger = logging.getLogger(__name__)

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        try:
            result = self.repository.get(db, id)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Recurso con id {id} no encontrado"
                )
            return result
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error obteniendo recurso: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno del servidor"
            )

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[ModelType]:
        try:
            # Aplicar filtros si se proporcionan
            query_filters = {k: v for k, v in filters.items() if v is not None}
            if query_filters:
                # Para múltiples filtros, necesitamos una implementación más compleja
                # Por ahora, usamos el primer filtro
                field, value = next(iter(query_filters.items()))
                return self.repository.get_multi_by_field(db, field, value, skip, limit)
            return self.repository.get_multi(db, skip=skip, limit=limit)
        except Exception as e:
            self.logger.error(f"Error obteniendo múltiples recursos: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno del servidor"
            )

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        try:
            return self.repository.create(db, obj_in=obj_in)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            self.logger.error(f"Error creando recurso: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno del servidor"
            )

    def update(
        self, db: Session, *, id: Any, obj_in: UpdateSchemaType
    ) -> ModelType:
        try:
            db_obj = self.get(db, id)
            return self.repository.update(db, db_obj=db_obj, obj_in=obj_in)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error actualizando recurso: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno del servidor"
            )

    def delete(self, db: Session, *, id: Any) -> bool:
        try:
            db_obj = self.get(db, id)
            return self.repository.remove(db, id=id)
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error eliminando recurso: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno del servidor"
            )

    def exists(self, db: Session, id: Any) -> bool:
        return self.repository.exists(db, id)

    def count(self, db: Session) -> int:
        return self.repository.count(db)