from fastapi import APIRouter
from .endpoints.optimization import router as optimization_router

api_router = APIRouter()
api_router.include_router(optimization_router, prefix="/optimize", tags=["optimization"])