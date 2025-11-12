# Sistema AI de Validación y Homologación con Lógicas de Línea Azul

## 📋 Resumen

Se ha implementado un sistema completo de validación AI y homologación automatizada que incluye:

1. **Validación de Coherencia AI** de cuestionarios
2. **Aplicación automática de lógicas CSV** a líneas azules
3. **Extracción automática de composites** desde PDFs con OCR
4. **Comparación y promediado de composites** para actualizaciones Z1/Z2
5. **Flujos automatizados** de homologación y re-homologación

## 🏗️ Arquitectura Implementada

### Modelos de Datos (Backend)

#### Composite Model - Nuevos Campos
```python
composite_type: Enum(Z1, Z2)  # Z1: documentos, Z2: laboratorio
questionnaire_id: Integer     # Link a cuestionario específico
source_documents: JSON         # PDFs origen
extraction_confidence: Float   # Score de confianza 0-100
```

#### Questionnaire Model - Nuevos Campos
```python
ai_coherence_score: Integer           # Score coherencia 0-100
ai_coherence_details: JSON            # [{field, issue, severity}]
attached_documents: JSON              # Documentos subidos
```

### Servicios Backend

#### 1. `QuestionnaireCoherenceValidator`
**Ubicación:** `backend/app/services/questionnaire_coherence_validator.py`

Valida coherencia lógica del cuestionario detectando contradicciones:
- ✅ Natural 100% vs contiene aditivos
- ✅ Vegano vs origen animal
- ✅ Organic vs pesticidas
- ✅ GMO consistencia
- ✅ RSPO certificación
- ✅ Halal/Kosher vs ingredientes prohibidos

**Uso:**
```python
validator = QuestionnaireCoherenceValidator(db)
score, issues = validator.validate_coherence(questionnaire_id)
# score: 0-100
# issues: [{field, issue, severity: "critical"|"warning"|"info"}]
```

#### 2. `BlueLineLogicEngine`
**Ubicación:** `backend/app/services/blue_line_logic_engine.py`

Aplica reglas del CSV de lógicas de línea azul:
- **SAP Logic**: Copia datos de SAP
- **Concatenate Logic**: Une valores de múltiples proveedores
- **Worst Case Logic**: Aplica jerarquía de peor caso
- **Manual Logic**: Deja vacío para entrada manual
- **Blocked Logic**: Campos no editables

**Reglas Codificadas:**
- 50+ campos con lógica Z001 (provisional)
- 50+ campos con lógica Z002 (definitivo)
- Jerarquías worst-case: YES_NA_NO y NO_NA_YES

**Uso:**
```python
engine = BlueLineLogicEngine(db)
responses = engine.create_blue_line_from_questionnaire(
    material_id=123,
    questionnaire_id=456,
    material_type=BlueLineMaterialType.Z001
)
```

#### 3. `CompositeExtractorAI`
**Ubicación:** `backend/app/services/composite_extractor_ai.py`

Extrae composición química de PDFs usando OCR:
- 📄 Soporta PDFs con texto y escaneados
- 🔍 Detección de tablas de composición
- 🧪 Extracción de CAS numbers, nombres, porcentajes
- ✨ Validación automática (suma ~100%)

**Tecnologías:**
- PyMuPDF para extracción de texto
- pytesseract + OCR para PDFs escaneados
- OpenCV para preprocesamiento de imagen
- Regex patterns para CAS y porcentajes

**Uso:**
```python
extractor = CompositeExtractorAI()
components, confidence = extractor.extract_from_pdfs([
    "path/to/coa1.pdf",
    "path/to/coa2.pdf"
])
# components: [{component_name, cas_number, percentage, confidence}]
# confidence: 0-100
```

#### 4. `CompositeComparisonService`
**Ubicación:** `backend/app/services/composite_comparison_service.py`

Compara y promedía composites:
- 🔄 Comparación detallada de dos composites
- ➗ Cálculo de composite promedio (simple average)
- ⚖️ Cálculo de composite ponderado (weighted average)
- 📊 Match score y detección de cambios significativos

**Uso:**
```python
service = CompositeComparisonService(db)

# Comparar
comparison = service.compare_composites(composite_a_id, composite_b_id)
# Returns: {components_added, components_removed, components_changed, match_score}

# Promediar
averaged = service.calculate_average_composite(
    composite_a_id,
    composite_b_id,
    target_material_id
)
```

## 🔌 Endpoints API

### Questionnaires API

#### POST `/api/questionnaires/{id}/validate-coherence`
Valida coherencia del cuestionario con AI.

**Response:**
```json
{
  "questionnaire_id": 123,
  "coherence_score": 85,
  "issues": [
    {
      "field": "q3t1s4f44",
      "issue": "Product claims to be 100% natural but contains additives",
      "severity": "critical"
    }
  ],
  "status": "validated"
}
```

