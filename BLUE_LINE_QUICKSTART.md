# Blue Line - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Apply Database Migration

```bash
cd backend
alembic upgrade head
```

This creates the Blue Line tables and adds necessary columns.

### Step 2: Update Configuration

Add to your `.env` file:

```bash
# Blue Line Settings
BLUE_LINE_PURCHASE_LOOKBACK_YEARS=3
BLUE_LINE_AUTO_SYNC_ENABLED=true
BLUE_LINE_SYNC_INTERVAL_MINUTES=60

# SAP/ERP Integration (update with your credentials)
ERP_API_URL=https://your-erp-api.com
ERP_API_KEY=your-erp-api-key
SAP_COMPOSITE_API_URL=https://your-sap-api.com
SAP_COMPOSITE_API_KEY=your-sap-api-key
```

### Step 3: Start the Application

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev

# Terminal 3 - Celery Worker
cd backend
celery -A app.core.celery_app worker --loglevel=info

# Terminal 4 - Celery Beat (scheduled tasks)
cd backend
celery -A app.core.celery_app beat --loglevel=info
```

### Step 4: Configure Field Logic (First Time Only)

Create sample field logic configurations:

```bash
curl -X POST http://localhost:8000/api/blue-line/field-logic \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "material_name",
    "field_label": "Material Name",
    "field_category": "Basic Info",
    "field_type": "text",
    "material_type_filter": "ALL",
    "logic_expression": {"source": "material.name"},
    "priority": 1,
    "is_active": true,
    "description": "Name of the material"
  }'
```

Or bulk import (recommended):

```bash
curl -X POST http://localhost:8000/api/blue-line/field-logic/bulk-import \
  -H "Content-Type: application/json" \
  -d @field_logic_config.json
```

### Step 5: Access the UI

1. Open browser: `http://localhost:5173`
2. Navigate to "Línea Azul" in the sidebar
3. Explore Blue Line records, field logic, and sync status

## 💡 Common Tasks

### Calculate Blue Line for a Material

**Via API:**
```bash
curl -X POST http://localhost:8000/api/blue-line/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "material_id": 1,
    "supplier_code": "SUP001",
    "force_recalculate": false
  }'
```

**Via UI:**
1. Go to Materials page
2. Select a material with supplier_code
3. Material Detail → "Calculate Blue Line" button

### Check Eligibility

```bash
curl http://localhost:8000/api/blue-line/check-eligibility/material/1/supplier/SUP001
```

Response:
```json
{
  "material_id": 1,
  "supplier_code": "SUP001",
  "is_eligible": true,
  "reasons": [],
  "has_purchase_history": true,
  "regulatory_status_ok": true,
  "technical_status_ok": true
}
```

### Sync to SAP (Z1 Materials)

```bash
curl -X POST http://localhost:8000/api/blue-line/123/sync-to-sap
```

### Import from SAP (Z2 Materials)

```bash
curl -X POST http://localhost:8000/api/blue-line/material/1/import-from-sap
```

### List All Blue Lines

```bash
curl http://localhost:8000/api/blue-line
```

With filters:
```bash
curl "http://localhost:8000/api/blue-line?material_type=Z001&sync_status=PENDING"
```

## 🔧 Setup for Testing

### Create Test Material with Blue Line

```python
import requests

# 1. Create material with SAP fields
material = requests.post('http://localhost:8000/api/materials', json={
    "reference_code": "TEST-001",
    "name": "Test Material for Blue Line",
    "supplier": "Test Supplier",
    "supplier_code": "SUP-TEST-001",
    "sap_status": "Z1",
    "lluch_reference": "LLUCH-TEST-001",
    "material_type": "NATURAL",
    "cas_number": "123-45-6"
}).json()

print(f"Created material: {material['id']}")

# 2. Create a composite (so it becomes Z002 type)
# ... create chromatographic analysis and composite ...

# 3. Approve composite workflow with APC status
# ... set workflow to APC in Regulatory section ...

# 4. Set last purchase date (within 3 years)
import requests
from datetime import datetime, timedelta

purchase_date = (datetime.now() - timedelta(days=180)).isoformat()
requests.put(f'http://localhost:8000/api/materials/{material["id"]}', json={
    "last_purchase_date": purchase_date
})

# 5. Calculate Blue Line
blue_line = requests.post('http://localhost:8000/api/blue-line/calculate', json={
    "material_id": material['id'],
    "supplier_code": "SUP-TEST-001",
    "force_recalculate": False
}).json()

print(f"Created Blue Line: {blue_line['id']}")
print(f"Material Type: {blue_line['material_type']}")
print(f"Sync Status: {blue_line['sync_status']}")
print(f"Fields Count: {len(blue_line['blue_line_data'])}")
```

