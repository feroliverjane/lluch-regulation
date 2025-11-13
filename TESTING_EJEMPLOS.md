# Ejemplos para Testing del Sistema de Validación

Este documento describe los archivos de ejemplo disponibles para probar el sistema de validación de cuestionarios.

## 📄 Archivos JSON Disponibles

### 1. `test_validation_with_mismatches.json` ⭐ **RECOMENDADO PARA VALIDACIÓN**
- **Material:** BASIL0003 (existe con Blue Line)
- **Propósito:** Probar la visualización de campos que NO coinciden marcados en ROJO
- **Diferencias intencionales:** 7 campos no coinciden
  - Product Name: "[BASIL0003] H.E. BASILIC INDES MODIFIED" (vs esperado)
  - Product Code: "BASIL0003-TEST" (vs "BASIL0003")
  - CAS: "8015-73-4" (vs esperado)
  - Kosher Certificate: false (vs true)
  - 100% Natural: NO (vs YES)
  - 100% Pure: NO (vs YES)
  - Country: FR (vs BG)
  - Botanical Name: diferente
- **Score esperado:** ~30% (3 de 10 campos coinciden)
- **Uso:**
  1. Abre el frontend en http://localhost:5173
  2. Ve a "Importar Cuestionario"
  3. Selecciona `data/questionnaires/test_validation_with_mismatches.json`
  4. Observa cómo se detecta BASIL0003 automáticamente
  5. Haz clic en "Validar Cuestionario"
  6. Verás 7 campos marcados en ROJO con todas las diferencias

### 2. `test_manual_vanilla.json`
- **Material:** VANILLA001 (nuevo - no existe)
- **Propósito:** Probar detección de material nuevo y creación
- **Uso:**
  1. Selecciona el archivo en el frontend
  2. El sistema detectará VANILLA001 automáticamente
  3. Verás el mensaje de "Material Nuevo Detectado"
  4. Puedes crear el material desde el modal integrado

### 3. `test_manual_jasmine.json`
- **Material:** JASMINE001 (nuevo - no existe)
- **Propósito:** Alternativa para probar detección de material nuevo
- **Uso:** Similar a test_manual_vanilla.json

## 🧪 Scripts de Testing

### `test_validation_flow.py`
Script completo que prueba:
- ✅ Verificación de materiales existentes
- ✅ Verificación de Blue Lines
- ✅ Importación de cuestionario con diferencias
- ✅ Validación de comparación y score
- ✅ Listado de campos que no coinciden

**Ejecutar:**
```bash
python3 test_validation_flow.py
```

### `test_new_material_detection.py`
Script que prueba la detección de materiales nuevos.

**Ejecutar:**
```bash
python3 test_new_material_detection.py
```

### `borrar_material_test.py`
Script para eliminar materiales de prueba.

**Ejecutar:**
```bash
# Eliminar un material específico
python3 borrar_material_test.py JASMINE001

# Modo interactivo
python3 borrar_material_test.py
```

## 📋 Casos de Uso Recomendados

### Caso 1: Probar Validación con Diferencias (ROJO)
1. Asegúrate de que BASIL0003 existe con Blue Line
2. Usa `test_validation_with_mismatches.json`
3. Verás 7 campos marcados en ROJO

### Caso 2: Probar Material Nuevo
1. Elimina el material de prueba primero:
   ```bash
   python3 borrar_material_test.py VANILLA001
   ```
2. Usa `test_manual_vanilla.json`
3. Verás el flujo completo de creación de material nuevo

### Caso 3: Probar Validación Perfecta
1. Crea un cuestionario JSON idéntico a la Blue Line
2. Todos los campos deberían coincidir
3. Score: 100%

## 🔍 Verificación de Resultados

Después de importar `test_validation_with_mismatches.json`, deberías ver:

- ✅ **Score de Validación:** 30%
- ✅ **Campos que coinciden:** 3 de 10
- ✅ **Campos que NO coinciden:** 7 (marcados en ROJO)
- ✅ **Cada campo en rojo muestra:**
  - Nombre del campo con icono ❌
  - Valor Esperado (de Blue Line)
  - Valor Actual (del cuestionario)
  - Severidad (CRITICAL/WARNING)

## 🎯 Checklist de Testing

- [ ] Material se detecta automáticamente del JSON
- [ ] Botón cambia a "Validar Cuestionario" cuando hay material detectado
- [ ] Comparación se realiza automáticamente
- [ ] Score de validación se muestra correctamente
- [ ] Campos que NO coinciden aparecen en ROJO
- [ ] Valores "Esperado" vs "Actual" se muestran claramente
- [ ] Checkboxes funcionan para aceptar diferencias
- [ ] Botón "Aceptar todas" funciona
- [ ] Botón "Ver Cuestionario Importado" navega correctamente
- [ ] No hay navegación automática (usuario controla)














