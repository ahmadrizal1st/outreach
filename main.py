import os
import argparse
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.database import engine, Base
from app.api.routes import api_router
from app.followup.scheduler import init_scheduler
from app.core.logger import setup_logger
from app.core.errors import http_exception_handler, general_exception_handler
from fastapi.exceptions import HTTPException

logger = setup_logger()

def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — runs on startup and shutdown."""
    init_db()
    init_scheduler()
    logger.info("Outreach API started.")
    yield
    logger.info("Outreach API shutting down.")

app = FastAPI(title="Outreach API", lifespan=lifespan)

from app.core.security import BasicAuthMiddleware, CSRFMiddleware
app.add_middleware(CSRFMiddleware)
app.add_middleware(BasicAuthMiddleware)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(api_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    parser = argparse.ArgumentParser()
    parser.add_argument('--init-db', action='store_true', help='Initialize the database')
    args = parser.parse_args()

    if args.init_db:
        init_db()
        print("✅ Database initialized")
    else:
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
