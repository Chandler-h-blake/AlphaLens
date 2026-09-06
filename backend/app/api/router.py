from fastapi import APIRouter

from app.api.routes import dashboard, factors, health, industry, market, research, system


api_router = APIRouter()
api_router.include_router(health.router, tags=["system"])
api_router.include_router(factors.router, prefix="/factors", tags=["factors"])
api_router.include_router(research.router, prefix="/research", tags=["research"])
api_router.include_router(industry.router, prefix="/industry", tags=["industry"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(dashboard.router, prefix="/market", tags=["dashboard"])
api_router.include_router(dashboard.review_router, prefix="/reviews", tags=["reviews"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
