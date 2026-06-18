#!/bin/bash
set -e

# Este script se ejecuta automáticamente al iniciar la base de datos por primera vez.
# Utilizamos un script bash (.sh) en lugar de un .sql crudo para poder inyectar 
# las contraseñas desde las variables de entorno de forma segura, evitando 
# hardcodearlas en el código fuente.

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- 1. Creamos un usuario exclusivo para la API (no es superusuario)
    CREATE ROLE ${API_DB_USER} WITH LOGIN PASSWORD '${API_DB_PASSWORD}';

    -- 2. Revocamos el acceso por defecto para evitar que usuarios no autorizados vean la estructura
    REVOKE ALL ON SCHEMA public FROM PUBLIC;

    -- 3. Le damos permiso de uso del esquema al nuevo usuario
    GRANT USAGE ON SCHEMA public TO ${API_DB_USER};

    -- 4. Le otorgamos permisos estrictamente operativos sobre las tablas (Menor Privilegio)
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ${API_DB_USER};

    -- 5. Permitimos que use las secuencias (necesario para que funcionen los IDs autoincrementales)
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ${API_DB_USER};

    -- 6. Garantizamos que cualquier tabla FUTURA que creen tus compañeros también aplique esta regla
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ${API_DB_USER};
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO ${API_DB_USER};
EOSQL
