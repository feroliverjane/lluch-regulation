# Sistema de Gestión de Composites - Lluch Regulation

Sistema automatizado para la gestión de composites de materias primas con análisis cromatográficos, cálculo automático, workflow de aprobación e integraciones.

## Stack Tecnológico

- **Backend:** FastAPI + Python 3.11+
- **Frontend:** React + TypeScript + Vite
- **Base de datos:** PostgreSQL
- **Procesamiento:** Pandas
- **Tareas async:** Celery + Redis

## Estructura del Proyecto

```
lluch-regulation/
├── backend/          # API FastAPI
├── frontend/         # Aplicación React
├── data/            # Datos y uploads
└── docker-compose.yml
```

## Inicio Rápido

### Requisitos Previos

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+

### Instalación con Docker

```bash
# Clonar repositorio y navegar al directorio
cd lluch-regulation

# Levantar servicios
docker-compose up -d

# Aplicar migraciones
docker-compose exec backend alembic upgrade head

# Generar datos dummy
docker-compose exec backend python -m app.scripts.generate_dummy_data
```

La aplicación estará disponible en:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Instalación Local

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Aplicar migraciones
alembic upgrade head

# Generar datos dummy
python -m app.scripts.generate_dummy_data

# Ejecutar servidor
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Funcionalidades Principales

### 1. Gestión de Materiales
- CRUD completo de materiales (fragancias y aromas)
- Historial de versiones
- Documentación asociada
- Integración con SAP (estados Z1/Z2/Z001/Z002)

### 2. Análisis Cromatográficos
- Upload de archivos CSV
- Parser automático de componentes
- Validación de datos
- Visualización de resultados

### 3. Cálculo de Composites
- **Modo LAB:** Agregación de análisis cromatográficos
- **Modo CALCULATED:** Cálculo desde documentación técnica
- Promedio ponderado por lotes/cantidades
- Clasificación automática: componentes vs impurezas

### 4. Workflow de Aprobación
- Estados: DRAFT → PENDING_APPROVAL → APPROVED/REJECTED
- Estados Blue Line: APC, APR, REJ, CAN, EXP, INC, REA, RUN, VAL
- Asignación a técnicos
- Comparación de versiones
- Auditoría completa

### 5. Sistema de Versionado
- Historial completo de cambios
- Comparación visual entre versiones
- Detección de cambios significativos

### 6. Revisión Periódica
- Recálculo automático programado
- Notificaciones de desviaciones
- Dashboard de materiales a revisar

### 7. Línea Azul (Blue Line) - **NUEVO**
- **Automatización de homologación LLUCH 103721**
- 446 campos configurables con lógica personalizable
- Cálculo automático basado en aprobaciones y compras
- Sincronización bidireccional con SAP Composite
  - Z1 (validado) → envía a SAP
  - Z2 (provisional) ← importa de SAP
- Reglas de elegibilidad: APC/APR Regulatory + No REJ Technical + compras últimos 3 años
- Gestión de material tipo Z001 (provisional) y Z002 (homologado)
- Ver documentación completa en [BLUE_LINE_GUIDE.md](BLUE_LINE_GUIDE.md)

## API Endpoints

Ver documentación completa en `/docs` (Swagger UI) cuando el servidor esté corriendo.

Principales endpoints:
- `POST /api/materials` - Crear material
- `GET /api/materials` - Listar materiales
- `POST /api/chromatographic-analyses` - Subir análisis CSV
- `POST /api/composites/calculate` - Calcular composite
- `PUT /api/composites/{id}/approve` - Aprobar composite
- `GET /api/workflows` - Ver aprobaciones pendientes
- `POST /api/blue-line/calculate` - Calcular Línea Azul
- `POST /api/blue-line/{id}/sync-to-sap` - Sincronizar con SAP
- `GET /api/blue-line/field-logic` - Gestionar lógica de 446 campos

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Arquitectura de Integraciones

El sistema está preparado para integrarse con:
- **ChemSD:** Importar/exportar datos químicos
- **ERP:** Sincronización de materiales e inventario
- **CRM:** Notificaciones a clientes

Los adaptadores están en `backend/app/integrations/` listos para configuración cuando las APIs estén disponibles.

## Desarrollo

### Base de Datos

Las migraciones se gestionan con Alembic:

```bash
# Crear nueva migración
alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
alembic upgrade head

# Revertir migración
alembic downgrade -1
```

### Datos Dummy

Para regenerar datos de prueba:

```bash
python -m app.scripts.generate_dummy_data --clean
```

## Licencia

Propietario - Lluch Regulation © 2025






