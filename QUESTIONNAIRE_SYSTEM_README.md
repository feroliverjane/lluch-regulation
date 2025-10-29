# Sistema de Cuestionarios de Homologación

Sistema completo para gestión automatizada de cuestionarios de homologación con validación inteligente mediante IA, basado en el formato real de cuestionarios de Lluch.

## 📋 Características Principales

### 1. Estructura Real de Lluch
- **174 campos** extraídos del formato JSON real
- **Código de campo** (fieldCode): formato `q{Q}t{TAB}s{SECTION}f{FIELD}`
  - Ejemplo: `q3t1s2f15` = Questionnaire 3, Tab 1, Section 2, Field 15
- **16 tipos de campo** diferentes:
  - `yesNoComments` (67 campos) - Preguntas de cumplimiento con comentarios
  - `inputText` (37 campos) - Entrada de texto
  - `yesNoNA` (25 campos) - Sí/No/No Aplica
  - `lov` (14 campos) - Lista de valores/dropdowns
  - `inputNumber` (7 campos) - Números
  - `checkTableMatCasPercen` (5 campos) - Tablas material/CAS/porcentaje
  - Y 10 tipos más para tablas complejas

### 2. Organización
- **6 Tabs** (pestañas principales)
- **31 Secciones** organizadas por temas:
  - Información del proveedor y producto
  - Certificaciones (Kosher, Halal, Food Grade)
  - Origen y fuente botánica
  - Cumplimiento regulatorio (EU, US, Asia)
  - Parámetros de calidad
  - Alérgenos y seguridad alimentaria
  - Sostenibilidad y renovabilidad
  - Almacenamiento y vida útil

### 3. Validación Automática
- **Comparación con Línea Azul**: 23 campos críticos mapeados
- **Detección de desviaciones**: Cálculo automático de porcentajes
- **Clasificación por severidad**: INFO, WARNING, CRITICAL
- **Generación de incidentes**: Automática para desviaciones críticas

### 4. AI Mockup Inteligente
- **Risk Score**: 0-100 basado en validaciones
- **Recomendaciones**: APPROVE, REVIEW, REJECT
- **Confianza**: 75-90% según contexto
- **Resúmenes contextuales**: Generados según tipo de cuestionario y desviaciones

## 🗂️ Archivos y Ejemplos

### Archivos JSON Reales
```
data/questionnaires/
├── JSON Z1_Basicilo_MPE.txt              (Real: 235 campos, requestId: 2027)
├── template_lluch_standard.json           (Template extraído: 174 campos)
└── BASIL0003_exported.csv                 (Exportado a CSV para Excel)
```

### Ejemplos Didácticos CSV
```
data/questionnaires/
├── DEMO-MAT-001_v1_initial_homologation.csv   (Aprobado perfecto)
├── DEMO-MAT-001_v2_rehomologation.csv         (Con desviaciones)
└── PLANTILLA_CUESTIONARIO_HOMOLOGACION.csv    (Plantilla en blanco)
```

## 🔧 Scripts Disponibles

### 1. Análisis de JSON Real
```bash
python ejemplo_importar_json_real.py
```
**Muestra**:
- Estructura del JSON (235 campos)
- Distribución de tipos de campo
- Extracción de metadata
- Organización por secciones
- Campos críticos identificados
- Conversión a CSV

### 2. Importar y Procesar JSON
```bash
cd backend
python app/scripts/import_and_process_real_json.py
```
**Proceso**:
1. Importa JSON real (BASIL0003)
2. Crea material y Blue Line
3. Valida 174 campos
4. Genera análisis IA
5. Crea incidentes automáticos

### 3. Crear Template desde JSON
```bash
cd backend
python app/scripts/create_template_from_json.py
```
**Genera**:
- Template en DB con 174 preguntas
- Estructura organizada por tabs/sections
- Validación rules por tipo de campo
- Export JSON para documentación

### 4. Demo End-to-End Completo
```bash
cd backend
python app/scripts/generate_e2e_demo.py
```
**Demuestra**:
- Homologación inicial (v1)
- Rehomologación (v2) con cambios
- Validación automática
- IA detectando problemas
- Resolución de incidentes
- Aprobación workflow

