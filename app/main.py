from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .exceptions import DomainError
from .http_error_mapping import http_status_for_domain_error
from .routers import appointments, auth, doctors
from .settings import get_settings


def _domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainError):
        raise exc
    return JSONResponse(status_code=http_status_for_domain_error(exc), content={"detail": exc.detail})


def create_app() -> FastAPI:
    settings = get_settings()
    if settings.app_env.lower() != "dev" and settings.jwt_secret == "dev-secret-change-me":
        raise RuntimeError("JWT_SECRET must be set in non-dev environments")

    app = FastAPI(title="GP Appointments API", docs_url=None, redoc_url=None)

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.get("/docs", include_in_schema=False)
    def swagger_ui():
        response = get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Swagger UI",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        )
        html = response.body.decode("utf-8").replace(
            "</head>",
            '<link rel="stylesheet" type="text/css" href="/static/swagger.css"></head>',
        )
        return HTMLResponse(content=html)

    app.add_exception_handler(DomainError, _domain_error_handler)

    app.include_router(auth.router)
    app.include_router(doctors.router)
    app.include_router(appointments.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
