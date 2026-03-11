"""Example InPost connector built with the Pinquark Connector SDK."""

from __future__ import annotations

from pinquark_connector_sdk import ConnectorApp, action, trigger


class InPostConnector(ConnectorApp):
    name = "inpost"
    category = "courier"
    version = "3.0.0"
    display_name = "InPost Example (SDK)"
    description = "InPost courier connector demonstrating the Connector SDK"

    class Config:
        required_credentials = ["organization_id", "access_token"]
        rate_limits = {"default": "10/s"}
        port = 8000

    def _base_url(self, payload: dict) -> str:
        sandbox = payload.get("sandbox_mode", False)
        return (
            "https://sandbox-api-shipx-pl.easypack24.net"
            if sandbox
            else "https://api-shipx-pl.easypack24.net"
        )

    def _auth_headers(self, payload: dict) -> dict[str, str]:
        return {"Authorization": f"Bearer {payload.get('access_token', '')}"}

    def _org_id(self, payload: dict) -> str:
        return str(payload.get("organization_id", ""))

    async def test_connection(self) -> bool:
        accounts = self.accounts.list_accounts()
        if not accounts:
            return True
        creds = self.accounts.get(accounts[0])
        if not creds:
            return True
        base = (
            "https://sandbox-api-shipx-pl.easypack24.net"
            if creds.get("sandbox_mode")
            else "https://api-shipx-pl.easypack24.net"
        )
        url = f"{base}/v1/organizations/{creds.get('organization_id', '')}/shipments"
        resp = await self.http.get(
            url,
            headers={"Authorization": f"Bearer {creds.get('access_token', '')}"},
            params={"per_page": "1"},
        )
        return resp.status_code == 200

    @action("shipment.create")
    async def create_shipment(self, payload: dict) -> dict:
        base = self._base_url(payload)
        url = f"{base}/v1/organizations/{self._org_id(payload)}/shipments"
        resp = await self.http.post(url, headers=self._auth_headers(payload), json=payload)
        resp.raise_for_status()
        return resp.json()

    @action("label.get")
    async def get_label(self, payload: dict) -> dict:
        base = self._base_url(payload)
        shipment_id = payload.get("shipment_id", "")
        url = f"{base}/v1/organizations/{self._org_id(payload)}/shipments/{shipment_id}/label"
        resp = await self.http.get(url, headers=self._auth_headers(payload))
        resp.raise_for_status()
        return {"content_base64": resp.text, "format": payload.get("format", "pdf")}

    @action("shipment.status")
    async def get_shipment_status(self, payload: dict) -> dict:
        base = self._base_url(payload)
        tracking = payload.get("tracking_number") or payload.get("shipment_id", "")
        url = f"{base}/v1/organizations/{self._org_id(payload)}/shipments/{tracking}/status"
        resp = await self.http.get(url, headers=self._auth_headers(payload))
        resp.raise_for_status()
        return resp.json()

    @action("pickup_points.list")
    async def list_pickup_points(self, payload: dict) -> dict:
        base = self._base_url(payload)
        url = f"{base}/v1/organizations/{self._org_id(payload)}/points"
        params = {k: v for k, v in (("city", payload.get("city")), ("postcode", payload.get("zip_code"))) if v}
        resp = await self.http.get(url, headers=self._auth_headers(payload), params=params)
        resp.raise_for_status()
        data = resp.json()
        return {"points": data if isinstance(data, list) else data.get("items", [])}

    @action("shipment.cancel")
    async def cancel_shipment(self, payload: dict) -> dict:
        base = self._base_url(payload)
        shipment_id = payload.get("shipment_id", "")
        url = f"{base}/v1/organizations/{self._org_id(payload)}/shipments/{shipment_id}/cancel"
        resp = await self.http.post(url, headers=self._auth_headers(payload))
        resp.raise_for_status()
        return {"cancelled": True, "shipment_id": shipment_id}

    @trigger("shipment.status_changed", interval_seconds=300)
    async def poll_shipment_statuses(self) -> list[dict]:
        events: list[dict] = []
        for account in self.accounts.list_accounts():
            creds = self.accounts.get(account)
            if not creds:
                continue
            base = (
                "https://sandbox-api-shipx-pl.easypack24.net"
                if creds.get("sandbox_mode")
                else "https://api-shipx-pl.easypack24.net"
            )
            url = f"{base}/v1/organizations/{creds.get('organization_id', '')}/shipments"
            try:
                resp = await self.http.get(
                    url,
                    headers={"Authorization": f"Bearer {creds.get('access_token', '')}"},
                    params={"per_page": "10", "status": "created"},
                )
                if resp.status_code != 200:
                    continue
                data = resp.json()
                items = data.get("items", data) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                for s in items:
                    sid = s.get("id") or s.get("shipmentId") or s.get("tracking_number")
                    status = s.get("status", "unknown")
                    if sid:
                        events.append({
                            "event": "shipment.status_changed",
                            "shipment_id": sid,
                            "tracking_number": s.get("tracking_number", sid),
                            "status": status,
                            "account": account,
                        })
            except Exception:
                pass
        return events


if __name__ == "__main__":
    InPostConnector().run()
