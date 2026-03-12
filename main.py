from fastapi import FastAPI
from electricity.api.v1.router import router as api_v1_router

app = FastAPI(
    title="Spotprices API",
    description="Electricity Tariff and Spot Price Analysis System",
    version="1.0.0",
)

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Spotprices API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
