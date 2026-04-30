# StayHub Backend

Backend REST de StayHub, desarrollado con FastAPI, SQLAlchemy y `psycopg2-binary` para exponer la lógica de la base de datos PostgreSQL.

Este backend está pensado como una capa de acceso a datos y exposición de endpoints. La evaluación principal del proyecto está en la base de datos, por lo que la implementación backend se mantiene simple y sin lógica de negocio compleja.

## Estado actual

El backend está preparado para integrarse con la base de datos del proyecto, pero su funcionamiento completo depende de que estén creadas las tablas, relaciones, restricciones y datos seed definidos por el equipo de base de datos.

## Tecnologías

- Python 3.12
- FastAPI
- SQLAlchemy 2.x
- psycopg2-binary
- Pydantic v2
- uv
- PostgreSQL 16 + PostGIS

## Estructura

```text
backend/
├── Dockerfile
├── pyproject.toml
├── README.md
└── app/
    ├── main.py
    ├── database.py
    ├── models/
    ├── routers/
    └── schemas/
```

## Variables de entorno

El backend toma la configuración desde el archivo `.env` ubicado en la raíz del proyecto.

```env
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_PORT=
```

> El host de la base de datos dentro de Docker es `db`, porque coincide con el nombre del servicio en `docker-compose.yml`.

## Instalación local con `uv`

Desde la carpeta `backend/`:

```bash
uv sync
```

Esto crea el entorno virtual y instala las dependencias del `pyproject.toml`.

## Ejecución local

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Luego podés abrir:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

## Ejecución con Docker

Desde la raíz del proyecto:

```bash
docker compose up -d --build
```

Servicios principales:

- `db`: PostgreSQL + PostGIS
- `backend`: API FastAPI
- `pgadmin`: interfaz visual para PostgreSQL

## Endpoints

### Health

- `GET /health`

Respuesta esperada:

```json
{
  "status": "healthy"
}
```

### Usuarios

Prefijo: `/usuarios`

- `GET /usuarios/` - listar usuarios
- `GET /usuarios/{id}` - obtener usuario por ID
- `POST /usuarios/` - crear usuario

### Propiedades

Prefijo: `/propiedades`

- `GET /propiedades/` - listar propiedades con filtros opcionales por `ciudad`, `tipo`, `precio_min` y `precio_max`
- `GET /propiedades/{id}` - obtener propiedad por ID
- `POST /propiedades/` - crear propiedad
- `PUT /propiedades/{id}` - actualizar propiedad
- `DELETE /propiedades/{id}` - baja lógica, cambia el estado a `eliminada`

### Reservas

Prefijo: `/reservas`

- `GET /reservas/` - listar reservas con filtros opcionales por `estado`, `huesped_id` y `propiedad_id`
- `GET /reservas/{id}` - obtener reserva por ID
- `POST /reservas/` - crear reserva
- `PATCH /reservas/{id}/estado` - actualizar solo el estado

## Modelos y schemas

La carpeta `app/models/` contiene los modelos ORM de SQLAlchemy que representan tablas existentes en PostgreSQL.

La carpeta `app/schemas/` contiene los schemas Pydantic para requests y responses.

Convención usada:

- `Base`: campos comunes
- `Create`: datos requeridos para crear
- `Response`: salida hacia el cliente

## Reglas de diseño respetadas

- No se usa SQL crudo en el backend.
- No se crean índices desde Python.
- No se generan migraciones automáticas.
- No se usa `Base.metadata.create_all()`.
- No se implementa autenticación compleja.
- No se agregan tests.

## Nota importante sobre la base de datos

Este backend depende de la implementación final de la base de datos del proyecto. Eso significa que la API puede arrancar y mostrar su documentación, pero el comportamiento completo depende de que existan:

- tablas creadas
- relaciones correctas
- datos seed
- restricciones
- transacciones definidas por el equipo de base de datos

Cuando la base de datos esté lista, el backend ya queda preparado para conectarse sin cambios estructurales grandes.
