# Guía de Inicio Rápido - Sistema de Gestión de Composites

Esta guía te ayudará a poner en marcha el sistema de gestión de composites de Lluch Regulation.

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.11+** - [Descargar Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Descargar Node.js](https://nodejs.org/)
- **PostgreSQL 15+** - [Descargar PostgreSQL](https://www.postgresql.org/download/)
- **Redis** (opcional, para Celery) - [Descargar Redis](https://redis.io/download)
- **Docker & Docker Compose** (recomendado) - [Descargar Docker](https://www.docker.com/products/docker-desktop)

## Opción 1: Inicio Rápido con Docker (Recomendado)

### 1. Configurar variables de entorno

Crea un archivo `.env` en el directorio `backend/`:

```bash
cd backend
cp .env.example .env
```

Edita `.env` si necesitas cambiar alguna configuración (los valores por defecto funcionarán con Docker).

### 2. Levantar los servicios

Desde el directorio raíz del proyecto:

```bash
docker-compose up -d
```

Esto iniciará:
- PostgreSQL (puerto 5432)
- Redis (puerto 6379)
- Backend API (puerto 8000)
- Frontend (puerto 5173)
- Celery Worker
- Celery Beat

### 3. Aplicar migraciones de base de datos

```bash
docker-compose exec backend alembic upgrade head
```

### 4. Generar datos de prueba

```bash
docker-compose exec backend python -m app.scripts.generate_dummy_data
```

### 5. Acceder a la aplicación

- **Frontend:** http://localhost:5173
- **API Backend:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc

### 6. Credenciales de prueba

- **Admin:** `admin` / `admin123`
- **Técnico:** `tech_maria` / `tech123`
- **Viewer:** `viewer` / `viewer123`

## Opción 2: Instalación Local (Sin Docker)

### 1. Configurar PostgreSQL

Crea una base de datos:

```sql
CREATE DATABASE lluch_regulation;
CREATE USER lluch_user WITH PASSWORD 'lluch_pass';
GRANT ALL PRIVILEGES ON DATABASE lluch_regulation TO lluch_user;
```

### 2. Configurar Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En macOS/Linux:
source venv/bin/activate
# En Windows:
# venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
# Crea el archivo .env manualmente con el siguiente contenido:
```

Contenido del archivo `backend/.env`:

```env
DATABASE_URL=postgresql://lluch_user:lluch_pass@localhost:5432/lluch_regulation
API_V1_PREFIX=/api
PROJECT_NAME=Lluch Regulation - Composite Management
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
MAX_UPLOAD_SIZE=10485760
UPLOAD_DIR=../data/uploads
COMPOSITE_THRESHOLD_PERCENT=5.0
REVIEW_PERIOD_DAYS=90
```

Continuar con backend:

```bash
# Aplicar migraciones
alembic upgrade head

# Generar datos de prueba
python -m app.scripts.generate_dummy_data

# Ejecutar servidor
uvicorn app.main:app --reload
```

El backend estará disponible en http://localhost:8000

### 3. Configurar Frontend

En una nueva terminal:

```bash
cd frontend

# Instalar dependencias
npm install

# Ejecutar servidor de desarrollo
npm run dev
```

El frontend estará disponible en http://localhost:5173

### 4. Configurar Celery (Opcional)

Para tareas asíncronas y programadas:

```bash
cd backend

# Terminal 1: Celery Worker
celery -A app.core.celery_app worker --loglevel=info

# Terminal 2: Celery Beat (tareas programadas)
celery -A app.core.celery_app beat --loglevel=info
```

## Estructura del Proyecto

```
lluch-regulation/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── api/            # Endpoints REST
│   │   ├── core/           # Configuración y DB
│   │   ├── models/         # Modelos SQLAlchemy
│   │   ├── schemas/        # Schemas Pydantic
│   │   ├── services/       # Lógica de negocio
│   │   ├── parsers/        # Parser CSV
│   │   ├── integrations/   # Adaptadores externos
│   │   ├── tasks/          # Tareas Celery
│   │   └── scripts/        # Scripts útiles
│   ├── alembic/            # Migraciones DB
│   └── tests/              # Tests
├── frontend/               # Aplicación React
│   └── src/
│       ├── components/     # Componentes reutilizables
│       ├── pages/          # Páginas
│       ├── services/       # Cliente API
│       └── types/          # Tipos TypeScript
├── data/
│   ├── uploads/            # Archivos CSV subidos
│   └── dummy/              # Datos de prueba
└── docker-compose.yml      # Configuración Docker
```

## Funcionalidades Principales

### 1. Gestión de Materiales

- Crear, editar y listar materiales (fragancias y aromas)
- Almacenar información: código de referencia, nombre, proveedor, CAS, tipo
- Historial completo de composites y análisis por material

### 2. Análisis Cromatográficos

- Subir archivos CSV con análisis de laboratorio
- Parser automático que identifica componentes, CAS numbers y porcentajes
- Validación de datos (suma 100%, rangos válidos)
- Agregación de múltiples análisis

### 3. Cálculo de Composites

**Modo LAB (prioritario):**
- Calcula composite a partir de análisis cromatográficos
- Promedio ponderado por lote/cantidad
- Clasificación automática: componente vs impureza
- Nivel de confianza basado en consistencia

**Modo CALCULATED:**
- Entrada manual de componentes
- Para cuando no hay análisis de laboratorio

### 4. Workflow de Aprobación

- Estados: DRAFT → PENDING_APPROVAL → APPROVED/REJECTED
- Asignación a técnicos
- Comentarios y razones de rechazo
- Auditoría completa

### 5. Versionado y Comparación

- Múltiples versiones de composites por material
- Comparación visual entre versiones
- Detección automática de cambios significativos

### 6. Revisión Periódica

- Tarea programada para recalcular composites antiguos
- Notificación si hay cambios significativos
- Configurable por umbral de cambio

## Uso del Sistema

### Flujo Típico de Trabajo

1. **Crear Material**
   - Ve a "Materiales" → "Nuevo Material"
   - Completa la información básica
   - Guarda el material

2. **Subir Análisis Cromatográficos**
   - Abre el detalle del material
   - Sube archivos CSV con análisis de laboratorio
   - El sistema los procesa automáticamente

3. **Calcular Composite**
   - Desde el material, haz clic en "Calcular Composite"
   - Selecciona los análisis a incluir (o usa todos)
   - El sistema calcula el promedio ponderado

4. **Revisar y Aprobar**
   - El composite se crea en estado DRAFT
   - Envía para aprobación
   - Un técnico revisa y aprueba/rechaza

5. **Consultar Historial**
   - Visualiza todas las versiones de composites
   - Compara versiones para ver cambios
   - Descarga reportes

### Formato de CSV para Análisis Cromatográficos

El parser acepta archivos CSV con las siguientes columnas (nombres flexibles):

**Requerido:**
- Componente: `component`, `compound`, `name`, `component_name`
- Porcentaje: `percentage`, `%`, `percent`, `concentration`, `area%`

**Opcional:**
- CAS Number: `cas`, `cas_number`, `cas number`, `cas_no`

**Ejemplo:**

```csv
CAS Number,Component,Percentage
5989-27-5,Limonene,35.5
78-70-6,Linalool,15.2
5392-40-5,Citral,5.8
106-24-1,Geraniol,12.3
```

## Integraciones Futuras

El sistema está preparado para integrarse con:

- **ChemSD:** Importar/exportar datos químicos
- **ERP:** Sincronizar materiales e inventario
- **CRM:** Notificar a clientes sobre cambios

Los adaptadores están en `backend/app/integrations/` listos para configurar cuando tengas acceso a las APIs.

## Solución de Problemas

### Error de conexión a la base de datos

Verifica que PostgreSQL esté corriendo:

```bash
# macOS
brew services start postgresql

# Linux
sudo service postgresql start

# Windows
net start postgresql-x64-15
```

### Error al instalar dependencias de Python

Asegúrate de tener Python 3.11+:

```bash
python --version
```

Si usas macOS y tienes problemas con psycopg2, instala:

```bash
brew install postgresql
```

### El frontend no carga datos

Verifica que el backend esté corriendo en http://localhost:8000:

```bash
curl http://localhost:8000/health
```

Debería responder: `{"status":"healthy"}`

### Celery no ejecuta tareas

Verifica que Redis esté corriendo:

```bash
redis-cli ping
```

Debería responder: `PONG`

## Comandos Útiles

### Backend

```bash
# Crear nueva migración
alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
alembic upgrade head

# Revertir migración
alembic downgrade -1

# Regenerar datos dummy
python -m app.scripts.generate_dummy_data --clean

# Ejecutar tests
pytest
```

### Frontend

```bash
# Instalar dependencias
npm install

# Modo desarrollo
npm run dev

# Build para producción
npm run build

# Preview del build
npm run preview

# Tests
npm test
```

### Docker

```bash
# Levantar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f backend

# Reiniciar servicio
docker-compose restart backend

# Detener servicios
docker-compose down

# Limpiar todo (¡cuidado!)
docker-compose down -v
```

## Próximos Pasos

1. Explora la API en http://localhost:8000/docs
2. Prueba crear materiales y subir análisis CSV
3. Calcula algunos composites
4. Experimenta con el workflow de aprobación
5. Revisa el código para personalizar según tus necesidades

## Soporte

Para preguntas o problemas:
- Revisa la documentación en `/docs`
- Consulta los logs: `docker-compose logs -f`
- Revisa el código fuente en GitHub

¡Bienvenido al Sistema de Gestión de Composites de Lluch Regulation!






