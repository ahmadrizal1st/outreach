import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import api_router

app = FastAPI(title="Client Finder", version="0.1.0")

# Setup static files directory
static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
os.makedirs(os.path.join(static_dir, "css"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "js"), exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
