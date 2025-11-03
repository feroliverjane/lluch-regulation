# 🔍 Troubleshooting: Sistemas de Validación AI y Extracción de PDFs

## 📋 Cómo Funcionan los Sistemas de Validación AI

### 1. **Validación de Coherencia AI** (`validate-coherence`)

**Endpoint:** `POST /api/questionnaires/{id}/validate-coherence`

**Cómo funciona:**
1. Toma las respuestas del cuestionario
2. Aplica reglas de coherencia lógica:
   - ✅ "100% Natural" vs "Contiene Aditivos" → CRITICAL
   - ✅ "Vegano" vs "Origen Animal" → CRITICAL
   - ✅ "Orgánico" vs "Usa Pesticidas" → CRITICAL
   - ✅ "Halal" vs "Contiene Etanol" → CRITICAL
   - ✅ "GMO Biocatalyst" sin etiquetar GMO → CRITICAL
   - ✅ RSPO certificado pero no miembro → WARNING
   - ✅ Kosher con ingredientes animales → WARNING
3. Calcula score: 100 - (deducciones por severidad)
4. Retorna lista de issues detectados

**No requiere PDFs** - Solo analiza las respuestas del cuestionario.

---

### 2. **Extracción de Composite desde PDFs** (`extract-composite`)

**Endpoint:** `POST /api/questionnaires/{id}/extract-composite`

**Flujo completo:**

```
1. Usuario sube PDFs → POST /questionnaires/{id}/upload-documents
   ↓
2. PDFs se guardan en: uploads/questionnaires/{id}/
   ↓
3. Metadatos se guardan en questionnaire.attached_documents
   ↓
4. Usuario hace clic en "Extraer Composite"
   ↓
5. Sistema lee los PDFs desde attached_documents
   ↓
6. CompositeExtractorAI procesa:
   a) Intenta extraer texto directo (PyMuPDF)
   b) Si falla, usa OCR (Tesseract + pdf2image)
   c) Busca patrones:
      - CAS numbers: \d{1,7}-\d{2}-\d
      - Porcentajes: XX.X%
      - Nombres de componentes
   d) Valida que % sumen ~100%
   ↓
7. Crea Composite Z1 con componentes extraídos
   ↓
8. Retorna composite_id y confianza
```

**Dependencias críticas:**
- ✅ Tesseract OCR instalado
- ✅ pdf2image funcionando
- ✅ PyMuPDF para extracción de texto
- ✅ PDFs accesibles en disco

---

## 🐛 Problemas Comunes y Soluciones

### ❌ Error: "No documents attached to questionnaire"

**Causa:** No has subido PDFs antes de extraer.

**Solución:**
```
1. Primero: POST /questionnaires/{id}/upload-documents (con archivos PDF)
2. Luego: POST /questionnaires/{id}/extract-composite
```

---

### ❌ Error: "No PDF documents found"

**Causa:** Los documentos subidos no tienen tipo "pdf" en metadata.

**Solución:** Verificar que el endpoint `upload-documents` guarde:
```json
{
  "filename": "documento.pdf",
  "path": "/path/to/file.pdf",
  "upload_date": "2025-10-31T...",
  "type": "pdf"  // ← Este campo es crítico
}
```

---

### ❌ Error: "No components could be extracted"

**Causas posibles:**

1. **PDF sin texto estructurado:**
   - PDF escaneado mal procesado por OCR
   - PDF corrupto
   - PDF protegido con contraseña

2. **Tesseract no instalado:**
   ```bash
   # macOS
   brew install tesseract
   
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr
   
   # Windows
   # Descargar de: https://github.com/UB-Mannheim/tesseract/wiki
   ```

3. **Formato de PDF no reconocido:**
   - El PDF no tiene tabla de composición
   - El texto no sigue el formato esperado:
     ```
     Componente CAS: 78-70-6 Porcentaje: 35.5%
     ```

**Solución:**
- Verificar que Tesseract esté instalado: `tesseract --version`
- Probar con un PDF de ejemplo que tenga formato claro
- Revisar logs del backend para más detalles

---

### ❌ Error: "Error extracting composite" (500)

**Posibles causas:**

1. **PDF no encontrado en disco:**
   - El path guardado en `attached_documents` no existe
   - Los archivos fueron movidos o eliminados

2. **Permisos de archivo:**
   - El servidor no tiene permisos para leer el PDF
   - El directorio de uploads no es accesible

3. **Memoria insuficiente:**
   - PDFs muy grandes causan problemas con OCR
   - Procesar múltiples PDFs simultáneamente

