"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import analyze, backtest, portfolio, simulate

app = FastAPI(
    title="Financial Analysis API",
    description="Bloomberg-style financial analysis toolkit — REST API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="/api", tags=["analysis"])
app.include_router(portfolio.router, prefix="/api", tags=["portfolio"])
app.include_router(simulate.router, prefix="/api", tags=["simulation"])
app.include_router(backtest.router, prefix="/api", tags=["backtest"])


@app.get("/")
async def root():
    return {"status": "ok", "docs": "/docs"}
