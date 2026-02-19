# Plataforma de Inteligencia de Negocio — RC Deportivo

Dashboard interactivo construido con Dash/Plotly para la gestión integral del RC Deportivo de La Coruña.

## Despliegue en Render

### 1. Subir a GitHub
```bash
git init
git add .
git commit -m "Initial deploy"
git remote add origin <URL_REPO>
git push -u origin main
```

### 2. Crear servicio en Render
1. Ir a [render.com](https://render.com) → **New Web Service**
2. Conectar el repositorio de GitHub
3. Configuración:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:server --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`

### 3. Variables de entorno (obligatorias)
Configurar en Render → Environment:

| Variable | Valor |
|---|---|
| `MYSQL_USER` | `alen_depor` |
| `MYSQL_PASSWORD` | *(contraseña de la BD)* |
| `MYSQL_HOST` | `82.165.192.201` |
| `MYSQL_DATABASE` | `Dash_Negocio` |

### 4. Verificar
Una vez desplegado, acceder a la URL proporcionada por Render. Se mostrará la pantalla de login.
