# Packeta (Zásilkovna) SOAP API — API Reference

Source: https://docs.packetery.com/

## WSDL
- https://www.zasilkovna.cz/api/soap.wsdl

## Authentication
Every SOAP request includes:
- `apiPassword` (string) — API password provided by Packeta

## Delivery Modes

### Pickup Point Mode
Default mode. Packet is delivered to a Packeta pickup point (Z-BOX, partner point). Requires `addressId` (target pickup point ID).

### PP Courier Mode
For specific courier IDs, the packet is delivered directly to the recipient's door by a partner courier. Requires:
- Valid courier ID from Packeta's supported courier list
- `carrierPickupPoint` (string, optional) — courier-specific pickup location

### Target Point
- `addressId` — Packeta pickup point ID for standard delivery
- `carrierPickupPoint` — Partner courier pickup point code (for PP courier mode)

## Methods

### createPacket
Creates a new packet.
- **Input**: apiPassword, packet attributes (name, surname, email, phone, addressId, value, weight, eshop, cod, currency, carrierPickupPoint)
- **Output**: Packet ID, barcode
- **Notes**: `addressId` is the target Packeta point. For PP courier mode, use courier-specific IDs and set `carrierPickupPoint` if applicable.

### packetStatus
Retrieves current status of a packet.
- **Input**: apiPassword, packetId
- **Output**: Status code, status text, timestamp
- **Status Codes**: 1 (received data), 2 (arrived at depot), 3 (ready for pickup), 4 (delivered), 5 (returned), 6 (cancelled)

### cancelPacket
Cancels an existing packet.
- **Input**: apiPassword, packetId
- **Output**: Confirmation status
- **Notes**: Only packets not yet dispatched can be cancelled

### packetLabelPdf
Retrieves the Packeta label (sticker) for a packet in PDF format.
- **Input**: apiPassword, packetId, format (A6 or A7), offset
- **Output**: PDF bytes (label)
- **Notes**: A6 format recommended for standard label printers

### packetsCourierLabelsPdf
Retrieves courier-specific labels for packets in PP courier mode.
- **Input**: apiPassword, packetIds (array), offset, courierNumber
- **Output**: PDF bytes (courier labels)
- **Notes**: Used when sending via partner courier — generates the courier's native label format

### packetCourierNumberV2
Assigns a courier tracking number to a packet for PP courier mode.
- **Input**: apiPassword, packetId
- **Output**: Courier tracking number, courier name
- **Notes**: Must be called before generating courier labels. Links the Packeta packet to a specific courier consignment.

## Common Structures

### PacketAttributes
- `number` (string) — Sender's order number
- `name` (string) — Recipient first name
- `surname` (string) — Recipient last name
- `email` (string) — Recipient email
- `phone` (string) — Recipient phone (with country prefix)
- `addressId` (int) — Target Packeta point ID
- `value` (float) — Declared value
- `weight` (float) — Weight in kg
- `eshop` (string) — E-shop identifier
- `cod` (float, optional) — Cash on delivery amount
- `currency` (string) — Currency code (CZK, PLN, EUR, etc.)
- `carrierPickupPoint` (string, optional) — Carrier-specific pickup point code
- `note` (string, optional) — Note for recipient
- `street` (string, optional) — Required for PP courier mode
- `houseNumber` (string, optional) — Required for PP courier mode
- `city` (string, optional) — Required for PP courier mode
- `zip` (string, optional) — Required for PP courier mode

## Error Handling
SOAP faults with structured fault details:
- `InvalidApiPasswordFault` — Invalid API password
- `PacketIdFault` — Invalid or unknown packet ID
- `PacketAttributesFault` — Missing or invalid packet attributes (includes per-field error details)
- `ExternalGatewayFault` — Error communicating with partner courier
