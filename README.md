# 🏠 StayHub — Plataforma de Gestión de Alojamientos

## 📚 Cátedra

**Base de Datos Avanzada** — Universidad Tecnológica Nacional FRSR

## 👥 Integrantes grupo 10

| Nombre                            |
| ----------------------------------|
| Moya, Carlos Esteban              |
| Iriarte Lopez, Ana Valentina      |
| Parada Hernandez, Yianela Solange |
| Vulcano, Candela Nair             |
| Reali, Tomas                      |

---

## 📌 Descripción

Proyecto académico desarrollado para demostrar el uso avanzado de motores de base de datos relacionales, cubriendo índices, transacciones, backups y optimización de consultas sobre un dominio de negocio real.

StayHub es una plataforma simplificada de gestión de alojamientos (estilo Airbnb) donde propietarios pueden publicar propiedades y huéspedes pueden realizar reservas. El foco del proyecto está en la **capa de base de datos**: diseño del modelo, estrategia de indexación, integridad transaccional y política de backups.

El backend actúa únicamente como capa de exposición de la lógica implementada en PostgreSQL.

---

## 🛠️ Stack Tecnológico

### Base de Datos

| Tecnología        | Uso                                                         |
| ----------------- | ----------------------------------------------------------- |
| **PostgreSQL 16** | Motor principal de base de datos relacional                 |
| **PostGIS**       | Extensión espacial para búsquedas por proximidad geográfica |

### Backend

| Tecnología      | Uso                                              |
| --------------- | ------------------------------------------------ |
| **Python 3.12** | Lenguaje principal del servidor                  |
| **FastAPI**     | Framework HTTP para exposición de endpoints REST |
| **SQLAlchemy**  | ORM y manejo de conexiones                       |
| **Psycopg2**    | Driver nativo PostgreSQL                         |
| **Uvicorn**     | Servidor ASGI                                    |

### Infraestructura y Herramientas

| Tecnología                  | Uso                                               |
| --------------------------- | ------------------------------------------------- |
| **Docker / Docker Compose** | Contenerización de la base de datos y el servicio |
| **pgAdmin 4**               | Administración visual de PostgreSQL               |
| **pg_dump / pg_restore**    | Backups lógicos programados                       |
| **Git**                     | Control de versiones                              |

---

## 🗄️ Temas de Base de Datos Aplicados

### 🔁 Backups

- Backup completo con `pg_dump` en formato custom (binario comprimido)
- Genera archivos con timestamp en `backend/backups/`
- Rotación automática: un script elimina los backups con más de 7 días de antigüedad (`backup_auto.py`)
- Verificación automática de integridad: valida que el archivo se creó y no está vacío
- Manejo de errores: rollback automático del archivo si algo falla
- Script separado `restore_db.py` para restauración con `pg_restore`
- Ejecución automática programada mediante `cron` a las 02:00 AM todos los días

### 🔍 Índices

La estrategia de indexación cubre los patrones de acceso reales del sistema: búsquedas por rango, lookups de igualdad, filtros combinados, consultas dentro de estructuras JSON/array y búsqueda espacial con PostGIS. Todos los índices están definidos en la migración Alembic `95648156dc74_initial_schema.py` y se aplican automáticamente con `alembic upgrade head`.

#### B-Tree (por defecto) — rangos y ordenamiento

| Índice                   | Tabla         | Columnas                          | Uso                                            |
| ------------------------ | ------------- | --------------------------------- | ---------------------------------------------- |
| `idx_propiedades_precio` | `propiedades` | `precio`                          | Filtros por rango de precio                    |
| `idx_propiedades_tipo`   | `propiedades` | `tipo`                            | Filtro por tipo de alojamiento                 |
| `idx_reservas_fechas`    | `reservas`    | `fecha_checkin`, `fecha_checkout` | Búsqueda de disponibilidad por rango de fechas |
| `idx_reservas_estado`    | `reservas`    | `estado`                          | Filtro por estado de reserva                   |
| `idx_reservas_creado_en` | `reservas`    | `creado_en`                       | Ordenamiento cronológico                       |
| `ix_usuarios_rol`        | `usuarios`    | `rol`                             | Filtro por rol (huesped / propietario / admin) |
| `ix_propiedades_ciudad`  | `propiedades` | `ciudad`                          | Filtro por ciudad                              |

