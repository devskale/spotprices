from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from electricity.api.v1.router import router as api_v1_router

app = FastAPI(
    title="Spotprices API",
    description="Electricity Tariff and Spot Price Analysis System",
    version="1.0.0",
)

# Allow the showcase (and any local dev frontend) to fetch from the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/electricity")


@app.get("/")
async def root():
    return {"message": "Spotprices API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
