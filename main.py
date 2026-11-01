from utils import logging_config  # just importing applies config
import logging



logger = logging.getLogger("my_app")

from fastapi import FastAPI

from api.v1.routers import notes as notes_router
from api.v1.routers import query as query_router
from api.v1.routers import users as users_router
from api.v1.routers import notebooks as notebooks_router
from utils.rate_limit import RateLimitMiddleware
from api.v1.routers import auth as auth_router
from api.v1.routers import admin as admin_router

# from utils.chunker.download_data import ensure_punkt
# from contextlib import asynccontextmanager

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     ensure_punkt()   # one time when app starts
#     yield
#     # Cleanup code (if needed) goes here

# app = FastAPI(lifespan=lifespan, title="Smart Notes System API", version="1.0.0")

app = FastAPI(title="Smart Notes System API", version="1.0.0")

# Middlewares
app.add_middleware(RateLimitMiddleware)

# Routers
app.include_router(auth_router.router) 
app.include_router(users_router.router)
app.include_router(notebooks_router.router)
app.include_router(notes_router.router)
app.include_router(admin_router.router)
app.include_router(query_router.router)

#app.include_router(search_router.router)

#from utils.clean_data import cleanup_database
from utils.chunker.download_data import ensure_punkt
@app.get("/health")
def health():
    # clean database
    #cleanup_database()
    logger.info("Health check successful.and ensure_punkt() called")
    ensure_punkt()
    return {"status": "ok"}