## 🎯 Workflow Automatizado

```
📄 JSON del Proveedor (235 campos)
    ↓
🔍 Parser extrae fieldCodes + valores
    ↓
📋 Template define estructura y validaciones
    ↓
💾 Questionnaire almacena respuestas completas
    ↓
🗺️ FieldMapper traduce fieldCodes → Blue Line
    ↓
🤖 Validación automática (23 campos críticos)
    │
    ├─ ✅ Todo OK → AI Score bajo → APPROVE
    ├─ ⚠️ Warnings → AI Score medio → REVIEW
    └─ 🔴 Críticos → AI Score alto → REJECT + Incidentes
    ↓
👤 Revisión Manual
    │
    ├─ Escalar a proveedor
    ├─ Anular con justificación
    └─ Resolver
    ↓
✅ Aprobar → Update Blue Line → Sync SAP
```

## 📊 Mapeo de Campos Críticos

### Información Básica
- `q3t1s2f15` → Supplier Name ⭐ CRITICAL
- `q3t1s2f16` → Product Name ⭐ CRITICAL
- `q3t1s2f17` → Product Code ⭐ CRITICAL
- `q3t1s2f23` → CAS Number ⭐ CRITICAL

### Certificaciones
- `q3t1s3f27` → Kosher Certificate ⭐ CRITICAL
- `q3t1s3f28` → Halal Certificate ⭐ CRITICAL
- `q3t1s3f29` → Food/Flavour Grade ⭐ CRITICAL

### Origen y Naturaleza
- `q3t1s4f33` → Country of Botanical Origin ⭐ CRITICAL
- `q3t1s4f38` → Botanical Name ⭐ CRITICAL
- `q3t1s4f44` → 100% Natural ⭐ CRITICAL
- `q3t1s4f46` → 100% Pure ⭐ CRITICAL

### Cumplimiento Regulatorio
- `q3t3s6f172` → REACH Registered ⭐ CRITICAL
- `q3t3s20f188` → Cosmetics Regulation Compliant ⭐ CRITICAL
- `q3t4s25f228` → HACCP Certificate ⭐ CRITICAL
- `q3t4s27f242` → EU Regulations Compliant ⭐ CRITICAL

### Alérgenos y Seguridad
- `q3t4s32f265` → Allergen Control Plan ⭐ CRITICAL
- `q3t4s32f267` → May Contain Traces ⭐ CRITICAL
- `q3t6s36f292` → Animal Origin Ingredients ⭐ CRITICAL

### Sostenibilidad
- `q3t8s38f308` → Renewability Percentage

### Almacenamiento
- `q3t1s40f347` → Shelf Life
- `q3t1s40f348` → Storage Temperature

## 🎨 Tipos de Campo Soportados

### Simples
- `inputText` - Texto libre
- `inputNumber` - Números
- `inputTextarea` - Texto largo

### Booleanos
- `yesNoNA` - Sí/No/No Aplica
- `yesNoComments` - Sí/No + Comentarios
- `checkComents` - Checkbox + Comentarios

### Listas
- `lov` - List of Values (dropdown)
- `selectManyMenu` - Selección múltiple
- `selectManyCheckbox` - Checkboxes múltiples

### Tablas Complejas
- `checkTableMatCasPercen` - Material/CAS/Porcentaje
- `tableDescYesNoPercen` - Descripción/Sí-No/Porcentaje
- `tableDescYesNoSubtCASPercent` - Compleja con sustancia/CAS
- `presenceIngredientTablePercentHandlers2` - Alérgenos alimentarios
- `checkTableMatCasAnnexPercen` - Con anexos regulatorios

## 🔌 API Endpoints

### Templates
- `GET /api/questionnaire-templates` - Listar templates
- `GET /api/questionnaire-templates/default` - Template por defecto
- `GET /api/questionnaire-templates/{id}` - Template específico
- `GET /api/questionnaire-templates/{id}/sections` - Organizado por secciones

### Questionnaires
- `POST /api/questionnaires` - Crear nuevo (con template_id opcional)
- `GET /api/questionnaires` - Listar
- `GET /api/questionnaires/{id}` - Ver detalles
- `POST /api/questionnaires/{id}/submit` - Enviar para revisión
- `POST /api/questionnaires/{id}/approve` - Aprobar
- `POST /api/questionnaires/{id}/reject` - Rechazar

