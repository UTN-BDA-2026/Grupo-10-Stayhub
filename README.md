# 🏠 StayHub — Plataforma de Gestión de Alojamientos

## 📚 Cátedra

**Base de Datos Avanzada** — Universidad Tecnológica Nacional FRSR

## 👥 Integrantes grupo 10

| Nombre                       |
| ---------------------------- |
| Moya, Carlos Esteban         |
| Iriarte Lopez, Ana Valentina |
| Parada, Solange Yanina       |
| Vulcano, Candela Nair        |
| Reali, Tomas                 |

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

- Estrategia de backup completo semanal con `pg_dump` en formato custom
- Backup incremental diario mediante WAL archiving
- Script automatizado de restauración con `pg_restore` y verificación de integridad
- Política de retención: 4 backups semanales + 30 backups diarios

### 🔍 Índices

El proyecto aplica los siguientes índices vistos en la cátedra:

- 1. B+Tree (por defecto): precio, fechas, rol, etc. — búsquedas por rango
- 2. Hash (email): usuario.email, para igualdad exacta en login O(1)
- 3. Compuesto: (ciudad, estado), (propiedad_id, estado) — filtros combinados
- 4. GIN (JSONB): amenidades — búsqueda dentro de JSON
- 5. GIN (array): tags — búsqueda dentro de arrays
- 6. Constraint CHECK: validaciones a nivel de BD
- 7. Constraint UNIQUE: email
- 8. Constraint FK: integridad referencial en cascada

### 💳 Transacciones

- Control de concurrencia en reservas: prevención de **doble booking** mediante niveles de aislamiento `SERIALIZABLE`
- Bloqueos explícitos con `SELECT FOR UPDATE` sobre disponibilidad
- Manejo de rollback automático ante fallos de pago o validación
- Demostración de anomalías (dirty read, phantom read) y cómo los niveles de aislamiento las previenen

---

## 📁 Estructura del Proyecto

```
stayhub/
├── db/
│   ├── schema/
│   │   ├── 01_tablas.sql
│   │   ├── 02_indices.sql
│   │   └── 03_datos_seed.sql
│   ├── transactions/
│   │   ├── reserva_confirmar.sql
│   │   └── pago_procesar.sql
│   └── backups/
│       ├── backup_full.sh
│       └── restore.sh
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   └── models/
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
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
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_PORT=
PGADMIN_EMAIL=
PGADMIN_PASSWORD=
```

---

## 🔬 Consultas de Demostración

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
