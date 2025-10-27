# Deploy del Backend - Lluch Regulation

## 🚀 Deploy en Railway (Recomendado)

### Paso 1: Preparar el Repositorio

1. **Sube tu código a GitHub** (si no lo has hecho ya)
2. **Asegúrate de que todos los archivos estén en el repositorio**

### Paso 2: Crear Proyecto en Railway

1. **Ve a [railway.app](https://railway.app)**
2. **Inicia sesión** con GitHub
3. **Haz clic en "New Project"**
4. **Selecciona "Deploy from GitHub repo"**
5. **Elige tu repositorio**

### Paso 3: Configurar el Servicio

1. **Railway detectará automáticamente** que es un proyecto Python
2. **Configura las variables de entorno:**

#### Variables de Entorno Requeridas:
```
SECRET_KEY=tu-clave-secreta-super-segura
DATABASE_URL=postgresql://... (Railway la proporciona automáticamente)
ALLOWED_ORIGINS=https://tu-netlify-site.netlify.app,http://localhost:5173
```

#### Variables Opcionales:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password
SMTP_FROM=noreply@lluchregulation.com
```

### Paso 4: Configurar PostgreSQL

1. **En Railway, haz clic en "Add Service"**
2. **Selecciona "Database" > "PostgreSQL"**
3. **Railway creará automáticamente la variable `DATABASE_URL`**

### Paso 5: Deploy

1. **Railway comenzará el deploy automáticamente**
2. **Espera a que se complete** (5-10 minutos)
3. **Obtén la URL** de tu backend (algo como `https://tu-proyecto.railway.app`)

## 🔧 Configuración Post-Deploy

### 1. Actualizar Frontend en Netlify

1. **Ve a tu proyecto en Netlify**
2. **Site settings > Environment variables**
3. **Actualiza `VITE_API_URL`** con la URL de Railway

### 2. Actualizar Redirecciones

1. **En Netlify, ve a Site settings > Redirects and rewrites**
2. **Actualiza la regla:**
   ```
   /api/* https://tu-proyecto.railway.app/api/:splat 200
   ```

### 3. Verificar el Deploy

1. **Visita `https://tu-proyecto.railway.app/docs`** - Deberías ver la documentación de la API
2. **Prueba tu frontend** - Las llamadas a la API deberían funcionar

## 🛠️ Troubleshooting

### Error: "Database connection failed"
- Verifica que PostgreSQL esté configurado en Railway
- Revisa que `DATABASE_URL` esté configurada correctamente

### Error: "CORS policy"
- Añade tu dominio de Netlify a `ALLOWED_ORIGINS`
- Formato: `https://tu-sitio.netlify.app`

### Error: "Module not found"
- Verifica que `requirements.txt` esté en la raíz del backend
- Asegúrate de que todas las dependencias estén listadas

## 📊 Monitoreo

### Railway Dashboard
- **Logs**: Ve los logs en tiempo real
- **Metrics**: CPU, memoria, requests
- **Variables**: Gestiona variables de entorno

### Health Check
- **Endpoint**: `https://tu-proyecto.railway.app/docs`
- **Status**: Debería mostrar la documentación de FastAPI

## 💰 Costos

### Railway Free Tier:
- **500 horas/mes** (suficiente para desarrollo)
- **1GB RAM**
- **1GB storage**
- **PostgreSQL incluido**

### Si necesitas más recursos:
- **$5/mes** por servicio adicional
- **Escalado automático**

## 🔄 Deploy Automático

Una vez configurado, Railway hará deploy automático cada vez que hagas push a tu repositorio.

### Comandos Útiles:
```bash
# Ver logs en tiempo real
railway logs

# Conectar a la base de datos
railway connect

# Ejecutar comandos en el servidor
railway run python -m app.scripts.generate_dummy_data
```


