import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core.database import engine, Base
from app.api.routes import api_router
from app.followup.scheduler import init_scheduler

# Initialize Database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Outreach API")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
async def startup_event():
    init_scheduler()

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