#### POST `/api/questionnaires/{id}/upload-documents`
Sube PDFs para extracción de composite.

**Body:** `multipart/form-data` con archivos PDF

**Response:**
```json
{
  "questionnaire_id": 123,
  "uploaded_files": [
    {
      "filename": "coa.pdf",
      "path": "/uploads/questionnaires/123/20251031_120000_coa.pdf",
      "upload_date": "2025-10-31T12:00:00",
      "type": "pdf"
    }
  ],
  "total_documents": 1
}
```

#### POST `/api/questionnaires/{id}/extract-composite`
Extrae composite de documentos subidos usando AI.

**Response:**
```json
{
  "questionnaire_id": 123,
  "composite_id": 456,
  "composite_type": "Z1",
  "components_count": 12,
  "extraction_confidence": 87.5,
  "status": "extracted"
}
```

#### GET `/api/questionnaires/{id}/composite`
Obtiene composite asociado al cuestionario.

### Composites API

#### POST `/api/composites/average`
Crea composite promedio de dos composites (para actualizar Z1).

**Query Params:**
- `composite_a_id`: ID composite existente
- `composite_b_id`: ID nuevo composite
- `target_material_id`: ID material destino

**Response:** `CompositeResponse`

#### POST `/api/composites/compare-detailed`
Compara dos composites en detalle.

**Query Params:**
- `composite_a_id`: Primer composite
- `composite_b_id`: Segundo composite

**Response:**
```json
{
  "composite_a_id": 1,
  "composite_b_id": 2,
  "components_added": [...],
  "components_removed": [...],
  "components_changed": [
    {
      "component_name": "Linalool",
      "cas_number": "78-70-6",
      "old_percentage": 35.5,
      "new_percentage": 38.2,
      "change": 2.7,
      "change_percent": 7.6
    }
  ],
  "significant_changes": true,
  "total_change_score": 15.3,
  "match_score": 84.7
}
```

## 📖 Flujos de Uso

### Flujo 1: Nuevo Material sin Línea Azul

1. **Importar cuestionario** → `POST /questionnaires/import/json`
2. **Validar coherencia AI** → `POST /questionnaires/{id}/validate-coherence`
3. **Revisar y aprobar** issues de coherencia (manual)
4. **Subir documentos** → `POST /questionnaires/{id}/upload-documents`
5. **Extraer composite AI** → `POST /questionnaires/{id}/extract-composite`
6. **Crear línea azul** → `POST /questionnaires/{id}/create-blue-line`
   - Sistema aplica automáticamente lógicas CSV
   - Se vincula composite Z1 generado

### Flujo 2: Re-homologación (Material con Línea Azul Existente)

1. **Importar cuestionario** → Sistema detecta línea azul existente
2. **Comparar con línea azul** → Automático al importar
3. **Validar coherencia** → `POST /questionnaires/{id}/validate-coherence`
4. **Revisar diferencias** (manual) → Ver validations/incidents
5. **Aprobar cuestionario** (manual)
6. **Subir documentos** → `POST /questionnaires/{id}/upload-documents`
7. **Extraer composite** → `POST /questionnaires/{id}/extract-composite`
8. **Comparar composites** → `POST /composites/compare-detailed`
   - Compara nuevo composite con Z1/Z2 existente
9. **Decidir acción según tipo**:
   
   **Si Línea Azul tiene Z1:**
   - Opción: Actualizar Z1 con promedio
   - `POST /composites/average` → Crea nuevo Z1 promediado
   - Reemplaza composite de línea azul
   
   **Si Línea Azul tiene Z2:**
   - Solo informativo (Z2 es definitivo)
   - No se modifica línea azul

10. **Aprobar material-supplier** → Marca como re-homologado

### Flujo 3: Actualizar Z1 a Z2 (Laboratorio)

1. **Importar análisis laboratorio** → Crear composite origen=LAB
2. **Marcar como Z2** → `composite_type = CompositeType.Z2`
3. **Vincular a línea azul** → Reemplaza composite Z1
4. **Línea azul ahora es definitiva** → No más actualizaciones automáticas

## 🔧 Configuración Requerida

### Dependencias Adicionales

Agregadas a `requirements.txt`:
```
# PDF and OCR
pytesseract==0.3.10
pdf2image==1.16.3
opencv-python==4.8.1.78
Pillow==10.1.0
PyMuPDF==1.23.8
fuzzywuzzy==0.18.0
python-Levenshtein==0.23.0
```

### Instalación de Tesseract OCR

**Mac:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki

### Migración de Base de Datos

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

## 📊 Lógicas de Línea Azul Implementadas

### Tipos de Lógica

1. **SAP**: Datos desde SAP (material_name, CAS, EINECS, FEMA, etc.)
2. **CONCATENATE**: Une valores de múltiples proveedores (país origen, nombre botánico)
3. **WORST_CASE**: Aplica jerarquía (natural, GMO, certificaciones)
4. **MANUAL**: Campos vacíos para entrada manual (la mayoría en Z002)
5. **BLOCKED**: No editables (fechas sistema)

