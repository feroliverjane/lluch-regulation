# Blue Line (Línea Azul) - Implementation Guide

## Overview

The **Blue Line** (Línea Azul) is an automated system for managing LLUCH material-supplier homologation records. It represents the internal homologation specification for a material-supplier pair (e.g., LLUCH 103721) and defines Lluch's expectations for each ingredient.

## Key Concepts

### What is the Blue Line?

The Blue Line is a comprehensive record containing **446 configurable fields** that define the specifications and properties of a material-supplier combination. It serves as:

1. **Homologation Reference**: The definitive specification for what Lluch expects from an ingredient
2. **SAP Integration Point**: Bidirectional synchronization with SAP Composite system
3. **Quality Standard**: Baseline for evaluating new homologations

### Material Types

The system recognizes two material types:

- **Z001 (Provisional - Worst Case)**: Data estimated from supplier information (provisional)
- **Z002 (Homologated - Analyzed)**: Data from actual Lluch laboratory analysis

### SAP Status Codes

Materials can have different SAP statuses that determine sync behavior:

- **Z1 (Active/Validated)**: Blue Line data is pushed **TO** SAP Composite
- **Z2 (Provisional)**: Composite data is pulled **FROM** SAP to Blue Line

## Eligibility Rules

A material-supplier pair is eligible for Blue Line creation when **ALL** of the following conditions are met:

1. **Regulatory Approval**: Must have `APC` (Approved Conditionally) OR `APR` (Approved Regulatory) status in the Regulatory section
2. **No Technical Rejection**: Must NOT have `REJ` (Rejected) status in the Technical section
3. **Purchase History**: Must have at least one purchase or sample request in the last **3 years**

### Exclusion States

Homologation records in these states are **excluded** from Blue Line calculation:

- `CAN` - Cancelled
- `REJ` - Rejected
- `EXP` - Expired

### Single Provider Rule

If a material has only one supplier and all homologation records go to CAN/REJ/EXP states, the Blue Line record will be **deleted** or **emptied**.

## Architecture

### Backend Components

#### Models

1. **BlueLine** (`backend/app/models/blue_line.py`)
   - Stores the 446 fields as JSON
   - Tracks material type (Z001/Z002)
   - Manages sync status with SAP
   - Unique constraint on material_id + supplier_code

2. **BlueLineFieldLogic** (`backend/app/models/blue_line_field_logic.py`)
   - Configures logic for each of the 446 fields
   - Supports different logic per material type
   - Priority-based execution order

3. **Material** (Extended)
   - Added fields: `sap_status`, `supplier_code`, `lluch_reference`, `last_purchase_date`, `is_blue_line_eligible`

4. **ApprovalWorkflow** (Extended)
   - Added fields: `section`, `regulatory_status`, `technical_status`
   - Extended status enum with Blue Line states (APC, APR, REJ, CAN, EXP, INC, REA, RUN, VAL)

#### Services

1. **BlueLineCalculator** (`backend/app/services/blue_line_calculator.py`)
   - Main calculation engine
   - Checks eligibility based on rules
   - Applies field logic to calculate all 446 fields
   - Determines material type (Z001 vs Z002)
   - Aggregates homologation records

2. **BlueLineSyncService** (`backend/app/services/blue_line_sync_service.py`)
   - Bidirectional SAP synchronization
   - `sync_to_sap()`: Z1 materials → SAP Composite
   - `import_from_sap()`: Z2 materials ← SAP Composite
   - Validates sync eligibility
   - Transforms data between formats

#### ERP Adapter Extensions

New methods added to `ERPAdapter`:

- `get_purchase_history_last_n_years()`: Check 3-year purchase criterion
- `get_material_sap_status()`: Get Z1/Z2/Z001/Z002 status
- `sync_blue_line_to_composite()`: Send Blue Line to SAP
- `import_composite_data()`: Fetch SAP Composite data
- `get_homologation_records()`: Fetch approval records

### API Endpoints

**Blue Line Management**:
- `POST /api/blue-line/calculate` - Calculate Blue Line for material-supplier pair
- `GET /api/blue-line/{blue_line_id}` - Get Blue Line by ID
- `GET /api/blue-line/material/{material_id}` - Get all Blue Lines for material
- `GET /api/blue-line/material/{material_id}/supplier/{supplier_code}` - Get specific Blue Line
- `GET /api/blue-line` - List all Blue Lines (with filters)
- `DELETE /api/blue-line/{blue_line_id}` - Delete Blue Line

