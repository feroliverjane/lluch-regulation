# Formatos JSON: Lluch vs Responses

## 📋 Formato Lluch (Original)

El formato **Lluch** es el formato original que viene del sistema Lluch. Es un formato de **array de objetos** con estructura plana.

### Estructura:

```json
{
  "requestId": 2027,
  "data": [
    {
      "fieldCode": "q3t1s2f15",
      "fieldName": "Supplier Name",
      "fieldType": "inputText",
      "value": "M.P.E MATIERES PREMIERES ESSENTIELL"
    },
    {
      "fieldCode": "q3t1s2f16",
      "fieldName": "Product Name",
      "fieldType": "inputText",
      "value": "[BASIL0003] H.E. BASILIC INDES"
    },
    {
      "fieldCode": "q3t1s2f23",
      "fieldName": "CAS",
      "fieldType": "inputText",
      "value": "8015-73-4"
    }
  ]
}
```

### Características:

- ✅ **Estructura externa**: Objeto con `requestId` y `data` (array)
- ✅ **Formato de campo**: Cada campo es un objeto con propiedades `fieldCode`, `fieldName`, `fieldType`, `value`
- ✅ **Orden preservado**: Los campos están en orden dentro del array
- ✅ **Metadatos**: Incluye `requestId` a nivel raíz
- ✅ **Formato estándar Lluch**: Este es el formato que viene directamente del sistema Lluch

---

## 📋 Formato Responses (Interno)

El formato **Responses** es el formato que usa nuestro sistema internamente después de parsear el formato Lluch. Es un **objeto/diccionario** indexado por `fieldCode`.

### Estructura:

```json
{
  "q3t1s2f15": {
    "name": "Supplier Name",
    "type": "inputText",
    "value": "PROVEEDOR PRUEBA TEST"
  },
  "q3t1s2f16": {
    "name": "Product Name",
    "type": "inputText",
    "value": "PRODUCTO PRUEBA TEST"
  },
  "q3t1s2f23": {
    "name": "CAS",
    "type": "inputText",
    "value": "TEST-123-4"
  }
}
```

### Características:

- ✅ **Estructura interna**: Objeto/diccionario directo, sin `requestId` ni `data`
- ✅ **Clave principal**: El `fieldCode` es la clave del objeto
- ✅ **Propiedades simplificadas**: `name`, `type`, `value` (en lugar de `fieldName`, `fieldType`, `value`)
- ✅ **Acceso rápido**: Permite acceso directo por `fieldCode` (ej: `responses["q3t1s2f15"]`)
- ✅ **Formato optimizado**: Más eficiente para búsquedas y validaciones

---

## 🔄 Conversión entre Formatos

### Lluch → Responses (Parsing)

El parser (`QuestionnaireJSONParser`) convierte el formato Lluch al formato Responses:

```python
# Entrada (Lluch):
{
  "requestId": 2027,
  "data": [
    {
      "fieldCode": "q3t1s2f15",
      "fieldName": "Supplier Name",
      "fieldType": "inputText",
      "value": "M.P.E MATIERES PREMIERES ESSENTIELL"
    }
  ]
}

# Salida (Responses):
{
  "q3t1s2f15": {
    "name": "Supplier Name",
    "type": "inputText",
    "value": "M.P.E MATIERES PREMIERES ESSENTIELL"
  }
}
```

**Proceso de conversión:**

1. Extrae `requestId` → se guarda en metadatos
2. Itera sobre el array `data`
3. Para cada campo:
   - Usa `fieldCode` como clave del diccionario
   - Convierte `fieldName` → `name`
   - Convierte `fieldType` → `type`
   - Mantiene `value` igual
4. Ignora campos en blanco (`fieldType == "blank"`)

### Responses → Lluch (Si fuera necesario)

Aunque no está implementado actualmente, la conversión inversa sería:

```python
# Entrada (Responses):
{
  "q3t1s2f15": {
    "name": "Supplier Name",
    "type": "inputText",
    "value": "M.P.E MATIERES PREMIERES ESSENTIELL"
  }
}

# Salida (Lluch):
{
  "requestId": 2027,  # desde metadatos
  "data": [
    {
      "fieldCode": "q3t1s2f15",
      "fieldName": "Supplier Name",
      "fieldType": "inputText",
      "value": "M.P.E MATIERES PREMIERES ESSENTIELL"
    }
  ]
}
```

---

## 📊 Comparación Visual

| Aspecto | Formato Lluch | Formato Responses |
|--------|---------------|-------------------|
| **Estructura principal** | Objeto con `requestId` y `data` (array) | Objeto/diccionario directo |
| **Organización** | Array de objetos | Diccionario indexado por `fieldCode` |
| **Acceso a campos** | Búsqueda en array | Acceso directo: `responses["q3t1s2f15"]` |
| **Propiedades** | `fieldCode`, `fieldName`, `fieldType`, `value` | `name`, `type`, `value` |
| **Metadatos** | `requestId` en raíz | `requestId` guardado en metadatos separados |
| **Uso** | Archivos de entrada (importación) | Almacenamiento interno (base de datos) |
| **Rendimiento** | Requiere búsqueda O(n) | Acceso O(1) por `fieldCode` |

---

## 📁 Archivos de Ejemplo

### Formato Lluch (Original):
- `data/questionnaires/JSON Z1_Basicilo_MPE.txt` ✅ Formato Lluch completo

### Formato Responses (Interno):
- `data/questionnaires/test_import_validation.json` ⚠️ Formato Responses (debería ser Lluch para importación)

---

## ⚠️ Problema con el Archivo de Prueba

El archivo `test_import_validation.json` está en formato **Responses** (objeto indexado por `fieldCode`), pero el sistema de importación espera el formato **Lluch** (con `requestId` y `data` como array).

**Solución:** El archivo de prueba debería tener el formato Lluch para que funcione correctamente con el endpoint de importación.

---

## 🔍 Cómo Identificar el Formato

### Formato Lluch:
```json
✅ Tiene "requestId" en la raíz
✅ Tiene "data" como array
✅ Cada elemento tiene "fieldCode", "fieldName", "fieldType"
```

### Formato Responses:
```json
✅ Es un objeto directo (sin "requestId" ni "data")
✅ Las claves son "fieldCode" (ej: "q3t1s2f15")
✅ Cada valor tiene "name", "type", "value"
```

---

## 📝 Notas Importantes

1. **Almacenamiento en BD**: El sistema almacena los cuestionarios en formato **Responses** en la columna `responses` (tipo JSON)
2. **Importación**: El endpoint `/api/questionnaires/import/json` espera formato **Lluch**
3. **Validación**: La validación contra BlueLine funciona con formato **Responses** (ambos en la misma estructura)
4. **Conversión automática**: El parser convierte automáticamente Lluch → Responses durante la importación

