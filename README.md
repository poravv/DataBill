# Invoice Processing System

Sistema de procesamiento de facturas utilizando OpenAI Vision para extracción automática de datos.

## Requisitos

- Python 3.11+
- MongoDB
- OpenAI API Key
- Minio Server (para almacenamiento de imágenes)

## Configuración

1. Crear y activar entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
Crear archivo `.env`:
```env
# OpenAI y Flask
OPENAI_API_KEY=your_key
SECRET_KEY=your_secret

# MongoDB
MONGO_URI=your_mongo_uri
MONGODB_DB=dbinvoice
MONGODB_COLLECTION=invoices

# Minio Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_SECURE=False
MINIO_BUCKET=invoices
```

4. Iniciar Minio Server:
```bash
docker run -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ":9001"
```

## Ejecución

```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

## Documentación API

Swagger UI disponible en `http://localhost:5000/docs`

### Endpoints Principales

- `POST /api/v1/invoice/upload` - Subir y procesar factura
- `GET /api/v1/invoices` - Listar facturas
- `PUT /api/v1/invoice/{id}` - Actualizar factura
- `GET /api/v1/export/json` - Exportar datos

## Estructura

### Endpoints Web
- **Interfaz de Usuario**
  - `/` - Página principal
  - `/upload` - Subir nueva factura
  - `/invoices` - Ver todas las facturas
  - `/verify_invoices` - Verificar facturas pendientes
  - `/export` - Descargar facturas en formato Excel

### Características
- Autenticación mediante tokens
- Paginación y filtrado de resultados
- Respuestas en formato JSON
- Manejo de errores estandarizado
- Interfaz Swagger UI para pruebas

## Almacenamiento

El sistema utiliza Minio como servidor de almacenamiento de objetos:
- Las imágenes de facturas se almacenan en Minio
- Accesible a través del endpoint configurado
- Interfaz web de administración en puerto 9001
- Bucket automáticamente creado al iniciar la aplicación

### Uso del Sistema
1. **Web UI**: Accede a http://localhost:5000
2. **API Docs**: Accede a http://localhost:5000/docs
3. **Swagger JSON**: Disponible en http://localhost:5000/apispec.json

### Desarrollador
- **Autor**: Lic. Andres Vera
- **Año**: 2024
- **Documentación**: http://localhost:5000/docs

