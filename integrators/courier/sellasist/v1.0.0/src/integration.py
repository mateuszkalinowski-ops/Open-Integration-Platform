import base64
import io
import logging
from http import HTTPStatus

import httpx
from pypdf import PdfMerger

from src.config import settings
from src.schemas import SellAsistCredentials

logger = logging.getLogger(__name__)


class SellAsistIntegration:
    """SellAsist courier integration.

    Handles label retrieval from the SellAsist API.
    The API URL template contains 'login' as a placeholder
    that gets replaced with the actual account login.
    """

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=settings.rest_integration_timeout)
        logger.info(
            "SellAsist integration initialised with API URL template: %s",
            settings.sellasist_api_url,
        )

    async def close(self) -> None:
        await self._client.aclose()

    def _build_base_url(self, login: str) -> str:
        return settings.sellasist_api_url.replace("login", login)

    @staticmethod
    def _build_headers(api_key: str) -> dict[str, str]:
        return {
            "apiKey": api_key,
            "accept": "application/json",
        }

    async def get_label_bytes(
        self,
        credentials: SellAsistCredentials,
        waybill_numbers: list[str],
        external_id: str,
    ) -> tuple[bytes | str, int]:
        """Retrieve waybill label PDF(s) from SellAsist.

        Fetches all shipments for the given order, downloads each label,
        and merges them into a single PDF when multiple labels exist.

        Returns:
            Tuple of (pdf_bytes, http_status) on success,
            or (error_message, http_status) on failure.
        """
        _waybill_number = waybill_numbers[0]
        base_url = self._build_base_url(credentials.login)
        headers = self._build_headers(credentials.api_key)

        response = await self._client.get(
            f"{base_url}/ordersshipments",
            params={"order_id": external_id},
            headers=headers,
        )

        if response.status_code != HTTPStatus.OK:
            logger.error(
                "Failed to fetch shipments from SellAsist: status=%d url=%s",
                response.status_code,
                response.request.url,
            )
            return "Błąd podczas pobierania etykiety z sellasist", HTTPStatus.BAD_REQUEST

        waybill_list = response.json()
        if not waybill_list:
            return "Brak listu przewozowego dla tego zamówienia", HTTPStatus.BAD_REQUEST

        waybills_bytes: list[bytes] = []
        for single_waybill in waybill_list:
            waybill_id = single_waybill["id"]

            waybill_response = await self._client.get(
                f"{base_url}/ordersshipments/{waybill_id}",
                headers=headers,
            )

            if waybill_response.status_code == HTTPStatus.OK:
                waybill_data = waybill_response.json()
                file_data = waybill_data.get("file")
                if file_data:
                    waybills_bytes.append(base64.b64decode(file_data))

        if not waybills_bytes:
            return "Brak pliku dla listu przewozowego do tego zamówienia", HTTPStatus.BAD_REQUEST

        if len(waybills_bytes) == 1:
            return waybills_bytes[0], HTTPStatus.OK

        merger = PdfMerger()
        for pdf in waybills_bytes:
            merger.append(io.BytesIO(pdf))

        merged_buffer = io.BytesIO()
        merger.write(merged_buffer)
        merger.close()
        merged_buffer.seek(0)

        return merged_buffer.read(), HTTPStatus.OK
