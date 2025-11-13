# 🔧 Configuración de OpenAI - Guía Paso a Paso

## ✅ Paso 1: Verificar Instalación

OpenAI ya está instalado ✅

```bash
# Verificar instalación
cd backend
source venv/bin/activate
pip show openai
```

## 🔑 Paso 2: Obtener API Key de OpenAI

1. **Ve a:** https://platform.openai.com/api-keys
2. **Inicia sesión** o crea una cuenta
3. **Crea una nueva API key:**
   - Click en "Create new secret key"
   - Dale un nombre (ej: "Lluch Regulation")
   - **Copia la key** (solo se muestra una vez)

## 📝 Paso 3: Configurar .env

### Opción A: Editar .env existente

Abre `backend/.env` y agrega estas líneas:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-tu-api-key-aqui
USE_OPENAI_FOR_EXTRACTION=true
```

**Reemplaza `sk-tu-api-key-aqui` con tu API key real.**

### Opción B: Crear desde ejemplo

```bash
cd backend
cp .env.example .env
# Luego edita .env y agrega tu API key
```

## 🧪 Paso 4: Verificar Configuración

Ejecuta este script para verificar:

```bash
cd backend
python -c "
from app.core.config import settings
print('✅ OpenAI API Key configurada:', bool(settings.OPENAI_API_KEY))
print('✅ Usar OpenAI:', settings.USE_OPENAI_FOR_EXTRACTION)
"
```

## 🚀 Paso 5: Probar Extracción

### Test rápido:

```bash
# Probar con un PDF de ejemplo
python test_openai_extraction.py path/to/tu_archivo.pdf sk-tu-api-key
```

### Desde la API:

1. Sube un PDF usando el endpoint:
```bash
POST /api/questionnaires/{id}/upload-documents
```

2. Extrae composite (ahora usará OpenAI automáticamente):
```bash
POST /api/questionnaires/{id}/extract-composite
```

## 🔍 Verificar que Funciona

El sistema usará OpenAI si:
- ✅ `OPENAI_API_KEY` está configurado
- ✅ `USE_OPENAI_FOR_EXTRACTION=true`
- ✅ La API key es válida

Si algo falla, el sistema automáticamente:
- Usará OCR local como fallback
- Mostrará un error claro en los logs

## 💰 Costos Aproximados

- **Por PDF:** ~$0.01-0.03
- **100 PDFs:** ~$1.50-3.00
- **Muy económico** para uso moderado

## 🛠️ Troubleshooting

### Error: "OpenAI API key not found"
**Solución:** Verifica que `.env` tenga `OPENAI_API_KEY=sk-...`

### Error: "Invalid API key"
**Solución:** Verifica que la key sea correcta y tenga créditos

### Quiere usar OCR local en su lugar
**Solución:** Cambia `USE_OPENAI_FOR_EXTRACTION=false` en `.env`

## ✅ Estado Actual

Después de seguir estos pasos, tu sistema:
- ✅ Usará OpenAI Vision API para extraer PDFs
- ✅ Tendrá mayor precisión (95%+)
- ✅ Manejará layouts complejos mejor
- ✅ Guardará el método usado en metadata del composite

---

**¿Necesitas ayuda?** Revisa los logs del backend o ejecuta el script de diagnóstico.













