# Cuestionarios de Homologación - Ejemplos

Este directorio contiene ejemplos de cuestionarios de homologación en formato CSV que simulan los documentos que los proveedores envían a Lluch.

## 📄 Archivos Disponibles

### 1. `DEMO-MAT-001_v1_initial_homologation.csv`
**Cuestionario de Homologación Inicial - Aprobado**

- **Material**: DEMO-MAT-001 (Premium Lavender Essential Oil)
- **Proveedor**: Provence Natural Extracts (PROV-LAV-2024)
- **Versión**: 1
- **Fecha**: 2025-05-01
- **Estado**: Aprobado hace 6 meses
- **Características**:
  - ✅ Todos los parámetros dentro de especificaciones
  - ✅ Pureza: 99.8%
  - ✅ Humedad: 0.15%
  - ✅ Sostenibilidad: 85/100
  - ✅ Sin alérgenos
  - ✅ Certificaciones: Orgánico, Fair Trade, ISO 9001

### 2. `DEMO-MAT-001_v2_rehomologation.csv`
**Cuestionario de Rehomologación - Con Desviaciones**

- **Material**: DEMO-MAT-001 (Premium Lavender Essential Oil)
- **Proveedor**: Provence Natural Extracts (PROV-LAV-2024)
- **Versión**: 2
- **Fecha**: 2025-10-25
- **Motivo**: Renovación anual de homologación
- **Cambios Detectados**:
  - 🔴 **CRÍTICO**: Pureza bajó de 99.8% → 97.2% (-2.6%)
  - 🔴 **CRÍTICO**: Humedad aumentó de 0.15% → 0.85% (+467%)
  - 🔴 **CRÍTICO**: Sostenibilidad bajó de 85 → 62 (-27%)
  - ⚠️ **WARNING**: Nuevo alérgeno detectado (trazas de frutos secos)
  - ⚠️ **WARNING**: Pérdida de certificación Fair Trade
  - ⚠️ Shelf life reducido de 24 → 18 meses

**Explicaciones del Proveedor**:
- Sequía prolongada en 2024 afectó calidad del cultivo
- Instalación compartida con procesamiento de frutos secos desde Sep 2024
- Proceso de recertificación Fair Trade en curso
- Plan de mejora implementado

## 🎯 Uso de los Archivos

### Opción 1: Ver/Analizar el CSV
```bash
# Abrir en Excel/LibreOffice para revisión manual
open data/questionnaires/DEMO-MAT-001_v2_rehomologation.csv
```

### Opción 2: Importar al Sistema
```bash
# Ejecutar el script de ejemplo
python ejemplo_importar_cuestionario.py
```

### Opción 3: Importar Programáticamente
```python
from app.parsers.questionnaire_csv_parser import QuestionnaireCSVParser
from app.core.database import SessionLocal

db = SessionLocal()
questionnaire_id = QuestionnaireCSVParser.import_from_csv(
    'data/questionnaires/DEMO-MAT-001_v2_rehomologation.csv',
    db
)
print(f"Cuestionario importado: #{questionnaire_id}")
```

## 📊 Estructura del CSV

### Secciones Incluidas

1. **Metadata**: Material, proveedor, versión, fecha
2. **Información de la Empresa**: Datos de contacto, registro legal
3. **Certificaciones**: ISO, orgánico, kosher, halal, fair trade, etc.
4. **Sostenibilidad**: Prácticas ambientales, scoring
5. **Alérgenos**: Declaraciones y control
6. **Parámetros de Calidad**: Pureza, humedad, análisis químicos
7. **Composición**: Componentes principales, impurezas
8. **Cadena de Suministro**: Origen, trazabilidad, shelf life
9. **Documentación**: TDS, SDS, CoA, etc.
10. **Explicación de Cambios** (solo rehomologación): Justificaciones y acciones correctivas
11. **Firmas**: Preparado por, revisado por, aprobado por

## 🔄 Workflow Automático

Cuando se importa un CSV al sistema:

1. **Parse** → Extrae metadata y respuestas del CSV
2. **Create** → Crea registro de Questionnaire en DB
3. **Validate** → Compara automáticamente contra Blue Line
4. **AI Analysis** → Calcula risk score y genera recomendaciones
5. **Incidents** → Crea incidentes para desviaciones críticas
6. **Review** → Usuario revisa y resuelve incidentes
7. **Approve** → Si todo OK, aprueba y actualiza Blue Line

## 🎬 Demo End-to-End

Para ver el workflow completo automatizado:

```bash
cd backend
python app/scripts/generate_e2e_demo.py
```

Este script:
- ✅ Crea material DEMO-MAT-001 con Blue Line
- ✅ Carga cuestionario v1 (aprobado)
- ✅ Carga cuestionario v2 (con desviaciones)
- ✅ Ejecuta validación automática
- ✅ Genera análisis de IA
- ✅ Crea incidentes críticos
- ✅ Demuestra resolución de incidentes
- ✅ Aprueba cuestionario final

## 📝 Formato del CSV

El CSV usa un formato estructurado por secciones:

```csv
SECCIÓN X: NOMBRE DE LA SECCIÓN
Campo,Valor,Cambio vs V1 (opcional)
field_name,field_value,explanation
...
```

**Ventajas**:
- ✅ Fácil de leer y editar en Excel
- ✅ Estructura clara por secciones
- ✅ Incluye explicaciones de cambios
- ✅ Formato estándar que proveedores pueden completar
- ✅ Parser automático extrae todo

## 💡 Personalización

Para crear nuevos cuestionarios:

1. Copia uno de los CSV de ejemplo
2. Modifica los valores según tu caso
3. Importa usando el parser
4. El sistema validará y analizará automáticamente

## 🔗 Links Útiles

- API Docs: http://localhost:8000/docs
- Questionnaires UI: http://localhost:5173/questionnaires
- Material Detail: http://localhost:5173/materials/9

