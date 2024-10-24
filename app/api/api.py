
from fastapi import APIRouter
from .endpoints import engagement_api
from .endpoints import auth_api
from .endpoints import coveragemap_api
from .endpoints import nielsen_api
from .endpoints import useradmin_api
api_router = APIRouter()

api_router.include_router(auth_api.router, prefix="/auth", tags=["auth"])
api_router.include_router(engagement_api.router, prefix="/engagement", tags=["engagement"])
api_router.include_router(coveragemap_api.router, prefix="/map", tags=["map"])
api_router.include_router(nielsen_api.router, prefix="/nielsen", tags=["nielsen"])
api_router.include_router(useradmin_api.router, prefix="/useradmin", tags=["useradmin"])