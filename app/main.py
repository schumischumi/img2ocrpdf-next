from pathlib import Path

from fastapi import FastAPI, APIRouter, Request, Depends

from api.api_v1.api import api_router
from core.config import settings

BASE_PATH = Path(__file__).resolve().parent

root_router = APIRouter()
app = FastAPI(title="OCR API", openapi_url="/openapi.json")


@root_router.get("/", status_code=200)
def root(
    request: Request) -> dict:
    """
    Root GET
    """

    return {"API": "img2ocrpdf-next", "Version": settings.API_V1_STR}


app.include_router(api_router, prefix=settings.API_V1_STR)  # <----- API versioning
app.include_router(root_router)

if __name__ == "__main__":
    # Use this for debugging purposes only
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="debug")