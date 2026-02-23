# InPost ShipX Courier Integration — v1.0.0

## Overview
InPost ShipX REST API integration for creating parcel locker and courier shipments, retrieving labels, tracking, and managing pickup points in Poland.

## External API
- **Protocol**: REST (JSON)
- **API URL (Production)**: https://api-shipx-pl.easypack24.net/
- **API URL (Sandbox)**: https://sandbox-api-shipx-pl.easypack24.net/
- **Documentation**: https://dokumentacja-inpost.atlassian.net/wiki/spaces/PL/pages/18153476
- **Developer Portal**: https://developers.inpost-group.com/

## Authentication
- Bearer token (Organization API token)
- Organization ID in URL path

## Services
- `inpost_locker_standard` — Standard locker delivery
- `inpost_locker_pass_thru` — Pass-through locker
- `inpost_locker_allegro` — Allegro locker
- `inpost_courier_standard` — Standard courier
- `inpost_courier_express_1000` — Express by 10:00
- `inpost_courier_express_1200` — Express by 12:00
- `inpost_courier_express_1700` — Express by 17:00
- `inpost_courier_palette` — Palette courier
- `inpost_courier_c2c` — Consumer to consumer

## Sandbox
Sandbox available at sandbox-api-shipx-pl.easypack24.net.

## Rate Limits
Not publicly documented. Use reasonable request rates.
