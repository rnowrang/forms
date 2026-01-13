"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import get_settings
from app.routers import auth, templates, forms, versions, audit, review, export

settings = get_settings()

app = FastAPI(
    title="IRB Forms Management System",
    description="Smart online forms with conditional sections, versioning, review workflow, and document generation",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(forms.router, prefix="/api/forms", tags=["Form Instances"])
app.include_router(versions.router, prefix="/api/versions", tags=["Versions"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit Trail"])
app.include_router(review.router, prefix="/api/review", tags=["Review Workflow"])
app.include_router(export.router, prefix="/api/export", tags=["Document Export"])

# Ensure storage directories exist
for dir_path in [settings.upload_dir, settings.generated_dir, settings.template_dir]:
    os.makedirs(dir_path, exist_ok=True)

# Mount static files for generated documents (protected in production)
if os.path.exists(settings.generated_dir):
    app.mount("/generated", StaticFiles(directory=settings.generated_dir), name="generated")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "irb-forms-backend"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "IRB Forms Management System API",
        "docs": "/docs",
        "health": "/health",
    }
