import os
import secrets
from fastapi import Request
from fastapi.responses import HTMLResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
import base64

class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Allow static files and health check
        if request.url.path.startswith("/static") or request.url.path.startswith("/health"):
            return await call_next(request)

        # Skip auth if credentials are not configured (development mode)
        # Assuming we check environment variables ADMIN_USER and ADMIN_PASS
        admin_user = os.getenv("ADMIN_USER")
        admin_pass = os.getenv("ADMIN_PASS")
        
        if not admin_user or not admin_pass:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return self._unauthorized()

        try:
            auth_decoded = base64.b64decode(auth_header.split(" ")[1]).decode("utf-8")
            username, password = auth_decoded.split(":", 1)
            
            is_correct_username = secrets.compare_digest(username.encode("utf-8"), admin_user.encode("utf-8"))
            is_correct_password = secrets.compare_digest(password.encode("utf-8"), admin_pass.encode("utf-8"))

            if not (is_correct_username and is_correct_password):
                return self._unauthorized()

        except Exception:
            return self._unauthorized()

        return await call_next(request)

    def _unauthorized(self):
        return Response(
            content="Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": "Basic"}
        )

class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Very simple CSRF protection.
    Requires HTMX or frontend to pass a specific header for POST/PUT/DELETE,
    or checks the Origin/Referer against Host.
    """
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            # Simple Origin/Referer check
            origin = request.headers.get("origin")
            referer = request.headers.get("referer")
            host = request.headers.get("host")
            
            # If both are missing, we can be strict or lenient. Let's be lenient for local tools,
            # but reject if they exist and don't match host.
            def is_valid_source(source_url):
                if not source_url:
                    return False
                # Remove scheme
                try:
                    source_host = source_url.split("://")[1].split("/")[0]
                    return source_host == host
                except Exception:
                    return False

            if origin or referer:
                if not (is_valid_source(origin) or is_valid_source(referer)):
                    return HTMLResponse("CSRF verification failed.", status_code=403)

        return await call_next(request)
