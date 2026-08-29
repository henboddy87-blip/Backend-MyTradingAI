from fastapi import APIRouter
from app.schemas.schemas import RiskCalculationRequest, RiskCalculationResponse
from app.services.risk_engine import RiskEngine

router = APIRouter(prefix="/risk", tags=["Risk Engine"])

@router.post("/calculate", response_model=RiskCalculationResponse)
def calculate_risk_parameters(req: RiskCalculationRequest):
    direction = "BUY" if req.take_profit > req.entry else "SELL"
    return RiskEngine.calculate_position_risk(
        account_balance=req.account_balance,
        risk_percentage=req.risk_percentage,
        entry=req.entry,
        stop_loss=req.stop_loss,
        take_profit=req.take_profit,
        direction=direction
    )
