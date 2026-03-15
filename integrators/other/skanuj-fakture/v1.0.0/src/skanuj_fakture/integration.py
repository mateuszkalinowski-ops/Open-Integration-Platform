"""SkanujFakture integration facade — multi-account management over the API client."""

import logging
from datetime import UTC, datetime
from typing import Any

from src.services.account_manager import AccountManager
from src.skanuj_fakture.client import SkanujFaktureClient
from src.skanuj_fakture.schemas import AuthStatusResponse, ConnectionStatus

logger = logging.getLogger(__name__)


class SkanujFaktureIntegration:
    """High-level facade over the SkanujFakture API supporting multiple accounts."""

    def __init__(self, account_manager: AccountManager) -> None:
        self._account_manager = account_manager
        self._clients: dict[str, SkanujFaktureClient] = {}

    def _get_client(self, account_name: str) -> SkanujFaktureClient:
        if account_name not in self._clients:
            account = self._account_manager.get_account(account_name)
            if account is None:
                raise ValueError(f"Account '{account_name}' not found")
            self._clients[account_name] = SkanujFaktureClient(account)
        return self._clients[account_name]

    async def close(self) -> None:
        for client in self._clients.values():
            await client.close()
        self._clients.clear()

    def reset_client(self, account_name: str) -> None:
        """Remove cached client so it is recreated on next use (e.g. after credential change)."""
        self._clients.pop(account_name, None)

    # -- Companies ---------------------------------------------------------------

    async def get_companies(self, account_name: str) -> list[dict[str, Any]]:
        client = self._get_client(account_name)
        return await client.get_companies()

    async def get_company_entities(self, account_name: str, company_id: int) -> list[dict[str, Any]]:
        client = self._get_client(account_name)
        return await client.get_company_entities(company_id)

    # -- Documents ---------------------------------------------------------------

    async def upload_document(
        self,
        account_name: str,
        company_id: int,
        file_content: bytes,
        filename: str,
        single_document: bool = True,
        sale: bool = False,
    ) -> dict[str, Any]:
        client = self._get_client(account_name)
        return await client.upload_document(company_id, file_content, filename, single_document, sale)

    async def upload_document_v2(
        self,
        account_name: str,
        company_id: int,
        file_content: bytes,
        filename: str,
        single_document: bool = True,
        invoice_type: str = "PURCHASE",
        company_entity_id: int | None = None,
    ) -> dict[str, Any]:
        client = self._get_client(account_name)
        return await client.upload_document_v2(
            company_id,
            file_content,
            filename,
            single_document,
            invoice_type,
            company_entity_id,
        )

    async def get_documents(
        self,
        account_name: str,
        company_id: int,
        document_statuses: list[str] | None = None,
        company_entity_id: int | None = None,
        company_entity_ids: list[int] | None = None,
        company_entity_nips: list[str] | None = None,
        is_sale: bool | None = None,
        invoice: list[str] | None = None,
        contractor: list[str] | None = None,
        contractor_nips: list[str] | None = None,
        real_contractor: list[str] | None = None,
        real_contractor_nips: list[str] | None = None,
        receiver: list[str] | None = None,
        receiver_nips: list[str] | None = None,
        buyer: list[str] | None = None,
        buyer_nips: list[str] | None = None,
        edit_user: list[str] | None = None,
        number: list[str] | None = None,
        document_types: list[int] | None = None,
        payment_types: list[int] | None = None,
        acceptance_status: list[str] | None = None,
        category: list[str] | None = None,
        text: list[str] | None = None,
        vat_costs: list[str] | None = None,
        cost_types: list[str] | None = None,
        cost_centers: list[str] | None = None,
        decret_attributes: list[str] | None = None,
        decret_attributes2: list[str] | None = None,
        decret_attributes3: list[str] | None = None,
        decret_attributes4: list[str] | None = None,
        decret_attributes5: list[str] | None = None,
        decret_attributes6: list[str] | None = None,
        decret_attributes7: list[str] | None = None,
        decret_attributes8: list[str] | None = None,
        descriptions: list[str] | None = None,
        filenames: list[str] | None = None,
        account_numbers: list[str] | None = None,
        ksef_number: list[str] | None = None,
        company_entity_id_where_users_are_guests: list[int] | None = None,
        create_date_from: int | None = None,
        create_date_to: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        operation_date_from: str | None = None,
        operation_date_to: str | None = None,
        posting_date_from: str | None = None,
        posting_date_to: str | None = None,
        input_date_from: str | None = None,
        input_date_to: str | None = None,
        payment_date_from: str | None = None,
        payment_date_to: str | None = None,
        netto_from: float | None = None,
        netto_to: float | None = None,
        vat_from: float | None = None,
        vat_to: float | None = None,
        brutto_from: float | None = None,
        brutto_to: float | None = None,
        amount_to_pay_from: float | None = None,
        amount_to_pay_to: float | None = None,
        duplicate: int | None = None,
        decreted: bool | None = None,
        archive: bool | None = None,
        in_ksef: bool | None = None,
        payment_status: str | None = None,
        comment: str | None = None,
        attribute: dict[str, Any] | None = None,
        check_document_ids: list[int] | None = None,
        exception_check_document_ids: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        client = self._get_client(account_name)
        return await client.get_documents(
            company_id,
            document_statuses=document_statuses,
            company_entity_id=company_entity_id,
            company_entity_ids=company_entity_ids,
            company_entity_nips=company_entity_nips,
            is_sale=is_sale,
            invoice=invoice,
            contractor=contractor,
            contractor_nips=contractor_nips,
            real_contractor=real_contractor,
            real_contractor_nips=real_contractor_nips,
            receiver=receiver,
            receiver_nips=receiver_nips,
            buyer=buyer,
            buyer_nips=buyer_nips,
            edit_user=edit_user,
            number=number,
            document_types=document_types,
            payment_types=payment_types,
            acceptance_status=acceptance_status,
            category=category,
            text=text,
            vat_costs=vat_costs,
            cost_types=cost_types,
            cost_centers=cost_centers,
            decret_attributes=decret_attributes,
            decret_attributes2=decret_attributes2,
            decret_attributes3=decret_attributes3,
            decret_attributes4=decret_attributes4,
            decret_attributes5=decret_attributes5,
            decret_attributes6=decret_attributes6,
            decret_attributes7=decret_attributes7,
            decret_attributes8=decret_attributes8,
            descriptions=descriptions,
            filenames=filenames,
            account_numbers=account_numbers,
            ksef_number=ksef_number,
            company_entity_id_where_users_are_guests=company_entity_id_where_users_are_guests,
            create_date_from=create_date_from,
            create_date_to=create_date_to,
            date_from=date_from,
            date_to=date_to,
            operation_date_from=operation_date_from,
            operation_date_to=operation_date_to,
            posting_date_from=posting_date_from,
            posting_date_to=posting_date_to,
            input_date_from=input_date_from,
            input_date_to=input_date_to,
            payment_date_from=payment_date_from,
            payment_date_to=payment_date_to,
            netto_from=netto_from,
            netto_to=netto_to,
            vat_from=vat_from,
            vat_to=vat_to,
            brutto_from=brutto_from,
            brutto_to=brutto_to,
            amount_to_pay_from=amount_to_pay_from,
            amount_to_pay_to=amount_to_pay_to,
            duplicate=duplicate,
            decreted=decreted,
            archive=archive,
            in_ksef=in_ksef,
            payment_status=payment_status,
            comment=comment,
            attribute=attribute,
            check_document_ids=check_document_ids,
            exception_check_document_ids=exception_check_document_ids,
        )

    async def get_documents_simple(
        self,
        account_name: str,
        company_id: int,
        document_statuses: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        client = self._get_client(account_name)
        return await client.get_documents_simple(company_id, document_statuses=document_statuses)

    async def update_document(
        self,
        account_name: str,
        company_id: int,
        document_id: int,
        document_data: dict[str, Any],
    ) -> dict[str, Any]:
        client = self._get_client(account_name)
        return await client.update_document(company_id, document_id, document_data)

    async def delete_documents(
        self,
        account_name: str,
        company_id: int,
        check_document_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        client = self._get_client(account_name)
        return await client.delete_documents(company_id, check_document_ids=check_document_ids)

    async def get_document_file(self, account_name: str, company_id: int, document_id: int) -> bytes:
        client = self._get_client(account_name)
        return await client.get_document_file(company_id, document_id)

    async def get_document_image(self, account_name: str, company_id: int, document_id: int) -> bytes:
        client = self._get_client(account_name)
        return await client.get_document_image(company_id, document_id)

    # -- Attributes --------------------------------------------------------------

    async def edit_attributes(
        self,
        account_name: str,
        company_id: int,
        document_id: int,
        attributes: list[dict[str, Any]],
        status_id: int | None = None,
    ) -> dict[str, Any]:
        client = self._get_client(account_name)
        return await client.edit_attributes(company_id, document_id, attributes, status_id)

    async def delete_attributes(self, account_name: str, company_id: int, document_id: int) -> dict[str, Any]:
        client = self._get_client(account_name)
        return await client.delete_attributes(company_id, document_id)

    # -- Dictionaries ------------------------------------------------------------

    async def get_dictionaries(self, account_name: str, company_id: int, dict_type: str) -> list[dict[str, Any]]:
        client = self._get_client(account_name)
        return await client.get_dictionaries(company_id, dict_type)

    async def add_dictionary_items(
        self,
        account_name: str,
        company_id: int,
        dict_type: str,
        items: list[dict[str, str]],
    ) -> dict[str, Any]:
        client = self._get_client(account_name)
        return await client.add_dictionary_items(company_id, dict_type, items)

    # -- KSeF -------------------------------------------------------------------

    async def get_ksef_xml(
        self,
        account_name: str,
        company_id: int,
        document_id: int,
        as_json: bool = False,
    ) -> str | dict[str, Any]:
        client = self._get_client(account_name)
        return await client.get_ksef_xml(company_id, document_id, as_json=as_json)

    async def get_ksef_qr(self, account_name: str, company_id: int, document_id: int) -> bytes:
        client = self._get_client(account_name)
        return await client.get_ksef_qr(company_id, document_id)

    async def send_ksef_invoice(
        self,
        account_name: str,
        company_id: int,
        invoice_data: dict[str, Any],
    ) -> dict[str, Any]:
        client = self._get_client(account_name)
        return await client.send_ksef_invoice(company_id, invoice_data)

    # -- Auth / Connection status ------------------------------------------------

    def get_auth_status(self, account_name: str) -> AuthStatusResponse:
        account = self._account_manager.get_account(account_name)
        if account is None:
            return AuthStatusResponse(account_name=account_name, authenticated=False)
        return AuthStatusResponse(
            account_name=account_name,
            authenticated=True,
            last_checked=datetime.now(UTC),
        )

    async def get_connection_status(self, account_name: str) -> ConnectionStatus:
        try:
            client = self._get_client(account_name)
            companies = await client.get_companies()
            return ConnectionStatus(
                account_name=account_name,
                connected=True,
                companies_count=len(companies),
                last_checked=datetime.now(UTC),
            )
        except Exception as e:
            logger.warning("Connection check failed for %s: %s", account_name, str(e))
            return ConnectionStatus(
                account_name=account_name,
                connected=False,
                last_checked=datetime.now(UTC),
                error=str(e),
            )