### Validaciones e Incidentes
- `GET /api/questionnaires/{id}/validations` - Ver validaciones
- `POST /api/questionnaires/{id}/validate` - Validar manualmente
- `POST /api/questionnaires/{id}/ai-analysis` - Análisis IA
- `GET /api/questionnaires/{id}/incidents` - Ver incidentes
- `POST /api/questionnaires/incidents/{id}/escalate` - Escalar
- `POST /api/questionnaires/incidents/{id}/override` - Anular
- `POST /api/questionnaires/incidents/{id}/resolve` - Resolver

## 📱 Interfaz de Usuario

### Páginas Disponibles
- `/questionnaires` - Lista con filtros
- `/questionnaires/new` - Formulario de creación
- `/questionnaires/{id}` - Detalles con validaciones e incidentes

### Características UI
- ✅ Tabla con información completa
- ✅ Filtros por estado
- ✅ Badges de estado con colores
- ✅ AI Risk Score visual (0-100)
- ✅ Recomendaciones IA con badges
- ✅ Gestión de incidentes integrada
- ✅ Botones de acción contextuales

## 🔍 Ejemplo de Uso

### Importar JSON Real
```python
from app.parsers.questionnaire_json_parser import QuestionnaireJSONParser
from app.core.database import SessionLocal

# Importar
db = SessionLocal()
questionnaire_id = QuestionnaireJSONParser.import_from_json(
    'data/questionnaires/JSON Z1_Basicilo_MPE.txt',
    db,
    material_code='BASIL0003'
)

# El sistema automáticamente:
# 1. Crea material si no existe
# 2. Almacena 174 campos con estructura completa
# 3. Preserva fieldCodes para trazabilidad
```

### Validar y Analizar
```python
from app.services.questionnaire_validation_service import QuestionnaireValidationService
from app.services.questionnaire_ai_service import QuestionnaireAIService

# Validar
validation_service = QuestionnaireValidationService(db)
validations = validation_service.validate_questionnaire(questionnaire_id)

# AI Analysis
ai_service = QuestionnaireAIService(db)
analysis = await ai_service.analyze_risk_profile(questionnaire_id)

# Resultados:
# - validations: Lista de desviaciones detectadas
# - analysis: {"risk_score": 70, "recommendation": "REJECT", ...}
```

## 🎯 Casos de Uso Demostrados

### Caso 1: Homologación Inicial Perfecta
- ✅ Material: DEMO-MAT-001 v1
- ✅ Todos los parámetros OK
- ✅ AI Score: 12/100 (Riesgo bajo)
- ✅ Recommendation: APPROVE
- ✅ Sin incidentes

### Caso 2: Rehomologación con Desviaciones
- ⚠️ Material: DEMO-MAT-001 v2
- 🔴 Pureza bajó 2.6%
- 🔴 Humedad aumentó 467%
- 🔴 Sostenibilidad bajó 27%
- ⚠️ AI Score: 65/100 (Riesgo medio)
- ⚠️ Recommendation: REVIEW
- 🔴 2 incidentes críticos generados

### Caso 3: JSON Real de Lluch
- 📄 Material: BASIL0003 (Basil Essential Oil)
- 📊 174 campos importados con estructura fieldCode
- 🔍 Validación de 23 campos críticos
- 🔴 2 desviaciones detectadas
- 🔴 AI Score: 70/100 (Riesgo alto)
- 🔴 Recommendation: REJECT
- 🔴 2 incidentes auto-generados

## 📦 Archivos Clave

