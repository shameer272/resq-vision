import os
import sys

# Ensure backend root is in sys.path so 'from app...' works regardless of cwd
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.endpoints import router as api_router

app = FastAPI(
    title="ResQ Vision API",
    description="Multimodal Emergency Situation Intelligence Platform powered by Gemma 4",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development allow all for easy pair programming & testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Endpoints
app.include_router(api_router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Centralized error handler. Ensures raw stack traces are logged on the server
    while client receives clean, actionable error messages.
    """
    print(f"[ERROR] Global exception during {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "Gemma analysis or internal service encountered an issue. Please verify input and retry.",
            "detail": str(exc) if settings.APP_ENV == "development" else "Server execution error"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True, app_dir=backend_root)
