# EPCIS Serial Number Aggregation Platform - PRD

## Overview
A pharmaceutical EPCIS (Electronic Product Code Information Services) v1.2 document generation platform for serialized packaging data aggregation and shipping event creation.

## Core Features

### 1. Project-Based EPCIS Creation (Completed)
- Multi-step wizard: Configuration → Serial Numbers → Generate EPCIS
- Multi-product support per project
- Hierarchical serial number collection (SSCC → Case → Inner Case → Item)
- Support for various packaging configurations
- EPCIS XML generation with EPCClass vocabulary, Location vocabulary, and events

### 2. Bulk EPCIS Creation (Completed - Feb 4, 2026)
**Route:** `/epcis/bulk-create`

**Features:**
- JSON file upload with serialized packaging data
- Automatic hierarchy resolution from `parentPackagingId` field
- Packaging type validation (EA < IN < CA < SSCC)
- EPCIS v1.2 generation including:
  - Commissioning ObjectEvents (one per record)
  - Aggregation Events (parent-child relationships)
  - Mass Aggregation under user-provided SSCC
  - Shipping ObjectEvent
- EPCClass and Location vocabulary generation
- Lot and expiration date support (ILMD extensions)
- Summary display with event counts and warnings
- XML file download
- Audit record persistence

**API Endpoint:** `POST /api/epcis/bulk-create`
- Accepts multipart form data with JSON file upload
- Required fields: shipping_sscc, sender/receiver location details

### 3. User Management
- JWT-based authentication
- Admin approval workflow for new users
- User settings and profile management

### 4. Location Management
- Save and reuse location data
- SGLN support for EPCIS compliance

## Technical Stack
- **Frontend:** React with custom CSS
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **External:** ScandIt SDK for barcode scanning

## File Structure
```
/app/
├── backend/
│   ├── server.py           # Main API endpoints
│   ├── bulk_epcis.py       # Bulk EPCIS creation logic
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.js               # Main project wizard
│       ├── AppRouter.js         # Route management
│       ├── BulkEPCISCreation.js # Bulk EPCIS UI component
│       ├── ProjectDashboard.js  # Dashboard with nav
│       └── ...
└── test_reports/
```

## Completed Work

### Feb 4, 2026
- **Bulk EPCIS Creation Feature**
  - Created `/app/backend/bulk_epcis.py` with hierarchy resolution and EPCIS generation
  - Added API endpoints in `server.py` (POST /api/epcis/bulk-create, GET /api/epcis/bulk-jobs)
  - Created `BulkEPCISCreation.js` React component
  - Updated `AppRouter.js` with /epcis/bulk-create route
  - Added navigation link in `ProjectDashboard.js`
  - All tests passing (13/13 backend, full frontend coverage)

### Previous Work
- Multi-product support for aggregation projects
- EPCIS header format updates
- Various bug fixes and UI improvements

## Prioritized Backlog

### P0 (Critical)
- None pending

### P1 (Important)
- None pending

### P2 (Nice to Have)
- Bulk EPCIS job history viewing in UI
- Batch validation for large JSON files
- Location selector integration in Bulk EPCIS form

## API Reference

### Bulk EPCIS Creation
```
POST /api/epcis/bulk-create
Content-Type: multipart/form-data

Parameters:
- file: JSON file (required)
- shipping_sscc: 18-digit SSCC (required)
- sender_name, sender_city, sender_country_code, sender_sgln (required)
- receiver_name, receiver_city, receiver_country_code, receiver_sgln (required)
- Optional: sender/receiver street, state, postal_code

Response:
{
  "summary": { totalRecordsProcessed, commissioningEventsCreated, ... },
  "xmlContent": "<?xml version='1.0'...>"
}
```

## Input JSON Format (Bulk)
```json
[
  {
    "_id": "unique-id",
    "type": "CA|IN|EA",
    "lot": "110539",
    "serialNumber": "3030781729685...",
    "expiration": "2027-04-30T00:00:00.000Z",
    "parentPackagingId": "parent-id-or-null",
    "additionalTradeItemIdentification": "00781729685",
    "regulatedProductName": "Product Name",
    "manufacturerOfTradeItemPartyName": "Manufacturer",
    "dosageFormType": "AEROSOL, METERED",
    "strengthDescription": "108 ug/1"
  }
]
```
