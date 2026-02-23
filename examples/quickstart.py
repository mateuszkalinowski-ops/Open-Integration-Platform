"""Open Integration Platform by Pinquark.com — Quick Start Example.

This example shows how to use the Python SDK to:
1. Browse available connectors
2. Create a flow (Allegro -> InPost)
3. Trigger an event and see it flow through

Prerequisites:
    pip install pinquark-sdk
    # Platform running at http://localhost:8080 with a tenant + API key
"""

import asyncio

from pinquark_sdk import PinquarkClient


async def main() -> None:
    async with PinquarkClient(
        api_key="pk_live_YOUR_API_KEY_HERE",
        base_url="http://localhost:8080",
    ) as client:

        # 1. Check platform health
        health = await client.health()
        print(f"Platform status: {health['status']} (v{health['version']})")

        # 2. Browse available connectors
        couriers = await client.connectors.list(category="courier")
        print(f"\nAvailable courier connectors: {len(couriers)}")
        for c in couriers:
            print(f"  - {c.display_name} v{c.version}: {', '.join(c.capabilities)}")

        # 3. Store credentials for a connector
        await client.credentials.store(
            connector_name="inpost",
            credentials={
                "organization_id": "YOUR_ORG_ID",
                "access_token": "YOUR_ACCESS_TOKEN",
            },
        )
        print("\nInPost credentials stored (encrypted)")

        # 4. Create a flow: Allegro order -> InPost shipment
        flow = await client.flows.create(
            name="Allegro -> InPost shipment",
            source_connector="allegro",
            source_event="order.created",
            destination_connector="inpost",
            destination_action="shipment.create",
            source_filter={"delivery_method": "inpost_paczkomat"},
            field_mapping=[
                {"from": "order.buyer.name", "to": "receiver.first_name"},
                {"from": "order.buyer.phone", "to": "receiver.phone"},
                {"from": "order.buyer.address.street", "to": "receiver.address.street"},
                {"from": "order.buyer.address.city", "to": "receiver.address.city"},
                {"from": "order.buyer.address.postal_code", "to": "receiver.address.postal_code"},
                {"from": "order.point_id", "to": "extras.target_point"},
            ],
        )
        print(f"\nFlow created: {flow.name} (id: {flow.id})")

        # 5. Simulate an event
        result = await client.flows.trigger_event(
            connector_name="allegro",
            event="order.created",
            data={
                "order": {
                    "id": "ALG-12345",
                    "buyer": {
                        "name": "Jan Kowalski",
                        "phone": "+48600100200",
                        "address": {
                            "street": "ul. Marszalkowska 1",
                            "city": "Warszawa",
                            "postal_code": "00-001",
                        },
                    },
                    "point_id": "WAW01A",
                    "delivery_method": "inpost_paczkomat",
                },
            },
        )
        print(f"\nEvent triggered: {result.flows_triggered} flow(s) executed")
        for ex in result.executions:
            print(f"  - Flow {ex['flow_id'][:8]}...: {ex['status']} ({ex['duration_ms']}ms)")

        # 6. Check execution log
        executions = await client.flows.list_executions(limit=5)
        print(f"\nRecent executions: {len(executions)}")
        for ex in executions:
            print(f"  [{ex.status}] {ex.started_at} — {ex.duration_ms}ms")


if __name__ == "__main__":
    asyncio.run(main())
