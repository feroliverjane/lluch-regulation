# Deploy en Netlify - Lluch Regulation

## Configuración del Deploy

### 1. Archivos de Configuración

El proyecto ya incluye los siguientes archivos para Netlify:

- `netlify.toml` - Configuración principal de Netlify
- `frontend/public/_redirects` - Redirecciones para SPA y API

### 2. Variables de Entorno

Para el deploy en producción, necesitas configurar las siguientes variables de entorno en Netlify:

```
VITE_API_URL=https://tu-backend-url.com
```

### 3. Pasos para el Deploy

#### Opción A: Deploy desde Git (Recomendado)

1. **Conecta tu repositorio a Netlify:**
   - Ve a [netlify.com](https://netlify.com)
   - Haz clic en "New site from Git"
   - Conecta tu repositorio de GitHub/GitLab/Bitbucket

2. **Configura el build:**
   - Build command: `npm run build`
   - Publish directory: `frontend/dist`
   - Base directory: `frontend`

3. **Configura las variables de entorno:**
   - Ve a Site settings > Environment variables
   - Añade `VITE_API_URL` con la URL de tu backend

#### Opción B: Deploy Manual

1. **Prepara el build:**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Sube la carpeta `dist`:**
   - Arrastra la carpeta `frontend/dist` a Netlify
   - O usa el CLI: `netlify deploy --dir=frontend/dist --prod`

### 4. Configuración del Backend

Para que el frontend funcione correctamente, necesitas:

1. **Deployar el backend** en un servicio como:
   - Heroku
   - Railway
   - DigitalOcean App Platform
   - AWS/GCP/Azure

2. **Actualizar la URL del backend** en las variables de entorno de Netlify

### 5. Redirecciones

El archivo `_redirects` está configurado para:
- Redirigir todas las llamadas `/api/*` a tu backend
- Manejar el routing del lado del cliente (SPA)

### 6. Verificación Post-Deploy

Después del deploy, verifica:

- [ ] El sitio carga correctamente
- [ ] Las llamadas a la API funcionan
- [ ] El routing del cliente funciona (navegación entre páginas)
- [ ] Los archivos estáticos se sirven correctamente

### 7. Optimizaciones Adicionales

Para mejorar el rendimiento:

1. **Code Splitting:** Considera implementar lazy loading para reducir el bundle inicial
2. **CDN:** Netlify ya incluye CDN global
3. **Caching:** Configura headers de cache para assets estáticos

### 8. Monitoreo

- Usa Netlify Analytics para monitorear el rendimiento
- Configura alertas para errores de build
- Monitorea las métricas de la API del backend

## Troubleshooting

### Error: "Cannot find module"
- Verifica que todas las dependencias estén en `package.json`
- Ejecuta `npm install` antes del build

### Error: "API calls failing"
- Verifica que `VITE_API_URL` esté configurado correctamente
- Comprueba que el backend esté desplegado y accesible

### Error: "Page not found on refresh"
- Verifica que el archivo `_redirects` esté en `frontend/public/`
- Asegúrate de que la regla `/* /index.html 200` esté presente


