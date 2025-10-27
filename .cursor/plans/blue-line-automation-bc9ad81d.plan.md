<!-- bc9ad81d-59cd-4100-9e38-8a2471fa2109 9d52e4b5-9b7d-4b73-a9c3-a3a2bf373192 -->
# Blue Line Automation Implementation Plan

## Overview

Extend the existing composite system to support the Blue Line (Línea Azul) - LLUCH's internal homologation registry for material-supplier pairs with automated field calculation, approval workflow integration, and bidirectional SAP/Composite synchronization.

## Key Requirements

- Blue Line records created automatically when: homologation approved (APC/APR in Regulatory, no REJ in Technical), and purchase made in last 3 years
- 446 configurable fields with logic dependent on material type (Z001: provisional, Z002: homologated)
- Exclude CAN, REJ, EXP states from calculations
- Z1 status materials → sync composition to Composite (SAP)
- Z2 status materials → import composition from Composite to Blue Line

## Database Model Changes

### 1. Extend Material Model

**File:** `backend/app/models/material.py`

- Add `sap_status` field (Z1, Z2, or other SAP statuses)
- Add `lluch_supplier_code` field (e.g., "103721" for LLUCH)

### 2. Extend Composite Model

**File:** `backend/app/models/composite.py`

- Add `is_blue_line` boolean flag
- Add `blue_line_fields` JSON column (stores the 446 configurable fields)
- Add `supplier_reference` field for material-supplier pair tracking

### 3. Extend ApprovalWorkflow Model

**File:** `backend/app/models/approval_workflow.py`

- Add new workflow states: APC, APR, REJ, INC, REA, RUN, VAL, CAN, EXP
- Add `regulatory_status` field (separate from technical status)
- Add `technical_status` field
- Add `section` field to distinguish Regulatory vs Technical approvals

## New Services

### 4. Create BlueLineCalculator Service

**File:** `backend/app/services/blue_line_calculator.py`

- `check_eligibility()`: Verify if material-supplier qualifies for Blue Line
- Check regulatory status (APC or APR)
- Check technical status (not REJ)
- Verify purchase history via ERP (last 3 years)
- `calculate_blue_line()`: Generate Blue Line record with 446 fields
- Apply field logic based on material type (Z001 vs Z002)
- Use field logic configuration
- `recalculate_blue_line()`: Update existing Blue Line when homologation changes
- `delete_blue_line_if_needed()`: Remove/empty Blue Line if only record becomes CAN/REJ/EXP

### 5. Create BlueLineFieldLogic Service

**File:** `backend/app/services/blue_line_field_logic.py`

- Configurable field calculation system for the 446 fields
- `apply_field_logic()`: Execute logic rules for each field
- `get_field_config()`: Retrieve configuration for specific field
- Support for Z001 (provisional/worst case) and Z002 (homologated) logic variants
- JSON-based configuration storage for easy updates without code changes

### 6. Create BlueLineSyncService

**File:** `backend/app/services/blue_line_sync.py`

- `sync_to_composite()`: Send Z1 material composition to SAP Composite
- `import_from_composite()`: Retrieve Z2 material composition from SAP
- Handle bidirectional synchronization logic
- Conflict resolution when data differs between systems

## ERP Integration Enhancement

### 7. Extend ERP Adapter

**File:** `backend/app/integrations/erp_adapter.py`

- Add `get_purchase_history_with_dates()`: Get detailed purchase/sample history
- Add `check_recent_purchases()`: Verify purchases in last N years
- Add `get_material_stock_status()`: Retrieve stock information
- Add `sync_blue_line_to_sap()`: Send Blue Line composition to SAP
- Add `get_composite_from_sap()`: Retrieve composition from SAP Composite

## API Endpoints

### 8. Blue Line API Endpoints

**File:** `backend/app/api/blue_line.py`

- `POST /api/blue-line/calculate/{material_id}`: Generate Blue Line for material
- `GET /api/blue-line/material/{material_id}`: Get Blue Line for material
- `GET /api/blue-line/eligible`: List materials eligible for Blue Line
- `PUT /api/blue-line/{blue_line_id}/sync-to-composite`: Sync Z1 to SAP
- `PUT /api/blue-line/{blue_line_id}/import-from-composite`: Import Z2 from SAP
- `GET /api/blue-line/{blue_line_id}/field-config`: Get field configuration
- `PUT /api/blue-line/field-config/{field_name}`: Update field logic configuration

