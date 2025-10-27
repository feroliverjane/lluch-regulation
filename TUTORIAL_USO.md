# Tutorial de Uso - Sistema de Gestión de Composites

## 🎯 Tutorial Completo: De CSV a Composite Aprobado

### Paso 1: Acceder al Sistema
1. Abre tu navegador
2. Ve a: **http://localhost:5173**
3. Verás el Dashboard con estadísticas

### Paso 2: Seleccionar un Material
1. Haz clic en **"Materiales"** en el menú lateral
2. Haz clic en **"ORN-002: Orange Oil Brazil"**
3. Verás la página de detalle del material

### Paso 3: Subir Análisis CSV
1. En la sección "Análisis Cromatográficos", haz clic en **"Subir CSV"** (botón azul)
2. Se abrirá un modal con un formulario
3. Completa el formulario:
   - **Archivo CSV**: Haz clic y navega a:
     ```
     /Users/alonahubarenko/Documents/Marc/Mafer AI/Lluch Regulation/data/uploads/orange_oil_batch_B2024.csv
     ```
   - **Número de Lote**: `B2024-001`
   - **Proveedor**: `Brasil Citrus Ltd`
   - **Peso/Cantidad**: `1.0` (dejar por defecto)
4. Haz clic en **"Subir y Procesar"**
5. Espera el mensaje: "✅ Análisis subido y procesado exitosamente!"

### Paso 4: Verificar el Análisis Procesado
1. El modal se cerrará automáticamente
2. En la sección "Análisis Cromatográficos" verás:
   - **Nombre del archivo**: orange_oil_batch_B2024.csv
   - **Estado**: Badge verde "Procesado"
   - **Lote**: B2024-001
3. Aparecerá un nuevo botón verde: **"Calcular Composite"**

### Paso 5: Calcular el Composite
1. Haz clic en **"Calcular Composite"**
2. Aparecerá un mensaje de confirmación:
   ```
   ¿Calcular nuevo composite usando 1 análisis disponibles?
   ```
3. Haz clic en **"Aceptar"**
4. Espera unos segundos
5. Verás el mensaje: "✅ Composite calculado! Versión X con 8 componentes"

### Paso 6: Ver el Composite Creado
1. En la sección "Composites", verás el nuevo composite
2. Haz clic en él para ver la página de detalle
3. Verás:
   - **Información del composite**:
     - Versión
     - Origen (LAB)
     - Estado (DRAFT)
     - Número de componentes
   - **Gráfica de barras** con la distribución
   - **Tabla detallada** con todos los componentes:
     - Nombre del componente
     - CAS Number
     - Porcentaje
     - Tipo (Componente/Impureza)
     - Nivel de confianza

### Paso 7: Aprobar el Composite (Opcional)
1. Si el composite está en estado PENDING_APPROVAL
2. Haz clic en el botón **"Aprobar"** (verde)
3. El estado cambiará a APPROVED
4. El composite quedará guardado permanentemente

---

## 🎨 Prueba con Diferentes Materiales

### Material 3: Lavender Oil (Lavanda)
1. Ve a: http://localhost:5173/materials/3
2. Sube: `lavender_oil_provence_2024.csv`
3. Este CSV tiene **12 componentes** (más complejo)
4. Calcula el composite y verás una composición más rica

### Material 4: Peppermint Oil (Menta)
1. Ve a: http://localhost:5173/materials/4
2. Sube: `peppermint_oil_usa_2024.csv`
3. Incluye Menthol (42.5%) como componente principal
4. Perfecto para ver cómo se identifican componentes principales

### Material 5: Eucalyptus Oil
1. Ve a: http://localhost:5173/materials/5
2. Sube: `eucalyptus_oil_australia_2024.csv`
3. Dominado por Eucalyptol (78.5%)
4. Ejemplo de material con un componente muy predominante

---

## 📊 Subir Múltiples Análisis (Promedio Ponderado)

Para ver el poder del sistema con agregación:

1. **Ve al Material 1** (Lemon Oil)
2. **Sube el mismo CSV 3 veces** con diferentes lotes:
   - Primera vez: Lote `A2023-001`, Peso `1.0`
   - Segunda vez: Lote `A2023-002`, Peso `1.5`
   - Tercera vez: Lote `A2023-003`, Peso `0.8`
3. **Calcula el composite**
4. El sistema calculará un **promedio ponderado** de los 3 análisis
5. Verás niveles de confianza más altos cuando hay múltiples análisis

---

## 🔍 Comparar Versiones de Composites

Si un material tiene múltiples versiones de composites:

1. Ve a la página del material
2. En la sección "Composites", verás todas las versiones
3. Haz clic en una versión
4. Usa la API para comparar:
   ```
   http://localhost:8000/api/composites/1/compare/2
   ```
5. Verás:
   - Componentes añadidos
   - Componentes eliminados
   - Componentes modificados
   - Score de cambio total

---

## 🔧 Explorar la API Interactiva

