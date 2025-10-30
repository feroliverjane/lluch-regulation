# Guía de Prueba - Sistema Material-Supplier

## Ubicación de MaterialSuppliers en BlueLineDetail

Los **MaterialSuppliers** aparecen al **final de la página BlueLineDetail**, después de:
1. Información General (ID, Tipo, Estado Sync, Composite, etc.)
2. Sección de Composite (si existe)
3. Sección de Datos de la Blue Line (tabs con campos)

La sección se llama: **"Material-Proveedores Asociados"**

## 📍 URLs para Probar

### 1. Ver BlueLine Detail con MaterialSuppliers
**URL:** `http://localhost:5173/blue-line/material/10`

**Dónde verlos:**
- Desplázate hasta el **final de la página**
- Busca la sección **"Material-Proveedores Asociados (2)"**
- Verás 2 proveedores listados:
  - PROVEEDOR PRUEBA TEST (Score: 80%)
  - M.P.E MATIERES PREMIERES ESSENTIELL (Score: 70%)

**Funcionalidad:**
- Haz clic en cualquier proveedor para **expandir/colapsar**
- Al expandir verás:
  - ID del Cuestionario (con link)
  - Fecha de Validación
  - Diferencias aceptadas vs no aceptadas

### 2. Importar Nuevo Cuestionario
**URL:** `http://localhost:5173/questionnaires/import`

**Pasos:**
1. Selecciona el archivo: `data/questionnaires/test_import_validation_lluch.json`
2. El sistema detectará automáticamente el material BASIL0003
3. Después de importar, verás:
   - **Comparación automática** con los 10 campos
   - **Score de validación** (0-100%)
   - **Lista de diferencias** con checkboxes
   - **Botón "Aceptar todas las diferencias"**
   - **Botón "Aceptar Cuestionario y Crear MaterialSupplier"**

**Diferentes escenarios:**
- **Si Blue Line existe:** Verás comparación y podrás aceptar/rechazar diferencias
- **Si Blue Line NO existe:** Verás mensaje y botón para crear Blue Line desde el cuestionario

### 3. Ver Cuestionario Detalle
**URL:** `http://localhost:5173/questionnaires/9`

Verás el cuestionario completo con todos los campos organizados por tabs y secciones.

## 🧪 Datos de Ejemplo Creados

### Material 10 (BASIL0003 - H.E. BASILIC INDES)
- **BlueLine ID:** 7
- **MaterialSuppliers:** 2
  1. **ID 1:** PROVEEDOR PRUEBA TEST (Score: 80%)
  2. **ID 2:** M.P.E MATIERES PREMIERES ESSENTIELL (Score: 70%, con 2 diferencias aceptadas)

### Cuestionario de Ejemplo
- **ID 9:** Cuestionario con diferencias intencionales
- **Diferencias:** Product Name, CAS Number, Kosher Certificate
- **Diferencias aceptadas:** Product Name, CAS Number

## 🔍 Qué Buscar en BlueLineDetail

1. **Desplázate hasta el final** de la página
2. **Busca la sección** con fondo oscuro (`#1f2937`) que dice:
   ```
   Material-Proveedores Asociados (2)
   ```
3. **Verás 2 cards** expandibles:
   - Cada card muestra:
     - Nombre del proveedor
     - Código del proveedor
     - Score de validación (badge de color según score)
     - Estado (ACTIVE/INACTIVE)
     - Icono de chevron (▼/▲) para expandir/colapsar

4. **Al hacer clic** para expandir:
   - Verás ID del Cuestionario (con link)
   - Fecha de Validación
   - Lista de diferencias:
     - **Verde:** Diferencias aceptadas
     - **Rojo:** Diferencias no aceptadas

## 📝 Archivo JSON de Prueba

**Ubicación:** `data/questionnaires/test_import_validation_lluch.json`

**Contenido:**
- Formato Lluch completo
- 177 campos
- Material: BASIL0003
- Diferencias intencionales para probar comparación

## ✅ Checklist de Pruebas

- [ ] Ver MaterialSuppliers en BlueLineDetail (`/blue-line/material/10`)
- [ ] Expandir/colapsar proveedores
- [ ] Ver detalles de diferencias aceptadas
- [ ] Importar cuestionario JSON (`/questionnaires/import`)
- [ ] Ver comparación automática
- [ ] Aceptar/rechazar diferencias individualmente
- [ ] Aceptar todas las diferencias
- [ ] Crear MaterialSupplier
- [ ] Verificar que aparece en BlueLineDetail
- [ ] Crear Blue Line desde cuestionario (si no existe)
- [ ] Crear Composite Z1 después de crear Blue Line

## 🎯 Flujo Completo de Prueba

1. **Importar Cuestionario:**
   - Ve a `/questionnaires/import`
   - Selecciona `test_import_validation_lluch.json`
   - Verifica que detecta material automáticamente
   - Verifica comparación automática

2. **Gestionar Diferencias:**
   - Marca algunas diferencias como aceptadas
   - Haz clic en "Aceptar todas" para probar
   - Crea MaterialSupplier

3. **Verificar en BlueLineDetail:**
   - Ve a `/blue-line/material/10`
   - Desplázate hasta el final
   - Verifica que el nuevo MaterialSupplier aparece
   - Expande para ver detalles

4. **Probar Creación de Blue Line:**
   - Importa un cuestionario para un material sin Blue Line
   - Verifica mensaje "No existe Blue Line"
   - Crea Blue Line desde cuestionario
   - Responde "Sí" a crear Composite Z1
   - Verifica que todo se crea correctamente