## Background Tasks

### 9. Blue Line Celery Tasks

**File:** `backend/app/tasks/blue_line_tasks.py`

- `auto_generate_blue_lines`: Periodic task to scan and create Blue Lines for eligible materials
- `sync_z1_materials_to_composite`: Sync all Z1 status materials to SAP
- `import_z2_materials_from_composite`: Import Z2 compositions from SAP
- `recalculate_affected_blue_lines`: When homologation status changes

## Schemas

### 10. Blue Line Pydantic Schemas

**File:** `backend/app/schemas/blue_line.py`

- `BlueLineCreate`, `BlueLineResponse`, `BlueLineUpdate`
- `BlueLineFieldConfig` for 446 field configurations
- `BlueLineEligibilityResponse`
- `BlueLineSyncRequest`, `BlueLineSyncResponse`

## Database Migrations

### 11. Alembic Migration

**File:** `backend/alembic/versions/XXX_add_blue_line_support.py`

- Add columns to `materials` table
- Add columns to `composites` table
- Update `approval_workflows` enum values
- Create index on `is_blue_line` for performance

## Configuration

### 12. Configuration Updates

**File:** `backend/app/core/config.py`

- Add `BLUE_LINE_PURCHASE_HISTORY_YEARS` (default: 3)
- Add `BLUE_LINE_AUTO_GENERATION_ENABLED` flag
- Add `BLUE_LINE_SYNC_ENABLED` flag
- Add SAP Composite integration settings

## Frontend Updates

### 13. Blue Line Management UI

**File:** `frontend/src/pages/BlueLine.tsx`

- List view of Blue Line records
- Eligibility checker showing which materials qualify
- Sync status indicators (last sync, pending sync)
- Manual trigger buttons for sync operations

**File:** `frontend/src/pages/BlueLineDetail.tsx`

- Display 446 fields in organized sections
- Edit field logic configuration (admin only)
- Visual diff when comparing with SAP Composite
- Sync history timeline

### 14. Material Detail Enhancement

**File:** `frontend/src/pages/MaterialDetail.tsx`

- Add SAP status indicator (Z1/Z2)
- Show Blue Line status and eligibility
- Quick link to Blue Line record if exists
- Purchase history display

### 15. API Service Updates

**File:** `frontend/src/services/api.ts`

- Add Blue Line API methods
- Add field configuration methods
- Add sync operation methods

## Testing

### 16. Unit Tests

- Test eligibility logic with various homologation states
- Test field calculation for Z001 and Z002 material types
- Test exclusion of CAN/REJ/EXP states
- Test purchase history validation

### 17. Integration Tests

- Test Blue Line auto-generation flow
- Test bidirectional sync (Z1↔SAP, Z2↔SAP)
- Test single-supplier edge case (deletion when last record expires)

## Documentation

### 18. Update Documentation

**Files:** `ARCHITECTURE.md`, `README.md`

- Document Blue Line system architecture
- Add configuration guide for 446 field logic
- Explain SAP integration setup
- Add troubleshooting guide for sync issues

### To-dos

- [ ] Extend Material, Composite, and ApprovalWorkflow models with Blue Line fields
- [ ] Create BlueLineFieldLogic service with configurable 446 fields system
- [ ] Create BlueLineCalculator service for eligibility checking and calculation
- [ ] Create BlueLineSyncService for bidirectional SAP/Composite synchronization
- [ ] Extend ERP adapter with purchase history and SAP Composite methods
- [ ] Create Blue Line API endpoints for CRUD and sync operations
- [ ] Create Pydantic schemas for Blue Line requests/responses
- [ ] Implement background tasks for auto-generation and synchronization
- [ ] Create Alembic migration for database schema changes
- [ ] Build frontend pages for Blue Line management and detail views
- [ ] Update Material detail page and API service with Blue Line features
- [ ] Write unit and integration tests for Blue Line functionality
- [ ] Update documentation with Blue Line system details