#### Hash — igualdad exacta O(1)

| Índice                    | Tabla      | Columnas | Uso                                                     |
| ------------------------- | ---------- | -------- | ------------------------------------------------------- |
| `idx_usuarios_email_hash` | `usuarios` | `email`  | Login: lookup por email exacto, sin necesidad de rangos |

> Hash es más eficiente que B-Tree para búsquedas de igualdad pura. Se eligió aquí porque el email nunca se consulta con `LIKE` ni con rangos.

#### Compuestos — filtros combinados

| Índice                          | Tabla         | Columnas                  | Uso                                                     |
| ------------------------------- | ------------- | ------------------------- | ------------------------------------------------------- |
| `idx_propiedades_ciudad_precio` | `propiedades` | `ciudad`, `precio`        | Búsqueda de propiedades por ciudad con filtro de precio |
| `ix_ciudad_estado`              | `propiedades` | `ciudad`, `estado`        | Filtro combinado ciudad + estado de publicación         |
| `idx_reservas_estado_checkin`   | `reservas`    | `estado`, `fecha_checkin` | Consultas de reservas activas ordenadas por fecha       |

#### Parciales — subconjuntos de alta frecuencia

| Índice                        | Tabla         | Condición                                     | Uso                                                                                    |
| ----------------------------- | ------------- | --------------------------------------------- | -------------------------------------------------------------------------------------- |
| `idx_propiedades_disponibles` | `propiedades` | `WHERE estado = 'disponible'`                 | Catálogo público: solo indexa las propiedades activas, reduciendo el tamaño del índice |
| `idx_reservas_activas`        | `reservas`    | `WHERE estado IN ('pendiente', 'confirmada')` | Verificación de disponibilidad: excluye reservas canceladas/completadas del índice     |

> Los índices parciales son más livianos que los totales porque solo indexan las filas relevantes. Para tablas con alto volumen de cancelaciones o propiedades pausadas, el beneficio es significativo.

#### Cubriente — evita acceso a tabla (Index-Only Scan)

| Índice                      | Tabla         | Columnas indexadas | Columnas incluidas (INCLUDE) |
| --------------------------- | ------------- | ------------------ | ---------------------------- |
| `idx_propiedades_cubriente` | `propiedades` | `id`, `precio`     | `nombre`, `rating`, `tipo`   |

> El índice cubriente permite que el listado de propiedades (`SELECT id, nombre, precio, rating, tipo`) se resuelva sin tocar la tabla principal. PostgreSQL lo usa en un Index-Only Scan cuando las columnas del `SELECT` están todas en el índice.

#### Funcional — normalización en el índice

| Índice                     | Tabla      | Expresión      | Uso                                                                                 |
| -------------------------- | ---------- | -------------- | ----------------------------------------------------------------------------------- |
| `idx_usuarios_email_lower` | `usuarios` | `lower(email)` | Login case-insensitive: `WHERE lower(email) = lower($1)` usa el índice directamente |

#### GIN — estructuras JSONB, arrays y búsqueda de texto

| Índice                           | Tabla         | Columna                                           | Uso                                                              |
| -------------------------------- | ------------- | ------------------------------------------------- | ---------------------------------------------------------------- |
| `idx_propiedades_amenidades_gin` | `propiedades` | `amenidades` (JSONB)                              | Búsqueda dentro del JSON: `amenidades @> '{"wifi": true}'`       |
| `idx_propiedades_tags_gin`       | `propiedades` | `tags` (array)                                    | Búsqueda dentro del array: `tags @> ARRAY['pet-friendly']`       |
| `idx_propiedades_fulltext_gin`   | `propiedades` | `to_tsvector('spanish', nombre \|\| descripcion)` | Búsqueda de texto completo en español sobre nombre y descripción |

> El índice de texto completo usa `pg_trgm` y `to_tsvector` con diccionario `spanish`. Permite consultas como `WHERE to_tsvector('spanish', nombre \|\| descripcion) @@ to_tsquery('spanish', 'cabaña & Mendoza')` sin sequential scan.

#### GiST — búsqueda espacial (PostGIS)

| Índice                           | Tabla         | Columna                           | Uso                                                                 |
| -------------------------------- | ------------- | --------------------------------- | ------------------------------------------------------------------- |
| `idx_propiedades_ubicacion_gist` | `propiedades` | `ubicacion` (GEOMETRY Point 4326) | Búsqueda por proximidad geográfica con `ST_DWithin` y `ST_Distance` |

