from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import MCPRequest, MCPResponse
from app.services.mcp_service import MCPService

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol"])

@router.post("/", response_model=MCPResponse)
async def handle_mcp_call(
    request: MCPRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = await MCPService.handle_rpc(
            db=db,
            user=current_user,
            method=request.method,
            params=request.params
        )
        return MCPResponse(id=request.id, result=result, error=None)
    except Exception as e:
        return MCPResponse(
            id=request.id,
            result=None,
            error={"code": -32603, "message": str(e)}
        )
