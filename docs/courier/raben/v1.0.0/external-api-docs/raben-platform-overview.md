# Raben Group — External API Documentation

## Source

- Website: https://polska.raben-group.com/rozwiazania-it
- myRaben portal: https://myraben.com
- Retrieved: 2026-02-22

## Platform Overview

Raben Group is a European logistics company operating in 17 countries offering:
- Domestic and international road transport (drobnica / LTL, FTL)
- Contract logistics (warehousing, copacking, comanufacturing)
- Intermodal transport
- Fresh logistics (temperature-controlled)

## IT Solutions

### myRaben (https://myraben.com)
Customer management platform with the following modules:

| Module | Description |
|---|---|
| **Track & Trace** | Advanced shipment tracking with ETA parameter |
| **myOrder** | Transport order placement |
| **myDelivery** | Individual delivery planning |
| **myClaim** | Complaint submission |
| **myOffer** | Price offer preparation |
| **mySlot** | Delivery notifications to warehouse |
| **myStock** | Contract logistics orders |
| **Individual config** | Account personalization and sub-accounts |

### ETA (Estimated Time of Arrival)
- Calculated from GPS position of mobile device on delivery vehicle
- Updates in Track & Trace module on myRaben.com
- Accuracy: +/- 2 hours
- Auto-updates on deviations >= 60 minutes
- Email notification service (EML) available for receivers:
  - 1st notification: Shipment registration with tracking link
  - 2nd notification: Loading on delivery vehicle
  - 3rd notification: ETA with estimated delivery time window

### PCD (Picture Confirming Delivery)
- Contactless delivery confirmation
- Driver takes 3 photos: label, shipment, shipment with label
- Recorded data: vehicle registration, date, time, GPS coordinates
- Documents visible in myTrack&Trace module

## Service Types

| Service | Description |
|---|---|
| Cargo Classic | Standard delivery (24/48 hours) |
| Cargo Premium | Priority delivery |
| Cargo Premium 08:00 | Time-definite delivery by 08:00 |
| Cargo Premium 10:00 | Time-definite delivery by 10:00 |
| Cargo Premium 12:00 | Time-definite delivery by 12:00 |
| Cargo Premium 16:00 | Time-definite delivery by 16:00 |

## Integration Methods

### Direct API (myRaben)
- Authentication: Username/password → JWT token
- Protocol: REST (JSON)
- Base URL: https://myraben.com/api/v1

### Third-Party Platforms
- AfterShip: Tracking API integration
- Cargoson: TMS platform with booking API
- TrackingMore: Tracking API

## API Endpoints (Inferred from myRaben Modules)

| Module | Endpoint Pattern | Method | Description |
|---|---|---|---|
| myOrder | `/orders` | POST | Create transport order |
| myOrder | `/orders/{id}` | GET | Get order details |
| myOrder | `/orders/{id}/cancel` | PUT | Cancel order |
| Track & Trace | `/tracking/{waybill}` | GET | Full tracking history |
| Track & Trace | `/tracking/{waybill}/status` | GET | Current status |
| Track & Trace | `/tracking/{waybill}/eta` | GET | ETA information |
| Labels | `/labels/{waybill}` | GET | Shipping label |
| myClaim | `/claims` | POST | Submit complaint |
| myClaim | `/claims/{id}` | GET | Get claim status |
| PCD | `/deliveries/{waybill}/confirmation` | GET | Delivery confirmation + photos |
| Auth | `/auth/login` | POST | JWT authentication |

## Countries of Operation

Bulgaria, Czech Republic, Estonia, Greece, Germany, Austria, Poland, Hungary, Italy,
Latvia, Lithuania, Netherlands, Romania, Slovakia, Switzerland, Turkey, Ukraine