```sql
-- Ejemplo: propiedades dentro de 5 km de San Rafael, Mendoza
SELECT nombre, ST_Distance(ubicacion, ST_MakePoint(-68.3391, -34.6177)::geography) AS metros
FROM propiedades
WHERE ST_DWithin(ubicacion::geography, ST_MakePoint(-68.3391, -34.6177)::geography, 5000)
ORDER BY metros;
```

#### Constraints como índices implícitos

PostgreSQL crea automáticamente un índice B-Tree por cada constraint `UNIQUE` y `PRIMARY KEY` declarado en el schema:

| Constraint               | Tabla                                | Tipo                                            |
| ------------------------ | ------------------------------------ | ----------------------------------------------- |
| `PRIMARY KEY`            | todas las tablas                     | B-Tree en `id`                                  |
| `UNIQUE (email)`         | `usuarios`                           | B-Tree en `email`                               |
| `UNIQUE (reserva_id)`    | `reseñas`                            | B-Tree en `reserva_id` (una reseña por reserva) |
| `FOREIGN KEY` en cascada | `propiedades`, `reservas`, `reseñas` | Integridad referencial                          |

### 🛡️ Seguridad y Auditoría

- **Separación de Privilegios en PostgreSQL**: Implementación del rol `API_DB_USER` restringido exclusivamente a operaciones DML (`SELECT`, `INSERT`, `UPDATE`, `DELETE`), revocando accesos DDL para mitigar el impacto de posibles intrusiones.
- **Auditoría Asíncrona en MongoDB**: Registro detallado de operaciones críticas (creación de usuarios, reservas, etc.) incluyendo contexto, utilizando `BackgroundTasks` para asegurar la trazabilidad sin penalizar el rendimiento transaccional principal.
- **Autenticación en NoSQL**: Blindaje de la base de datos MongoDB exigiendo credenciales de acceso para el registro de auditoría.
- **Gestión Segura de Secretos**: Eliminación de credenciales hardcodeadas (como en los scripts de inicialización SQL) mediante la inyección dinámica desde variables de entorno (`.env`).
- **Hardening de Aplicación**: Encriptación de contraseñas utilizando algoritmo fuerte nativo (`bcrypt`), validaciones estrictas de entrada (Pydantic) y políticas restrictivas de CORS.

### 💳 Transacciones

- **Control de concurrencia (prevención de doble booking)**: implementado en `ReservaRepository.crear_reserva_segura()` mediante **bloqueo pesimista de filas** con `SELECT ... FOR UPDATE` (`with_for_update()` en SQLAlchemy) sobre la propiedad antes de verificar disponibilidad. Esto garantiza que ninguna otra transacción pueda leer/modificar esa propiedad hasta que la primera haga commit o rollback.
- **Nivel de aislamiento**: se utiliza el nivel por defecto de PostgreSQL (`READ COMMITTED`). El `FOR UPDATE` es suficiente para evitar el doble booking sin necesidad de `SERIALIZABLE`, ya que el conflicto se previene bloqueando la fila específica en disputa en lugar de aislar toda la transacción.
- **Verificación de solapamiento de fechas**: dentro de la sección bloqueada, se consultan las reservas activas (`pendiente`/`confirmada`) de la propiedad y se valida que el rango `[fecha_checkin, fecha_checkout)` de la nueva reserva no se superponga con ninguna existente.
- **Atomicidad**: la verificación de disponibilidad y la creación de la reserva ocurren dentro de la misma transacción/sesión de SQLAlchemy. El repositorio no hace commit explícito (queda a cargo del router), de modo que si algo fallara antes del commit, ningún cambio queda persistido.
- **Demostración**: `backend/scripts/test_concurrencia.py` dispara dos requests `POST /reservas/` simultáneos (con threads) para la misma propiedad y fechas, y verifica automáticamente que solo una sea aceptada (201) y la otra rechazada (400) — confirmando que el locking previene la condición de carrera en la práctica.

---

## 📁 Estructura del Proyecto

