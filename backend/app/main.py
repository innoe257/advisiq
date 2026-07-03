from fastapi import FastAPI

from app.api.v1.auth import router as auth_router
from app.api.v1.interventions import router as interventions_router
from app.api.v1.risk import router as risk_router
from app.api.v1.students import router as students_router

app = FastAPI(title="AdvisIQ API", version="0.1.0")

app.include_router(auth_router, prefix="/api/v1")
app.include_router(students_router, prefix="/api/v1")
app.include_router(interventions_router, prefix="/api/v1")
app.include_router(risk_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
