import logging
from contextlib import asynccontextmanager
from http import HTTPStatus
import sys
from pathlib import Path
from typing import AsyncIterator

SDK_PYTHON_PATH = Path(__file__).resolve().parents[5] / "sdk/python"
if str(SDK_PYTHON_PATH) not in sys.path:
    sys.path.insert(0, str(SDK_PYTHON_PATH))

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from pinquark_connector_sdk.legacy import augment_legacy_fastapi_app

from src.config import settings
from src.integration import SellAsistIntegration
from src.schemas import ErrorResponse, LabelRequest

logger = logging.getLogger(__name__)

integration: SellAsistIntegration


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    global integration
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    integration = SellAsistIntegration()
    yield
    await integration.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="SellAsist Courier Integration",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    async def health() -> dict:
        return {"status": "healthy", "version": "1.0.0"}

    @app.get("/readiness")
    async def readiness() -> dict:
        return {"status": "ready", "version": "1.0.0"}

    @app.post("/labels")
    async def get_labels(request: LabelRequest) -> Response:
        result, status_code = await integration.get_label_bytes(
            credentials=request.credentials,
            waybill_numbers=request.waybill_numbers,
            external_id=request.external_id,
        )

        if isinstance(result, bytes):
            filename = f"{request.waybill_numbers[0]}.pdf"
            return Response(
                content=result,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(
                error={
                    "code": "LABEL_RETRIEVAL_FAILED",
                    "message": result,
                    "details": {},
                    "trace_id": "",
                }
            ).model_dump(),
        )

    return app


app = create_app()
app = augment_legacy_fastapi_app(
    app,
    manifest_path=Path(__file__).resolve().parent.parent / "connector.yaml",
)
