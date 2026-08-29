import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.dependencies import get_current_active_user
from app.models.models import ApiKey, User
from app.schemas.schemas import ApiKeyCreate, ApiKeyOut, ApiKeyCreatedResponse
from app.core.security import generate_api_key

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

@router.get("/", response_model=List[ApiKeyOut])
def get_user_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(ApiKey).filter(
        ApiKey.user_id == current_user.id,
        ApiKey.revoked_at.is_(None)
    ).order_by(ApiKey.created_at.desc()).all()

@router.post("/", response_model=ApiKeyCreatedResponse)
def create_api_key(
    req: ApiKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    raw_key, key_prefix, key_hash = generate_api_key()
    
    api_key_obj = ApiKey(
        user_id=current_user.id,
        name=req.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        rate_limit_per_min=req.rate_limit_per_min or 60,
        created_at=datetime.datetime.utcnow()
    )
    db.add(api_key_obj)
    db.commit()
    db.refresh(api_key_obj)

    return ApiKeyCreatedResponse(
        id=api_key_obj.id,
        name=api_key_obj.name,
        key_prefix=api_key_obj.key_prefix,
        api_key=raw_key,
        rate_limit_per_min=api_key_obj.rate_limit_per_min,
        created_at=api_key_obj.created_at
    )

@router.delete("/{id}")
def revoke_api_key(
    id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    key = db.query(ApiKey).filter(
        ApiKey.id == id,
        ApiKey.user_id == current_user.id
    ).first()
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")

    key.revoked_at = datetime.datetime.utcnow()
    db.commit()
    return {"message": f"API Key '{key.name}' successfully revoked"}
