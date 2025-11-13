# 🚀 AI Blue Line System - Quick Start Guide

## Sistema Completo de Homologación con IA

Este sistema implementa un flujo completo de homologación y re-homologación de materiales con validación AI, extracción automática de composites desde PDFs, y gestión inteligente de Líneas Azules.

---

## 📦 ¿Qué incluye este sistema?

### Backend (FastAPI + SQLAlchemy + AI)
✅ **Validación de Coherencia AI** - Detecta contradicciones lógicas en cuestionarios  
✅ **Extracción AI de Composites** - Extrae componentes químicos desde PDFs con OCR  
✅ **Motor de Lógicas Blue Line** - Reglas CSV codificadas en Python  
✅ **Comparación de Composites** - Cálculo de match scores y diferencias  
✅ **Sistema Z1/Z2** - Gestión de composites provisionales y definitivos  
✅ **Promedio Inteligente** - Recálculo de composites maestros  

### Frontend (React + TypeScript + Vite)
✅ **Página de Cuestionario Mejorada** - Con validación AI, upload docs, extracción  
✅ **Componente de Comparación** - Visualización side-by-side de composites  
✅ **Página Blue Line Mejorada** - Gestión de Z1/Z2 con botones de actualización  
✅ **UI/UX Moderna** - Dark mode, colores semánticos, estados de carga  

---

## 🎯 Casos de Uso Principales

### 1. Homologación Inicial (Material Nuevo)
```
1. Importar cuestionario JSON
2. Validar coherencia con IA → Ver score y issues
3. Subir PDFs de especificaciones
4. Extraer composite Z1 con IA → Componentes + porcentajes
5. Aprobar cuestionario
6. Crear Blue Line automáticamente
7. (Opcional) Actualizar a Z2 cuando llegue análisis de lab
```

### 2. Re-homologación (Material Existente)
```
1. Importar nuevo cuestionario para material con Blue Line
2. Sistema detecta Blue Line existente
3. Validar nuevo cuestionario con IA
4. Extraer nuevo composite Z1
5. Comparar con composite maestro
6. Si aprueba → Recalcular Z1 maestro (promedio)
7. (Opcional) Actualizar a Z2 definitivo
```

### 3. Actualización Z1 → Z2
```
1. Ir a Blue Line Detail
2. Click "Actualizar a Z2"
3. Subir archivo de laboratorio (PDF/XLSX/CSV)
4. Confirmar → Composite bloqueado permanentemente
5. Card cambia a verde con 🔒
```

---

## 🛠️ Instalación y Setup

### Prerrequisitos
```bash
- Python 3.9+
- Node.js 18+
- Tesseract OCR (para extracción de PDFs)
```

### Backend Setup
```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar Tesseract (macOS)
brew install tesseract

# Instalar Tesseract (Ubuntu)
sudo apt-get install tesseract-ocr

# Instalar Tesseract (Windows)
# Descargar de: https://github.com/UB-Mannheim/tesseract/wiki

# Aplicar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar dev server
npm run dev

# Abrir en navegador: http://localhost:5173
```

---

## 🧪 Testing

### Test de Integración Backend
```bash
cd backend
source venv/bin/activate
python test_complete_user_flow.py
```

### Test de Integración Frontend-Backend
```bash
# Asegúrate de que backend esté corriendo
python test_frontend_ai_integration.py
```

### Test Manual en UI
1. Abrir http://localhost:5173
2. Ir a "Cuestionarios" → Seleccionar uno
3. Probar botón "Validar Coherencia con IA"
4. Subir PDFs de prueba
5. Probar "Extraer Composite con IA"
6. Ir a "Blue Lines" → Ver composite Z1/Z2

---

