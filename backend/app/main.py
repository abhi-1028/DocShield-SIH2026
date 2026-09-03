from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.upload import router as upload_router
from app.api.screening import router as screening_router


app = FastAPI(
    title="DocumentShield API",
    description="AI-assisted document screening and tamper detection system",
    version="0.1.0"
)


# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routes
app.include_router(upload_router)
app.include_router(screening_router)


@app.get("/")
def health_check():
    return {
        "status": "online",
        "message": "DocumentShield backend is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }