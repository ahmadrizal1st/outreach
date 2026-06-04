import os
import argparse
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.database import engine, Base
from app.api.routes import api_router
from app.followup.scheduler import init_scheduler
from app.core.logger import setup_logger
from app.core.errors import http_exception_handler, general_exception_handler
from fastapi.exceptions import HTTPException

# Setup logger
logger = setup_logger()

# Initialize Database tables
def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized.")

app = FastAPI(title="Outreach API")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

# Register Exception Handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

@app.on_event("startup")
async def startup_event():
    init_db()
    init_scheduler()
    logger.info("Outreach API started.")

app.include_router(api_router)

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

