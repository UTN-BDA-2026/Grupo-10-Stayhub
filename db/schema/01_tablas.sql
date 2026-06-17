CREATE EXTENSION IF NOT EXISTS plpgsql;

-- ============================================================================
-- 1. TABLA: USUARIOS
-- ============================================================================
-- Entidad raíz: propietarios de alojamientos y huéspedes
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR NOT NULL,
    rol VARCHAR(20) NOT NULL,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT ck_rol CHECK (
        rol IN (
            'propietario',
            'huesped',
            'admin'
        )
    )
);

-- Índices en usuarios
CREATE INDEX IF NOT EXISTS ix_usuario_email ON usuarios USING hash (email);

CREATE INDEX IF NOT EXISTS ix_usuario_rol ON usuarios (rol);

-- ============================================================================
-- 2. TABLA: PROPIEDADES
-- ============================================================================
-- Alojamientos publicados por propietarios
CREATE TABLE IF NOT EXISTS propiedades (
    id SERIAL PRIMARY KEY,
    propietario_id INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    tipo VARCHAR(50) NOT NULL,
    ciudad VARCHAR(100) NOT NULL,
    direccion TEXT NOT NULL,
    ubicacion VARCHAR,
    precio NUMERIC(10, 2) NOT NULL,
    amenidades JSONB,
    tags TEXT [],
    estado VARCHAR(20) NOT NULL,
    rating NUMERIC(3, 2),
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT ck_propiedad_estado CHECK (
        estado IN (
            'disponible',
            'reservada',
            'mantenimiento',
            'inactiva'
        )
    ),
    CONSTRAINT ck_propiedad_precio CHECK (precio > 0),
    CONSTRAINT ck_propiedad_rating CHECK (
        rating >= 0
        AND rating <= 5
    )
);

-- Índices en propiedades
-- - Búsquedas simples por tipo y ciudad
CREATE INDEX IF NOT EXISTS ix_propiedad_tipo ON propiedades (tipo);

CREATE INDEX IF NOT EXISTS ix_propiedad_ciudad ON propiedades (ciudad);

-- - Búsqueda compuesta: ciudad + estado (muy común en filtrados de UI)
CREATE INDEX IF NOT EXISTS ix_ciudad_estado ON propiedades (ciudad, estado);

-- - Búsqueda en JSON amenidades (GIN: Generalized Inverted Index para JSONB)
CREATE INDEX IF NOT EXISTS ix_amenidades_gin ON propiedades USING gin (amenidades);

-- - Búsqueda en tags (array)
CREATE INDEX IF NOT EXISTS ix_propiedad_tags ON propiedades USING gin (tags);

-- - Búsqueda por rango de precios (B+Tree)
CREATE INDEX IF NOT EXISTS ix_propiedad_precio ON propiedades (precio);

-- ============================================================================
-- 3. TABLA: RESERVAS
-- ============================================================================
-- Reservas de huéspedes en propiedades
CREATE TABLE IF NOT EXISTS reservas (
    id SERIAL PRIMARY KEY,
    propiedad_id INTEGER NOT NULL REFERENCES propiedades (id) ON DELETE CASCADE,
    huesped_id INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    fecha_checkin DATE NOT NULL,
    fecha_checkout DATE NOT NULL,
    precio_total NUMERIC(10, 2) NOT NULL,
    estado VARCHAR(20) NOT NULL,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT ck_reserva_estado CHECK (
        estado IN (
            'pendiente',
            'confirmada',
            'cancelada',
            'completada'
        )
    ),
    CONSTRAINT ck_reserva_precio CHECK (precio_total > 0),
    CONSTRAINT ck_reserva_fechas CHECK (
        fecha_checkout > fecha_checkin
    )
);

-- Índices en reservas
-- - Búsqueda por propiedad (para validar disponibilidad)
CREATE INDEX IF NOT EXISTS ix_reserva_propiedad ON reservas (propiedad_id);

-- - Búsqueda por huésped
CREATE INDEX IF NOT EXISTS ix_reserva_huesped ON reservas (huesped_id);

-- - Búsqueda por rango de fechas (check-in y check-out)
CREATE INDEX IF NOT EXISTS ix_reserva_fechas ON reservas (fecha_checkin, fecha_checkout);

-- - Búsqueda compuesta: propiedad + estado (para disponibilidad)
CREATE INDEX IF NOT EXISTS ix_reserva_propiedad_estado ON reservas (propiedad_id, estado);

-- ============================================================================
-- 4. TABLA: RESEÑAS
-- ============================================================================
-- Comentarios y puntuaciones de huéspedes sobre propiedades
CREATE TABLE IF NOT EXISTS reseñas (
    id SERIAL PRIMARY KEY,
    reserva_id INTEGER NOT NULL UNIQUE REFERENCES reservas (id) ON DELETE CASCADE,
    propiedad_id INTEGER NOT NULL REFERENCES propiedades (id) ON DELETE CASCADE,
    huesped_id INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    puntuacion SMALLINT NOT NULL,
    comentario TEXT,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT ck_resena_puntuacion CHECK (
        puntuacion >= 1
        AND puntuacion <= 5
    )
);

-- Índices en reseñas
-- - Búsqueda de reseñas por propiedad (para mostrar ratings)
CREATE INDEX IF NOT EXISTS ix_resena_propiedad ON reseñas (propiedad_id);

-- - Búsqueda de reseñas por huésped
CREATE INDEX IF NOT EXISTS ix_resena_huesped ON reseñas (huesped_id);

-- ============================================================================
-- RESUMEN DE ÍNDICES IMPLEMENTADOS
-- ============================================================================
-- 1. B+Tree (por defecto): precio, fechas, rol, etc. — búsquedas por rango
-- 2. Hash (email): usuario.email, para igualdad exacta en login O(1)
-- 3. Compuesto: (ciudad, estado), (propiedad_id, estado) — filtros combinados
-- 4. GIN (JSONB): amenidades — búsqueda dentro de JSON
-- 5. GIN (array): tags — búsqueda dentro de arrays
-- 6. Constraint CHECK: validaciones a nivel de BD
-- 7. Constraint UNIQUE: email
-- 8. Constraint FK: integridad referencial en cascada
-- ============================================================================