## 📝 Minimum Field Logic Setup

To get started quickly, configure at least these essential fields:

```json
[
  {
    "field_name": "material_reference",
    "field_type": "text",
    "material_type_filter": "ALL",
    "logic_expression": {"source": "material.reference_code"},
    "priority": 1,
    "is_active": true
  },
  {
    "field_name": "material_name",
    "field_type": "text",
    "material_type_filter": "ALL",
    "logic_expression": {"source": "material.name"},
    "priority": 2,
    "is_active": true
  },
  {
    "field_name": "supplier_code",
    "field_type": "text",
    "material_type_filter": "ALL",
    "logic_expression": {"source": "supplier_code"},
    "priority": 3,
    "is_active": true
  },
  {
    "field_name": "lluch_company",
    "field_type": "text",
    "material_type_filter": "ALL",
    "logic_expression": {"fixed_value": "LLUCH"},
    "priority": 4,
    "is_active": true
  },
  {
    "field_name": "cas_number",
    "field_type": "text",
    "material_type_filter": "ALL",
    "logic_expression": {"source": "material.cas_number"},
    "priority": 5,
    "is_active": true
  }
]
```

Save as `minimal_fields.json` and import:
```bash
curl -X POST http://localhost:8000/api/blue-line/field-logic/bulk-import \
  -H "Content-Type: application/json" \
  -d @minimal_fields.json
```

## 🎯 Verification Checklist

- [ ] Database migration applied successfully
- [ ] Configuration updated in `.env`
- [ ] Backend API running on port 8000
- [ ] Frontend running on port 5173
- [ ] Celery worker running
- [ ] Celery beat scheduler running
- [ ] At least 5 field logics configured
- [ ] Test material created with supplier_code
- [ ] Blue Line calculated successfully
- [ ] UI accessible and showing Blue Line menu

## 🐛 Troubleshooting

### Blue Line Not Generated

**Check eligibility:**
```bash
curl http://localhost:8000/api/blue-line/check-eligibility/material/{id}/supplier/{code}
```

Common reasons:
- No purchase in last 3 years → Set `last_purchase_date`
- No APC/APR in Regulatory → Update workflow `regulatory_status`
- Has REJ in Technical → Update workflow `technical_status`

### Sync Failing

Check:
1. ERP/SAP credentials in `.env`
2. Network connectivity
3. Backend logs: `docker-compose logs backend` or check console
4. Sync error message in Blue Line record

### No Field Logics

Configure at least minimal fields first. Without field logics, Blue Line will have empty `blue_line_data`.

### Celery Tasks Not Running

Ensure both worker AND beat are running:
```bash
# Check processes
ps aux | grep celery

# Check scheduled tasks
celery -A app.core.celery_app inspect scheduled
```

## 📚 Next Steps

1. Review [BLUE_LINE_GUIDE.md](BLUE_LINE_GUIDE.md) for complete documentation
2. Configure all 446 fields based on business rules
3. Set up production ERP/SAP credentials
4. Configure monitoring and alerts
5. Test with real data
6. Train users on the UI

## 🆘 Need Help?

- **API Documentation**: http://localhost:8000/docs
- **Backend Logs**: `docker-compose logs -f backend`
- **Frontend Console**: Browser Developer Tools
- **Full Guide**: [BLUE_LINE_GUIDE.md](BLUE_LINE_GUIDE.md)

---

**Quick Start Version:** 1.0  
**Last Updated:** October 27, 2025