### Backend
```
backend/app/
├── models/
│   ├── questionnaire.py                    (Modelo principal)
│   ├── questionnaire_template.py           (Templates reutilizables)
│   ├── questionnaire_validation.py         (Resultados de validación)
│   └── questionnaire_incident.py           (Gestión de incidentes)
├── parsers/
│   ├── questionnaire_json_parser.py        (Parser formato Lluch)
│   └── questionnaire_csv_parser.py         (Parser CSV simple)
├── services/
│   ├── questionnaire_validation_service.py (Lógica de validación)
│   ├── questionnaire_ai_service.py         (IA mockup/real)
│   └── questionnaire_field_mapper.py       (Mapeo fieldCodes ↔ Blue Line)
├── api/
│   ├── questionnaires.py                   (REST API cuestionarios)
│   └── questionnaire_templates.py          (REST API templates)
└── scripts/
    ├── create_template_from_json.py        (Extrae template de JSON)
    ├── import_and_process_real_json.py     (E2E con JSON real)
    ├── generate_e2e_demo.py                (Demo completo)
    └── generate_questionnaire_dummy_data.py (Datos de prueba)
```

### Frontend
```
frontend/src/pages/
├── Questionnaires.tsx          (Lista con filtros y stats)
├── QuestionnaireDetail.tsx     (Detalles, validaciones, incidentes)
└── QuestionnaireForm.tsx       (Formulario de creación)
```

### Data
```
data/questionnaires/
├── JSON Z1_Basicilo_MPE.txt                          (JSON real)
├── template_lluch_standard.json                      (Template extraído)
├── BASIL0003_exported.csv                            (CSV exportado)
├── DEMO-MAT-001_v1_initial_homologation.csv         (Ejemplo v1)
├── DEMO-MAT-001_v2_rehomologation.csv               (Ejemplo v2)
├── PLANTILLA_CUESTIONARIO_HOMOLOGACION.csv          (Plantilla vacía)
└── README.md                                         (Documentación)
```

## 🚀 Cómo Ejecutar Demos

### Demo 1: JSON Real Completo
```bash
cd backend
python app/scripts/import_and_process_real_json.py
```
**Resultado**: Cuestionario #3 con 174 campos reales, validado y analizado

### Demo 2: End-to-End Workflow
```bash
cd backend  
python app/scripts/generate_e2e_demo.py
```
**Resultado**: Historia completa de DEMO-MAT-001 con v1 y v2

### Demo 3: Análisis de Estructura
```bash
python ejemplo_importar_json_real.py
```
**Resultado**: Análisis detallado del JSON sin importar

## 📊 Estadísticas del Sistema

- **Cuestionarios procesados**: 5+
- **Campos totales gestionados**: 174 (formato Lluch) + 60 (CSV simple)
- **Validaciones realizadas**: 15+
- **Incidentes generados**: 5
- **Templates creados**: 1
- **Materiales demo**: 5
- **Blue Lines**: 7

## 🔮 IA: Mock vs Real

### Actual (Mock)
- ✅ Algoritmo basado en reglas
- ✅ Consistente y predecible
- ✅ Sin costos de API
- ✅ Perfecto para demos

### Futuro (OpenAI)
```python
# Para activar IA real:
ai_service = QuestionnaireAIService(db, use_real_ai=True)

# Implementar en _real_ai_analysis():
import openai
response = await openai.ChatCompletion.acreate(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}]
)
```

## 📖 Documentación Adicional

- `BLUE_LINE_GUIDE.md` - Guía completa de Línea Azul
- `QUESTIONNAIRE_SYSTEM_README.md` - Este archivo
- `data/questionnaires/README.md` - Documentación de CSVs
- `ARCHITECTURE.md` - Arquitectura general del sistema

## 🎁 Estado Actual

✅ **Completamente funcional**:
- [x] Modelos de base de datos
- [x] Parsers JSON y CSV
- [x] Servicios de validación
- [x] IA mockup inteligente
- [x] API REST completa
- [x] Frontend con 3 páginas
- [x] Templates con estructura real
- [x] Mapeo de campos críticos
- [x] Gestión de incidentes
- [x] Workflow de aprobación
- [x] Demos end-to-end

## 📞 Acceso Rápido

- **API Docs**: http://localhost:8000/docs
- **Lista Cuestionarios**: http://localhost:5173/questionnaires
- **Cuestionario Real**: http://localhost:5173/questionnaires/3 (BASIL0003)
- **Blue Line**: http://localhost:5173/blue-line
- **Template API**: http://localhost:8000/api/questionnaire-templates/1

---

**Versión del Sistema**: 1.0.0  
**Última Actualización**: Octubre 2025  
**Formato Base**: Lluch JSON con fieldCodes (235 campos, 31 secciones)