1. Abre: **http://localhost:8000/docs**
2. Verás la documentación Swagger completa
3. Puedes probar TODOS los endpoints directamente:
   - Haz clic en cualquier endpoint
   - Haz clic en "Try it out"
   - Completa los parámetros
   - Haz clic en "Execute"
   - Verás la respuesta completa

### Endpoints útiles para probar:

- **GET /api/materials** - Ver todos los materiales
- **GET /api/composites/material/{id}** - Ver composites de un material
- **GET /api/chromatographic-analyses/material/{id}** - Ver análisis
- **POST /api/composites/calculate** - Calcular composite (JSON)

---

## 💡 Casos de Uso Avanzados

### 1. Crear Material Nuevo
1. Usa la API o código:
   ```bash
   curl -X POST http://localhost:8000/api/materials \
     -H "Content-Type: application/json" \
     -d '{
       "reference_code": "TEST-001",
       "name": "Mi Material de Prueba",
       "supplier": "Mi Proveedor",
       "material_type": "NATURAL"
     }'
   ```

### 2. Workflow Completo de Aprobación
1. Sube análisis → Estado: Procesado
2. Calcula composite → Estado: DRAFT
3. Envía para aprobación → Estado: PENDING_APPROVAL
4. Técnico revisa y aprueba → Estado: APPROVED
5. El composite queda registrado permanentemente

### 3. Revisar Periódicamente
- El sistema tiene tareas Celery programadas
- Cada X días recalcula composites antiguos
- Compara con la versión actual
- Notifica si hay cambios significativos

---

## 🎓 Conceptos Clave del Sistema

### Parser CSV Inteligente
- Detecta automáticamente columnas (CAS, Componente, %)
- Funciona con múltiples formatos
- Valida que la suma sea ≈100%
- Normaliza automáticamente si es necesario

### Cálculo de Composites
- **Modo LAB**: Usa análisis cromatográficos
- **Promedio Ponderado**: Considera peso/cantidad de cada análisis
- **Nivel de Confianza**: Basado en consistencia entre análisis
- **Clasificación Automática**: Componente vs Impureza (<1%)

### Versionado
- Cada recálculo crea una nueva versión
- Se mantiene historial completo
- Se puede comparar entre versiones
- Detección de cambios significativos

---

## 📁 Archivos CSV Disponibles

Todos están en:
```
/Users/alonahubarenko/Documents/Marc/Mafer AI/Lluch Regulation/data/uploads/
```

| Archivo | Material | Componentes | Características |
|---------|----------|-------------|-----------------|
| `lemon_oil_batch_A2023.csv` | Lemon Oil | 8 | Limonene dominante (68.5%) |
| `orange_oil_batch_B2024.csv` | Orange Oil | 8 | d-Limonene muy alto (92.3%) |
| `lavender_oil_provence_2024.csv` | Lavender | 12 | Composición compleja |
| `peppermint_oil_usa_2024.csv` | Peppermint | 12 | Menthol principal (42.5%) |
| `eucalyptus_oil_australia_2024.csv` | Eucalyptus | 9 | Eucalyptol dominante (78.5%) |

---

## 🚀 ¡Empieza Ahora!

1. **Abre**: http://localhost:5173
2. **Ve a**: Materiales → Orange Oil Brazil
3. **Sube**: orange_oil_batch_B2024.csv
4. **Calcula**: Haz clic en "Calcular Composite"
5. **Explora**: Ver el composite con gráfica y tabla

---

## 📞 Comandos Útiles

### Ver logs en tiempo real:
```bash
# Backend
tail -f "/Users/alonahubarenko/Documents/Marc/Mafer AI/Lluch Regulation/backend/backend.log"

# Frontend
tail -f "/Users/alonahubarenko/Documents/Marc/Mafer AI/Lluch Regulation/frontend/frontend.log"
```

### Reiniciar servicios:
```bash
# Detener todo
pkill -f "uvicorn app.main"
pkill -f "vite"

# Iniciar backend
cd "/Users/alonahubarenko/Documents/Marc/Mafer AI/Lluch Regulation/backend"
source venv/bin/activate
uvicorn app.main:app --reload &

# Iniciar frontend
cd "/Users/alonahubarenko/Documents/Marc/Mafer AI/Lluch Regulation/frontend"
npm run dev &
```

---

## ✅ Checklist de Funcionalidades Implementadas

- [x] Upload de CSV desde interfaz web
- [x] Parser automático de múltiples formatos
- [x] Cálculo de composites con promedio ponderado
- [x] Versionado automático
- [x] Visualización con gráficas (Recharts)
- [x] Tabla detallada de componentes
- [x] Niveles de confianza
- [x] Clasificación automática (componente/impureza)
- [x] API REST completa
- [x] Documentación Swagger
- [x] Base de datos SQLite funcional
- [x] 6 materiales de ejemplo
- [x] 5 archivos CSV de prueba

---

¡Disfruta explorando el sistema! 🎉