**SAP Synchronization**:
- `POST /api/blue-line/{blue_line_id}/sync-to-sap` - Manual sync to SAP (Z1)
- `POST /api/blue-line/material/{material_id}/import-from-sap` - Manual import from SAP (Z2)

**Eligibility**:
- `GET /api/blue-line/eligible-materials/list` - List all eligible materials
- `GET /api/blue-line/check-eligibility/material/{material_id}/supplier/{supplier_code}` - Check specific eligibility

**Field Logic Configuration**:
- `POST /api/blue-line/field-logic` - Create field logic
- `GET /api/blue-line/field-logic` - List all field logics
- `GET /api/blue-line/field-logic/{id}` - Get specific field logic
- `PUT /api/blue-line/field-logic/{id}` - Update field logic
- `DELETE /api/blue-line/field-logic/{id}` - Delete field logic
- `POST /api/blue-line/field-logic/bulk-import` - Bulk import field logics

### Automation (Celery Tasks)

1. **auto_generate_blue_line_on_approval**
   - Triggered when workflow reaches APC/APR state
   - Automatically generates or updates Blue Line

2. **check_and_update_purchase_history**
   - Runs daily at 1 AM
   - Checks ERP for purchase history
   - Updates `last_purchase_date` for materials

3. **periodic_blue_line_sync**
   - Runs every hour
   - Syncs all pending Blue Lines to SAP

4. **recalculate_blue_lines_on_status_change**
   - Triggered when status changes to CAN/REJ/EXP
   - Recalculates or deletes Blue Line as needed

5. **initial_blue_line_generation**
   - One-time bulk generation for existing materials
   - Processes in batches to avoid overload

6. **sync_z2_materials_from_sap**
   - Runs daily at 4 AM
   - Imports composite data from SAP for Z2 materials

## Field Logic Configuration

### Logic Expression Format

Field logic is defined as JSON with different types of expressions:

#### 1. Source-based Logic

```json
{
  "source": "material.name"
}
```

Extracts value directly from a source (material, composite, etc.)

#### 2. Fixed Value Logic

```json
{
  "fixed_value": "LLUCH"
}
```

Sets a constant value for the field.

#### 3. Calculation Logic

```json
{
  "calculation": {
    "type": "count",
    "source": "composites"
  }
}
```

Performs calculations on data.

#### 4. Conditional Logic

```json
{
  "expression": "IF composite.origin == 'LAB' THEN composite.components ELSE []"
}
```

Complex conditional expressions (to be implemented with rules engine).

### Example Field Logic Configurations

```python
# Field: material_name
{
  "field_name": "material_name",
  "field_type": "text",
  "material_type_filter": "ALL",
  "logic_expression": {
    "source": "material.name"
  },
  "priority": 1
}

# Field: supplier_reference
{
  "field_name": "supplier_reference",
  "field_type": "text",
  "material_type_filter": "ALL",
  "logic_expression": {
    "source": "supplier_code"
  },
  "priority": 2
}

# Field: lluch_company
{
  "field_name": "lluch_company",
  "field_type": "text",
  "material_type_filter": "ALL",
  "logic_expression": {
    "fixed_value": "LLUCH"
  },
  "priority": 3
}

# Field: composite_count
{
  "field_name": "composite_count",
  "field_type": "number",
  "material_type_filter": "ALL",
  "logic_expression": {
    "calculation": {
      "type": "count",
      "source": "composites"
    }
  },
  "priority": 10
}
```

### Bulk Import Field Logics

You can bulk import field logic configurations via the API:

```bash
POST /api/blue-line/field-logic/bulk-import
Content-Type: application/json

{
  "overwrite_existing": false,
  "field_logics": [
    {
      "field_name": "field1",
      "field_type": "text",
      ...
    },
    {
      "field_name": "field2",
      "field_type": "number",
      ...
    }
  ]
}
```

## Usage Examples

### 1. Calculate Blue Line for a Material

