from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=templates_dir)

async def http_exception_handler(request: Request, exc):
    return templates.TemplateResponse(
        "errors/error.html",
        {
            "request": request,
            "status_code": exc.status_code,
            "detail": exc.detail
        },
        status_code=exc.status_code
    )

async def general_exception_handler(request: Request, exc):
    return templates.TemplateResponse(
        "errors/error.html",
        {
            "request": request,
            "status_code": 500,
            "detail": str(exc)
        },
        status_code=500
    )