```
Repositorio-Grupo-10/
├── actividades.md
├── docker-compose.yml
├── LICENSE
├── README.md
├── backend/
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── guia-uv.md
│   ├── pyproject.toml
│   ├── README.md
│   ├── alembic/
│   │   ├── env.py
│   │   ├── README
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 95648156dc74_initial_schema.py
│   ├── app/
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── enums.py
│   │   │   ├── propiedad.py
│   │   │   ├── reseña.py
│   │   │   ├── reserva.py
│   │   │   └── usuario.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── log_actividad.py
│   │   │   ├── propiedad.py
│   │   │   ├── resena.py
│   │   │   ├── reserva.py
│   │   │   └── usuario.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── logs.py
│   │   │   ├── propiedades.py
│   │   │   ├── reseñas.py
│   │   │   ├── reservas.py
│   │   │   └── usuarios.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── log_actividad.py
│   │   │   ├── propiedad.py
│   │   │   ├── resena.py
│   │   │   ├── reserva.py
│   │   │   └── usuario.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── log_utils.py
│   ├── backups/
│   │   ├── backup_auto.py
│   │   ├── backup_db.py
│   │   └── restore_db.py
│   ├── scripts/
│   │   ├── consultas_demostracion.sql
│   │   ├── migrate_orm.py
│   │   ├── seed_db.py
│   │   ├── test_concurrencia.py
│   │   └── test_endpoints.py
├── db/
│   └── schema/
│       └── 04_seguridad_roles.sh
└── frontend/
    ├── app.js
    ├── index.html
    ├── login.html
    ├── login.js
    ├── README.md
    ├── register.html
    ├── register.js
    └── styles.css
```

---

## ⚙️ Instalación y Ejecución

### Requisitos previos

- Docker y Docker Compose instalados
- Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/UTN-BDA-2026/Grupo-10-Stayhub.git
cd Grupo-10-Stayhub

# 2. Copiar el archivo de variables de entorno y completarlo
cp .env.example .env

# 3. Levantar los contenedores (PostgreSQL + PostGIS + API)
docker compose up -d

# 4. Aplicar la migración inicial desde Alembic
cd backend
uv run alembic upgrade head

# 5. Acceder a la API
# http://localhost:8000/docs  →  Swagger UI interactivo

# 6. Acceder a pgAdmin
# http://localhost:5050
```

### Variables de entorno

El repositorio incluye un archivo `.env.example` con todas las variables necesarias y sin valores sensibles. **Nunca commitear el archivo `.env`** (ya está en el `.gitignore`).

```bash
cp .env.example .env
# Luego editar .env con los valores reales del entorno local
```

El archivo `.env.example` tiene la siguiente estructura:

```env
# PostgreSQL
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_PORT=

# pgAdmin
PGADMIN_EMAIL=
PGADMIN_PASSWORD=

# Credenciales seguras para la API
API_DB_USER=
API_DB_PASSWORD=

# MongoDB
MONGO_DB=
MONGO_PORT=
MONGO_USER=
MONGO_PASSWORD=
```

---

## 🔬 Consultas de Demostración

Se ha desarrollado el script `backend/scripts/consultas_demostracion.sql` con 10 consultas de nivel avanzado listas para ejecutar durante la defensa. Incluyen:
- Búsqueda Geoespacial con `ST_DWithin` (PostGIS)
- Búsqueda en JSONB con índices GIN
- Funciones de Ventana (`RANK() OVER`)
- Expresiones Comunes de Tabla (`WITH` CTEs)
- Bloqueos transaccionales para concurrencia (`FOR UPDATE`)

Cada tema cuenta con consultas documentadas que incluyen `EXPLAIN ANALYZE` antes y después de aplicar el índice correspondiente, mostrando la mejora de rendimiento.

```sql
-- Ejemplo: búsqueda combinada con índice multicolumna
EXPLAIN ANALYZE
SELECT p.nombre, p.precio, p.rating
FROM propiedades p
WHERE p.ciudad = 'Mendoza'
  AND p.precio BETWEEN 5000 AND 15000
  AND p.estado = 'disponible';

-- Ejemplo: búsqueda espacial con PostGIS
SELECT p.nombre, ST_Distance(p.ubicacion, ST_MakePoint(-68.8272, -32.8895)::geography) AS distancia_metros
FROM propiedades p
WHERE ST_DWithin(p.ubicacion::geography, ST_MakePoint(-68.8272, -32.8895)::geography, 5000)
ORDER BY distancia_metros;
```
