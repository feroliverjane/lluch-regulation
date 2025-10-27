# Arquitectura del Sistema - Lluch Regulation

## Visión General

El Sistema de Gestión de Composites de Lluch Regulation es una aplicación web moderna diseñada para automatizar la creación, gestión y aprobación de composites de materias primas para fragancias y aromas.

## Stack Tecnológico

### Backend
- **Framework:** FastAPI 0.104+ (Python 3.11+)
- **ORM:** SQLAlchemy 2.0
- **Validación:** Pydantic 2.5
- **Migraciones:** Alembic
- **Base de datos:** PostgreSQL 15+
- **Tareas asíncronas:** Celery + Redis
- **Procesamiento de datos:** Pandas

### Frontend
- **Framework:** React 18
- **Lenguaje:** TypeScript
- **Build tool:** Vite
- **Routing:** React Router v6
- **State management:** React Query (TanStack Query) + Zustand
- **Gráficas:** Recharts
- **Iconos:** Lucide React

### DevOps
- **Containerización:** Docker + Docker Compose
- **Servidor web:** Uvicorn (ASGI)
- **Proxy reverso:** Nginx (producción)

## Arquitectura de Capas

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND (React)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │   Pages      │  │  Components  │  │  Services │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
                         │
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────┐
│                 API LAYER (FastAPI)                  │
│  ┌──────────────────────────────────────────────┐  │
│  │         REST Endpoints (/api/*)              │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│               BUSINESS LOGIC LAYER                   │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │   Services   │  │   Parsers    │  │ Validators│ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                   DATA LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ SQLAlchemy   │  │  PostgreSQL  │  │   Redis   │ │
│  │   Models     │  │   Database   │  │   Cache   │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              INTEGRATION LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │   ChemSD     │  │     ERP      │  │    CRM    │ │
│  │   Adapter    │  │   Adapter    │  │  Adapter  │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
```

## Modelo de Datos

### Entidades Principales

#### Material
Representa una materia prima (aceite esencial, fragancia, etc.)
- Código de referencia único
- Nombre y descripción
- Proveedor
- CAS number
- Tipo (NATURAL, SYNTHETIC)

#### ChromatographicAnalysis
Análisis cromatográfico de laboratorio
- Archivo CSV procesado
- Lote, proveedor, fecha
- Datos parseados (componentes + porcentajes)
- Estado de procesamiento

#### Composite
Tabla de composición de un material
- Versión (incremental por material)
- Origen (LAB, CALCULATED, MANUAL)
- Estado (DRAFT, PENDING_APPROVAL, APPROVED, REJECTED)
- Metadatos (lotes, análisis usados)

#### CompositeComponent
Componente individual dentro de un composite
- CAS number
- Nombre del componente
- Porcentaje
- Tipo (COMPONENT, IMPURITY)
- Nivel de confianza

#### ApprovalWorkflow
Flujo de aprobación de composites
- Asignación a técnicos
- Comentarios y razones de rechazo
- Historial de estados

### Relaciones

```
Material (1) ──────── (N) ChromatographicAnalysis
   │
   │
   └────────────────── (N) Composite
                          │
                          └────── (N) CompositeComponent
                          │
                          └────── (1) ApprovalWorkflow
```

## Flujos de Datos

### 1. Upload y Procesamiento de Análisis CSV

```
User Upload CSV
       │
       ▼
ChromatographicAnalysisController.upload()
       │
       ▼
ChromatographicCSVParser.parse_file()
       │
       ├─ Identificar columnas (CAS, Component, %)
       ├─ Extraer componentes
       ├─ Validar suma 100%
       └─ Clasificar (COMPONENT vs IMPURITY)
       │
       ▼
Guardar ChromatographicAnalysis
       │
       ├─ parsed_data (JSON)
       ├─ is_processed = 1 (success)
       └─ metadata
```

### 2. Cálculo de Composite (Modo LAB)

```
User Request Calculate Composite
       │
       ▼
CompositeCalculator.calculate_from_lab_analyses()
       │
       ├─ Obtener análisis del material
       ├─ Filtrar por analysis_ids (si se especifican)
       │
       ▼
Agregación de componentes
       │
       ├─ Agrupar por CAS/nombre
       ├─ Calcular promedio ponderado por weight
       ├─ Calcular nivel de confianza (consistencia)
       └─ Normalizar a 100%
       │
       ▼
Crear Composite
       │
       ├─ Version = max(version) + 1
       ├─ Status = DRAFT
       ├─ Components[]
       └─ Metadata (análisis usados, lotes, etc.)
```

### 3. Workflow de Aprobación

```
User Submit for Approval
       │
       ▼
Composite.status = PENDING_APPROVAL
       │
       ▼
Crear/Actualizar ApprovalWorkflow
       │
       ├─ Asignar a técnico
       ├─ Status = PENDING
       └─ Notificar (email/Slack)
       │
       ▼
Técnico Revisa
       │
       ├─ Ver componentes
       ├─ Comparar con versión anterior
       └─ Decidir
       │
       ├─────────────┬─────────────┐
       │             │             │
       ▼             ▼             ▼
   APPROVE       REJECT       CANCEL
       │             │             │
       ▼             ▼             ▼
  Status=APPROVED  Status=REJECTED  Status=CANCELLED
  approved_at=NOW  rejection_reason  workflow.status
       │             │
       ▼             └─ Notificar
Workflow=APPROVED
Notificar a sistemas
  ├─ ChemSD
  ├─ ERP
  └─ CRM
```

### 4. Revisión Periódica (Celery Task)

```
Celery Beat Schedule (cada N días)
       │
       ▼
review_composites() task
       │
       ├─ Filtrar composites > REVIEW_PERIOD_DAYS
       │
       ▼
Para cada material:
       │
       ├─ Obtener último composite aprobado
       ├─ Recalcular con análisis actuales
       │
       ▼
Comparar nuevo vs actual
       │
       ├─ Total change > THRESHOLD?
       │
       ├──YES──▶ Guardar nuevo composite
       │         └─ Notificar técnico
       │
       └──NO───▶ Descartar
```

## Servicios Principales

### CompositeCalculator
Responsable del cálculo de composites
- `calculate_from_lab_analyses()`: Modo LAB
- `calculate_from_documents()`: Modo CALCULATED
- Agregación con promedio ponderado
- Normalización a 100%

### CompositeComparator
Comparación entre versiones de composites
- `compare_composites()`: Genera diff detallado
- Identifica componentes añadidos/eliminados/modificados
- Calcula score de cambio total
- Determina si los cambios son significativos

### ChromatographicCSVParser
Parser flexible de archivos CSV
- Detección automática de columnas
- Soporte para múltiples formatos
- Validación de datos
- Clasificación de componentes

## Integraciones Externas

### Arquitectura de Adaptadores

Cada integración externa tiene un adaptador dedicado que:
1. Abstrae la comunicación con la API externa
2. Maneja autenticación y errores
3. Transforma datos al formato interno
4. Permite mock para desarrollo sin APIs

```python
class ChemSDAdapter:
    def export_composite(composite_id, data) -> bool
    def import_component_data(cas_number) -> dict
    def sync_material(material_id, data) -> bool

class ERPAdapter:
    def sync_material(material_id, data) -> bool
    def update_inventory(material_id, version) -> bool
    def get_purchase_history(reference_code) -> list

class CRMAdapter:
    def notify_composite_approval(material, version) -> bool
    def get_material_customers(reference_code) -> list
```

### Configuración

Las integraciones se activan mediante variables de entorno:
- Si `API_URL` y `API_KEY` están configurados → enabled = True
- Si no → enabled = False (modo mock/logging)

## Seguridad

### Autenticación (Futuro)
- JWT tokens
- Roles: ADMIN, TECHNICIAN, VIEWER
- Permisos granulares por endpoint

### Validación de Datos
- Pydantic schemas en todos los endpoints
- Validación de tipos, rangos y formatos
- Sanitización de inputs

### Protección de Archivos
- Validación de tipo de archivo (solo CSV)
- Límite de tamaño (configurable)
- Escaneo de contenido

## Escalabilidad

### Horizontal Scaling
- FastAPI es stateless → múltiples instancias
- Load balancer (Nginx/HAProxy)
- Redis para sesiones compartidas

### Database Optimization
- Índices en columnas frecuentemente consultadas
- Paginación en listados
- Eager loading de relaciones
- Connection pooling

### Caching
- Redis para datos frecuentemente accedidos
- Cache invalidation en actualizaciones

### Async Processing
- Celery para tareas pesadas
- File uploads no bloquean requests
- Cálculos complejos en background

## Monitoring y Logging

### Logs
- Structured logging (JSON)
- Niveles: DEBUG, INFO, WARNING, ERROR
- Rotación de archivos
- Agregación con ELK/Splunk

### Métricas
- Response times
- Error rates
- Database query performance
- Celery task execution

### Health Checks
- `/health` endpoint
- Database connectivity
- Redis connectivity
- Disk space

## Testing

### Backend
- **Unit tests:** Pytest para servicios y parsers
- **Integration tests:** Tests de endpoints completos
- **Coverage:** Objetivo 80%+

### Frontend
- **Unit tests:** Vitest para componentes
- **Integration tests:** React Testing Library
- **E2E tests:** Playwright (futuro)

## Deployment

### Desarrollo
```bash
docker-compose up
```

### Producción
- Docker containers
- Nginx reverse proxy
- SSL/TLS certificates
- Environment-specific configs
- Database backups automáticos
- Log aggregation
- Monitoring (Prometheus + Grafana)

## Roadmap Futuro

1. **Autenticación completa**
   - OAuth2/OIDC
   - SSO con Azure AD

2. **IA/ML Features**
   - Predicción de impurezas
   - Detección de anomalías en análisis
   - Recomendación de composites similares

3. **Documentos PDF**
   - Parser de fichas técnicas
   - Extracción de datos con OCR/NLP
   - Generación de reportes PDF

4. **Notificaciones avanzadas**
   - Email templates
   - Slack/Teams integration
   - SMS para alertas críticas

5. **Auditoría completa**
   - Historial de cambios detallado
   - Compliance tracking
   - Export para reguladores

6. **Mobile app**
   - React Native
   - Aprobaciones desde móvil
   - Notificaciones push






