"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import auth, chat, children, curriculum, progress, resources, athletes, activities, checkins, interests, roadmap
from app.config import get_settings
from app.web import routes as web_routes
from app.web import athlete_routes

settings = get_settings()

# Template configuration
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"Starting {settings.app_name}...")
    yield
    # Shutdown
    print(f"Shutting down {settings.app_name}...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="A parenting curriculum assistant to help raise children from 0-18 years",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
)

# Mount static files
static_path = BASE_DIR.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include API routers
app.include_router(auth.router, prefix="/api")
app.include_router(children.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(curriculum.router, prefix="/api")
app.include_router(progress.router, prefix="/api")
app.include_router(resources.router, prefix="/api")
app.include_router(athletes.router, prefix="/api")
app.include_router(activities.router, prefix="/api")
app.include_router(checkins.router, prefix="/api")
app.include_router(interests.router, prefix="/api")
app.include_router(roadmap.router, prefix="/api")

# Include web routes (HTML pages)
app.include_router(web_routes.router)
app.include_router(athlete_routes.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Custom error handlers
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Custom handler for HTTP exceptions."""
    # Only render HTML for non-API requests
    if request.url.path.startswith("/api/"):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    if exc.status_code == 404:
        return templates.TemplateResponse(
            "pages/errors/404.html",
            {"request": request},
            status_code=404,
        )
    elif exc.status_code >= 500:
        return templates.TemplateResponse(
            "pages/errors/500.html",
            {"request": request},
            status_code=exc.status_code,
        )

    # For other errors, return a generic error response
    return templates.TemplateResponse(
        "pages/errors/500.html",
        {"request": request},
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    import logging
    logging.error(f"Unhandled exception: {exc}", exc_info=True)

    if request.url.path.startswith("/api/"):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return templates.TemplateResponse(
        "pages/errors/500.html",
        {"request": request},
        status_code=500,
    )