**Solución:**
```python
# Verificar configuración de UPLOAD_DIR en config.py
UPLOAD_DIR = "uploads"  # Debe ser relativo o absoluto

# Verificar permisos
chmod -R 755 uploads/
```

---

### ❌ Error: TesseractNotFoundError

**Causa:** Tesseract no está en el PATH del sistema.

**Solución:**

```python
# En composite_extractor_ai.py, puedes especificar path:
import pytesseract

# macOS
pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'

# Linux
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

---

## 🔧 Verificación y Debug

### 1. Verificar que los PDFs se subieron correctamente:

```bash
# Ver en base de datos
sqlite3 backend/app.db
SELECT id, attached_documents FROM questionnaires WHERE id = {tu_id};
```

Deberías ver JSON con:
```json
[
  {
    "filename": "documento.pdf",
    "path": "uploads/questionnaires/1/documento.pdf",
    "upload_date": "2025-10-31T...",
    "type": "pdf"
  }
]
```

### 2. Verificar que los archivos existen en disco:

```bash
# Buscar archivos subidos
find uploads/ -name "*.pdf" -type f

# Verificar permisos
ls -la uploads/questionnaires/{id}/
```

### 3. Probar extracción manualmente:

```python
# Script de prueba
from app.services.composite_extractor_ai import CompositeExtractorAI

extractor = CompositeExtractorAI()
components, confidence = extractor.extract_from_pdfs([
    "path/to/your/test.pdf"
])

print(f"Components: {len(components)}")
print(f"Confidence: {confidence}%")
for comp in components:
    print(f"  - {comp['component_name']}: {comp['percentage']}%")
```

---

## 📊 Formato Esperado en PDFs

El extractor busca:

### Formato 1: Tabla
```
Component    CAS Number    Percentage
Linalool     78-70-6       35.5%
Citronellol  106-22-9      25.0%
```

### Formato 2: Lista
```
Linalool (CAS: 78-70-6): 35.5%
Citronellol (CAS: 106-22-9): 25.0%
```

### Formato 3: Texto libre
```
El producto contiene 35.5% de Linalool (CAS 78-70-6)...
```

**Requisitos mínimos:**
- ✅ Al menos un CAS number válido
- ✅ Al menos un porcentaje asociado
- ✅ Nombre del componente reconocible

---

## 🚀 Mejoras Recomendadas

### 1. Mejor manejo de errores:

```python
# En extract-composite endpoint, agregar más detalles:
except Exception as e:
    logger.error(f"Error extracting composite: {e}", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error extracting composite: {str(e)}. "
               f"Please verify: 1) Tesseract installed, 2) PDFs accessible, 3) PDF format."
    )
```

### 2. Validación de archivos antes de procesar:

```python
# Verificar que archivos existan
for pdf_path in pdf_paths:
    if not Path(pdf_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF file not found: {pdf_path}"
        )
```

### 3. Logs más detallados:

```python
logger.info(f"Extracting from {len(pdf_paths)} PDFs")
logger.debug(f"PDF paths: {pdf_paths}")
logger.info(f"Extracted {len(components)} components with {confidence}% confidence")
```

---

## 📞 Debugging Paso a Paso

Si sigues teniendo problemas:

1. **Verifica el flujo completo:**
   ```
   ✅ Upload funciona → POST /upload-documents retorna 200
   ✅ Archivos en disco → ls uploads/questionnaires/{id}/
   ✅ Metadata guardada → SELECT attached_documents FROM questionnaires
   ✅ Extract intenta leer → Ver logs del backend
   ```

2. **Revisa logs del backend:**
   ```bash
   # Si estás usando uvicorn directamente
   # Los logs aparecen en la terminal donde corriste uvicorn
   
   # Buscar errores específicos
   grep -i "error\|exception\|traceback" <log_file>
   ```

3. **Prueba con un PDF de ejemplo simple:**
   - Crea un PDF con formato claro
   - Una sola tabla con CAS y porcentajes
   - Sin imágenes complejas

4. **Verifica dependencias:**
   ```bash
   python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
   python -c "import fitz; print(fitz.version)"
   python -c "from pdf2image import convert_from_path; print('OK')"
   ```

---

## 💡 Consejos

- **PDFs de buena calidad:** Escaneados con al menos 300 DPI
- **Formato claro:** Tablas bien estructuradas funcionan mejor
- **CAS numbers visibles:** Deben estar claramente legibles
- **Porcentajes explícitos:** Mejor si están en formato "XX.X%"

---

¿Qué error específico estás viendo? Comparte el mensaje exacto y puedo ayudarte más específicamente! 🚀