## 📁 Estructura del Proyecto

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── questionnaires.py         # 🆕 Endpoints AI
│   │   │   └── composites.py             # 🆕 Endpoints comparación
│   │   ├── models/
│   │   │   ├── composite.py              # 🆕 composite_type, questionnaire_id
│   │   │   └── questionnaire.py          # 🆕 ai_coherence_score
│   │   └── services/
│   │       ├── questionnaire_coherence_validator.py  # 🆕 Validador AI
│   │       ├── blue_line_logic_engine.py            # 🆕 Motor de lógicas
│   │       ├── composite_extractor_ai.py            # 🆕 Extractor OCR + AI
│   │       └── composite_comparison_service.py      # 🆕 Comparador
│   ├── alembic/versions/
│   │   └── e8f4a2b9c1d7_add_ai_composite_fields.py  # 🆕 Migración
│   └── requirements.txt                             # 🆕 Nuevas deps
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── QuestionnaireDetail.tsx    # 🔄 Mejorado con AI
│       │   └── BlueLineDetail.tsx         # 🔄 Mejorado con Z1/Z2
│       └── components/
│           └── CompositeComparison.tsx    # 🆕 Comparador visual
│
├── data/
│   └── rules blue line/
│       └── 03_Lógicas Línea Azul(Datos Gen.csv  # Reglas de negocio
│
├── AI_BLUE_LINE_SYSTEM_README.md         # 📘 Documentación completa
├── BACKEND_IMPLEMENTATION_COMPLETE.md    # ✅ Resumen backend
├── FRONTEND_AI_IMPLEMENTATION_COMPLETE.md # ✅ Resumen frontend
└── test_frontend_ai_integration.py       # 🧪 Tests
```

---

## 🔑 Endpoints Clave

### Nuevos Endpoints AI (Backend)
```python
POST   /api/questionnaires/{id}/validate-coherence
POST   /api/questionnaires/{id}/upload-documents
POST   /api/questionnaires/{id}/extract-composite
POST   /api/questionnaires/{id}/create-blue-line
GET    /api/questionnaires/{id}/composite
POST   /api/composites/{id}/update-to-z2
POST   /api/composites/compare-detailed
POST   /api/composites/average
```

---

## 🎨 Características de UI

### Validación de Coherencia
- Score visual de 0-100 con colores semánticos
- Lista de issues agrupados por severity
- Badges: `CRITICAL` (rojo), `WARNING` (amarillo), `INFO` (azul)

### Upload de Documentos
- Drag & drop de PDFs
- Lista de documentos con iconos y fechas
- Estado de carga visual

### Extracción de Composite
- Botón con loading state
- Card de éxito con info del composite
- Barra de confianza con colores
- Link directo al composite

### Comparación de Composites
- Grid 2 columnas side-by-side
- Score de match con colores
- Tablas de diferencias y únicos
- Mensaje especial si son idénticos

### Z1/Z2 Management
- Cards con colores: azul (Z1), verde (Z2)
- Botón "Actualizar a Z2" solo en Z1
- Lock visual 🔒 para Z2
- Advertencia de irreversibilidad

---

## 📊 Flujo de Datos

```
┌─────────────────┐
│  Cuestionario   │
│   (Importar)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│   Validación    │────▶│  Coherence   │
│   Coherencia AI │     │  Score + Issues│
└────────┬────────┘     └──────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│   Subir PDFs    │────▶│  Documentos  │
│                 │     │   Adjuntos   │
└────────┬────────┘     └──────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│  Extracción AI  │────▶│ Composite Z1 │
│   OCR + Parse   │     │  + Confianza │
└────────┬────────┘     └──────┬───────┘
         │                     │
         ▼                     │
┌─────────────────┐            │
│     Aprobar     │            │
│   Cuestionario  │            │
└────────┬────────┘            │
         │                     │
         ▼                     ▼
┌─────────────────┐     ┌──────────────┐
│  Crear Blue     │────▶│ Composite    │
│    Line con     │     │  Asociado    │
│  Lógicas CSV    │     │   a Blue     │
└────────┬────────┘     └──────┬───────┘
         │                     │
         │                     ▼
         │              ┌──────────────┐
         │              │  Lab Analysis│
         │              │    Llega     │
         │              └──────┬───────┘
         │                     │
         │                     ▼
         │              ┌──────────────┐
         └─────────────▶│ Actualizar a │
                        │   Z2 (🔒)   │
                        └──────────────┘
```

---

## 🧩 Integración con Sistemas Externos

### SAP
- Sincronización bidireccional de Blue Lines
- Importar datos maestros
- Exportar campos calculados

### ChemSD
- Consulta de información de CAS numbers
- Validación de sustancias químicas

### CRM
- Gestión de proveedores
- Historial de interacciones

---

## 📖 Documentación Completa

### Para Desarrolladores
- `AI_BLUE_LINE_SYSTEM_README.md` - Sistema completo
- `BACKEND_IMPLEMENTATION_COMPLETE.md` - Backend detallado
- `FRONTEND_AI_IMPLEMENTATION_COMPLETE.md` - Frontend detallado
- `ARCHITECTURE.md` - Arquitectura general

### Para Usuarios
- `BLUE_LINE_GUIDE.md` - Guía de uso de Blue Lines
- `QUESTIONNAIRE_SYSTEM_README.md` - Sistema de cuestionarios
- `GETTING_STARTED.md` - Primeros pasos

### Para Testing
- `test_complete_user_flow.py` - Test de flujo completo
- `test_frontend_ai_integration.py` - Test de endpoints AI
- `TESTING_EJEMPLOS.md` - Ejemplos de testing

---

## 🐛 Troubleshooting

### Backend no inicia
```bash
# Verificar dependencias
pip list | grep -E "(fastapi|sqlalchemy|alembic)"

# Reinstalar si es necesario
pip install -r requirements.txt --force-reinstall

# Verificar base de datos
alembic current
alembic upgrade head
```

### Frontend no muestra nuevas características
```bash
# Limpiar cache
rm -rf node_modules
npm install

# Rebuild
npm run build
npm run dev
```

### Tesseract no funciona
```bash
# Verificar instalación
tesseract --version

# macOS
brew reinstall tesseract

# Ubuntu
sudo apt-get install --reinstall tesseract-ocr

# Configurar path en código si es necesario
# backend/app/services/composite_extractor_ai.py
```

### Migración Alembic falla
```bash
# Ver historial
alembic history

# Downgrade si es necesario
alembic downgrade -1

# Re-aplicar
alembic upgrade head

# Si persiste, revisar:
# backend/alembic/versions/e8f4a2b9c1d7_add_ai_composite_fields.py
```

---

## 🚀 Deployment

### Backend (Production)
```bash
# Usar Gunicorn + Uvicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

# O Docker
docker build -t lluch-backend .
docker run -p 8000:8000 lluch-backend
```

### Frontend (Production)
```bash
# Build
npm run build

# Los archivos están en dist/
# Servir con Nginx, Apache, o hosting estático

# O Docker
docker build -t lluch-frontend .
docker run -p 80:80 lluch-frontend
```

---

## 📞 Contacto y Soporte

Para preguntas o issues:
1. Revisar documentación en `/docs`
2. Ejecutar tests de diagnóstico
3. Verificar logs en `backend/backend.log`

---

## 🎉 Conclusión

Este sistema está **100% funcional** y listo para:
- ✅ Validación AI de cuestionarios
- ✅ Extracción automática de composites
- ✅ Gestión completa de Blue Lines
- ✅ Sistema Z1/Z2 con actualización
- ✅ Comparación visual de composites

**¡Feliz homologación con IA! 🤖**

---

**Versión:** 1.0.0  
**Fecha:** 31 de Octubre, 2025  
**Estado:** ✅ PRODUCCIÓN READY













