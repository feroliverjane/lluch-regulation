#!/bin/bash

# Script para deploy en Netlify
# Uso: ./deploy-netlify.sh

echo "🚀 Iniciando deploy para Netlify..."

# Verificar que estamos en el directorio correcto
if [ ! -f "netlify.toml" ]; then
    echo "❌ Error: No se encontró netlify.toml. Ejecuta este script desde la raíz del proyecto."
    exit 1
fi

# Navegar al directorio del frontend
cd frontend

echo "📦 Instalando dependencias..."
npm install

echo "🔨 Construyendo la aplicación..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Error: El build falló. Revisa los errores arriba."
    exit 1
fi

echo "✅ Build completado exitosamente!"
echo ""
echo "📋 Próximos pasos para el deploy:"
echo "1. Ve a https://netlify.com"
echo "2. Haz clic en 'New site from Git'"
echo "3. Conecta tu repositorio"
echo "4. Configura:"
echo "   - Build command: npm run build"
echo "   - Publish directory: frontend/dist"
echo "   - Base directory: frontend"
echo "5. Añade la variable de entorno VITE_API_URL con tu URL del backend"
echo ""
echo "📁 Los archivos de build están en: frontend/dist"
echo "📄 Revisa DEPLOY_NETLIFY.md para más detalles"