### Worst Case Hierarchies

**YES_NA_NO** (Yes es peor):
- `contains_additives`
- `contains_gmo`
- `contains_nanomaterials`
- `contains_pah`
- `tested_on_animals`

**NO_NA_YES** (No es peor):
- `is_natural_100`
- `is_pure_100`
- `vegan`
- `kosher_certified`
- `halal_certified`

### Campos Mapeados

**50+ campos** del cuestionario Lluch mapeados a lógicas específicas:
- Identificadores (SAP)
- Certificaciones (Worst Case)
- Origen y botánica (Concatenate)
- Características producto (Worst Case)
- Restricciones (Worst Case)

Ver `backend/app/services/blue_line_rules.py` para lista completa.

## ⚙️ Configuración de Lógicas

Para modificar o agregar reglas de línea azul, editar:

```python
# backend/app/services/blue_line_rules.py

BLUE_LINE_FIELD_RULES = {
    "q3t1s2f23": {
        "blue_line_field": "cas_number",
        "logic_z001": LogicType.SAP,
        "logic_z002": LogicType.SAP
    },
    "q3t1s4f44": {
        "blue_line_field": "is_natural_100",
        "logic_z001": LogicType.WORST_CASE,
        "logic_z002": LogicType.MANUAL,
        "worst_case": WorstCaseHierarchy.NO_NA_YES
    }
}
```

## 🧪 Testing

### Test de Coherencia
```python
# test_coherence_validation.py
from app.services.questionnaire_coherence_validator import QuestionnaireCoherenceValidator

def test_natural_vs_additives():
    validator = QuestionnaireCoherenceValidator(db)
    score, issues = validator.validate_coherence(questionnaire_id)
    assert score >= 0 and score <= 100
    assert len(issues) > 0 if contradictions else len(issues) == 0
```

### Test de Extracción
```python
# test_composite_extraction.py
from app.services.composite_extractor_ai import CompositeExtractorAI

def test_pdf_extraction():
    extractor = CompositeExtractorAI()
    components, confidence = extractor.extract_from_pdfs(["test_coa.pdf"])
    assert len(components) > 0
    assert confidence > 0
    total = sum(c['percentage'] for c in components)
    assert 95 <= total <= 105  # ~100%
```

## 📝 Notas Importantes

### Tipos de Composite

- **Z1 (Provisional)**: Generado de documentos supplier, puede actualizarse
- **Z2 (Definitivo)**: Análisis laboratorio Lluch, inmutable

### Actualizaciones de Z1

Cuando llega nuevo cuestionario con composite:
1. Comparar con Z1 existente
2. Si diferencias < 5%: Match aceptable
3. Si diferencias >= 5%: Promediar y crear nuevo Z1
4. Método: Simple average de porcentajes

### Conversión Z1 → Z2

Una vez convertido a Z2:
- ✅ No más actualizaciones automáticas
- ✅ Datos definitivos de laboratorio
- ✅ Línea azul bloqueada para composites

## 🚀 Próximos Pasos

Para completar el sistema:

1. **Frontend - Questionnaire Detail Page**
   - Botones: Validar Coherencia, Subir Documentos, Extraer Composite
   - Mostrar coherence score y issues
   - Flujo visual de creación línea azul

2. **Frontend - Composite Comparison Component**
   - Vista lado a lado de composites
   - Highlighting de diferencias
   - Botón "Actualizar Z1" o "Mantener actual"

3. **Frontend - Blue Line Detail**
   - Badge Z1/Z2
   - Botón "Upgrade to Z2" (solo si Z1)
   - Modal import composite Z2 manual

4. **Notificaciones y Alertas**
   - Email cuando composite tiene discrepancias > 5%
   - Alert cuando coherence score < 70

## 📚 Documentación Adicional

- `BLUE_LINE_GUIDE.md` - Guía original de línea azul
- `QUESTIONNAIRE_SYSTEM_README.md` - Sistema de cuestionarios
- `data/rules blue line/03_Lógicas Línea Azul.csv` - CSV de lógicas completo

## 🐛 Troubleshooting

### OCR no funciona
- Verificar instalación Tesseract: `tesseract --version`
- Verificar PDFs no estén corruptos
- Revisar logs en `backend/backend.log`

### Percentajes no suman 100%
- Normal con variación ±2%
- Sistema normaliza automáticamente
- Si > 5% diferencia, revisa calidad PDF

### Lógicas no se aplican
- Verificar fieldCode existe en `BLUE_LINE_FIELD_RULES`
- Revisar tipo de material (Z001 vs Z002)
- Check SAP data disponible

---

**Sistema implementado por:** IA Assistant  
**Fecha:** Octubre 31, 2025  
**Versión:** 1.0.0












