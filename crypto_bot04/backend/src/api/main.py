from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import strategy

app = FastAPI(title="Balance Tracker API", description="Simple balance tracking API")

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(strategy.router, prefix="/v1/strategy")