```python
import requests

response = requests.post('http://localhost:8000/api/blue-line/calculate', json={
    "material_id": 123,
    "supplier_code": "SUP001",
    "force_recalculate": False
})

blue_line = response.json()
print(f"Blue Line ID: {blue_line['id']}")
print(f"Material Type: {blue_line['material_type']}")
print(f"Sync Status: {blue_line['sync_status']}")
```

### 2. Check Eligibility

```python
response = requests.get(
    'http://localhost:8000/api/blue-line/check-eligibility/material/123/supplier/SUP001'
)

eligibility = response.json()
print(f"Eligible: {eligibility['is_eligible']}")
print(f"Reasons: {eligibility['reasons']}")
```

### 3. Sync to SAP (Z1 Material)

```python
response = requests.post(
    'http://localhost:8000/api/blue-line/456/sync-to-sap'
)

result = response.json()
print(f"Success: {result['success']}")
print(f"Message: {result['message']}")
```

### 4. Import from SAP (Z2 Material)

```python
response = requests.post(
    'http://localhost:8000/api/blue-line/material/123/import-from-sap'
)

result = response.json()
print(f"Success: {result['success']}")
```

## Frontend Usage

### Blue Line Management Page

Navigate to `/blue-line` to:
- View all Blue Line records
- Filter by material type, sync status
- See summary statistics
- Access detailed views

### Blue Line Detail Page

Navigate to `/blue-line/{id}` to:
- View all 446 fields organized by category
- See material and Blue Line information
- Manually trigger sync operations
- View calculation metadata

### Field Logic Configuration

Navigate to `/blue-line/field-logic` to:
- Manage the 446 field logic configurations
- Create, edit, activate/deactivate field logics
- Bulk import configurations
- View by category and material type

## Database Migration

To apply the Blue Line database changes:

```bash
cd backend
alembic upgrade head
```

This will:
- Add new columns to `materials` and `approval_workflows` tables
- Create `blue_lines` and `blue_line_field_logics` tables
- Create necessary indexes and constraints

## Configuration

Add to your `.env` file:

```bash
# Blue Line Settings
BLUE_LINE_PURCHASE_LOOKBACK_YEARS=3
BLUE_LINE_AUTO_SYNC_ENABLED=true
BLUE_LINE_SYNC_INTERVAL_MINUTES=60

# SAP Integration
SAP_COMPOSITE_API_URL=https://sap-api.example.com
SAP_COMPOSITE_API_KEY=your-api-key-here

# ERP Integration (for purchase history)
ERP_API_URL=https://erp-api.example.com
ERP_API_KEY=your-erp-api-key
```

## Monitoring and Troubleshooting

### Check Celery Tasks

```bash
# View scheduled tasks
celery -A app.core.celery_app inspect scheduled

# View active tasks
celery -A app.core.celery_app inspect active

# View task stats
celery -A app.core.celery_app inspect stats
```

### Common Issues

#### Blue Line Not Generated

1. Check eligibility: `GET /api/blue-line/check-eligibility/material/{id}/supplier/{code}`
2. Verify purchase history in last 3 years
3. Check approval workflow states (need APC/APR in Regulatory, no REJ in Technical)

#### Sync Failures

1. Check `sync_error_message` field in Blue Line record
2. Verify ERP/SAP API credentials in `.env`
3. Check network connectivity to SAP systems
4. Review backend logs for detailed error messages

#### Field Logic Not Applied

1. Verify field logic is active: `is_active=true`
2. Check material_type_filter matches (Z001, Z002, or ALL)
3. Verify priority order
4. Check logic_expression format

## Future Enhancements

1. **Advanced Rules Engine**: Implement more sophisticated expression evaluation (e.g., using Python's `eval` safely or a DSL)
2. **Field Dependencies**: Support fields that depend on other calculated fields
3. **Validation Engine**: Validate field values against constraints
4. **Audit Trail**: Complete history of Blue Line changes
5. **Export/Import**: Export Blue Line data to Excel/PDF
6. **Approval Workflow**: Add approval process for Blue Line changes
7. **Notifications**: Email/SMS notifications for sync failures or eligibility changes

## Support

For questions or issues:
- Review API documentation: http://localhost:8000/docs
- Check logs: `docker-compose logs backend`
- Review this guide and ARCHITECTURE.md

---

**Version:** 1.0.0  
**Last Updated:** October 27, 2025

